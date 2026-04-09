import json
import inspect
import sys
from pathlib import Path

import numpy as np
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import (
    REVISION_MATCH_BATCH_SIZE,
    REVISION_MATCH_EPOCHS,
    REVISION_MATCH_LEARNING_RATE,
    REVISION_MATCH_MAX_SEQ_LEN,
    REVISION_MATCH_MODEL_CHECKPOINT,
    REVISION_MATCH_OUTPUT_DIR,
    REVISION_MATCH_TRAIN_DATA,
)


CANONICAL_LABELS = ["NO_MATCH", "MATCH"]


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="binary", pos_label=1, zero_division=0
    )
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    acc = accuracy_score(labels, preds)
    return {
        "accuracy": acc,
        "precision_match": precision,
        "recall_match": recall,
        "f1_match": f1,
        "precision_macro": macro_p,
        "recall_macro": macro_r,
        "f1_macro": macro_f1,
    }


def _load_tokenizer_with_fallback(checkpoint: str):
    try:
        return AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    except Exception:
        return AutoTokenizer.from_pretrained(checkpoint)


def _load_model_with_fallback(checkpoint: str, num_labels: int, id2label: dict, label2id: dict):
    model_kwargs = {
        "num_labels": num_labels,
        "id2label": id2label,
        "label2id": label2id,
    }

    # 1) Try local cache only first (no network hit).
    try:
        return AutoModelForSequenceClassification.from_pretrained(
            checkpoint,
            local_files_only=True,
            **model_kwargs,
        )
    except Exception:
        pass

    # 2) Online fallback without forcing safetensors conversion API.
    return AutoModelForSequenceClassification.from_pretrained(
        checkpoint,
        use_safetensors=False,
        **model_kwargs,
    )


def main():
    print("Memulai training Revision Target Matcher...")
    print(f"Input data : {REVISION_MATCH_TRAIN_DATA}")
    print(f"Checkpoint : {REVISION_MATCH_MODEL_CHECKPOINT}")
    print(f"Output dir : {REVISION_MATCH_OUTPUT_DIR}")

    if not REVISION_MATCH_TRAIN_DATA.exists():
        print(f"ERROR: dataset tidak ditemukan: {REVISION_MATCH_TRAIN_DATA}")
        print("Jalankan dulu: python -m src.data_processing.prepare_revision_matcher_dataset")
        return

    with open(REVISION_MATCH_TRAIN_DATA, "r", encoding="utf-8") as f:
        rows = json.load(f)

    rows = [
        r
        for r in rows
        if str(r.get("text_a", "")).strip()
        and str(r.get("text_b", "")).strip()
        and str(r.get("label", "")).strip().upper() in CANONICAL_LABELS
    ]
    if len(rows) < 50:
        print("ERROR: data terlalu sedikit. Minimal 50 pasangan.")
        return

    label2id = {label: idx for idx, label in enumerate(CANONICAL_LABELS)}
    id2label = {idx: label for label, idx in label2id.items()}

    data = [
        {
            "text_a": str(r["text_a"]),
            "text_b": str(r["text_b"]),
            "label_id": label2id[str(r["label"]).strip().upper()],
        }
        for r in rows
    ]

    y = [d["label_id"] for d in data]
    train_rows, test_rows = train_test_split(
        data,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    train_ds = Dataset.from_list(train_rows)
    test_ds = Dataset.from_list(test_rows)

    tokenizer = _load_tokenizer_with_fallback(REVISION_MATCH_MODEL_CHECKPOINT)
    try:
        model = _load_model_with_fallback(
            checkpoint=REVISION_MATCH_MODEL_CHECKPOINT,
            num_labels=len(CANONICAL_LABELS),
            id2label=id2label,
            label2id=label2id,
        )
    except Exception as e:
        raise RuntimeError(
            "Gagal memuat checkpoint revision matcher. "
            "Coba set HF_TOKEN (agar tidak kena rate limit), "
            "atau gunakan checkpoint lokal yang sudah terunduh.\n"
            f"Detail error: {e}"
        ) from e

    def tokenize_fn(batch):
        return tokenizer(
            batch["text_a"],
            batch["text_b"],
            truncation=True,
            max_length=REVISION_MATCH_MAX_SEQ_LEN,
        )

    train_ds = train_ds.map(tokenize_fn, batched=True)
    test_ds = test_ds.map(tokenize_fn, batched=True)

    train_ds = train_ds.rename_column("label_id", "labels")
    test_ds = test_ds.rename_column("label_id", "labels")

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    REVISION_MATCH_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    args_kwargs = {
        "output_dir": str(REVISION_MATCH_OUTPUT_DIR),
        "save_strategy": "epoch",
        "learning_rate": REVISION_MATCH_LEARNING_RATE,
        "per_device_train_batch_size": REVISION_MATCH_BATCH_SIZE,
        "per_device_eval_batch_size": REVISION_MATCH_BATCH_SIZE,
        "num_train_epochs": REVISION_MATCH_EPOCHS,
        "weight_decay": 0.01,
        "logging_dir": str(ROOT_DIR / "logs"),
        "logging_steps": 20,
        "save_total_limit": 2,
        "load_best_model_at_end": True,
        "metric_for_best_model": "f1_match",
        "greater_is_better": True,
        "fp16": torch.cuda.is_available(),
        "dataloader_num_workers": 0,
        "report_to": [],
    }

    ta_signature = inspect.signature(TrainingArguments.__init__).parameters
    if "evaluation_strategy" in ta_signature:
        args_kwargs["evaluation_strategy"] = "epoch"
    else:
        args_kwargs["eval_strategy"] = "epoch"

    args = TrainingArguments(**args_kwargs)

    trainer_kwargs = {
        "model": model,
        "args": args,
        "train_dataset": train_ds,
        "eval_dataset": test_ds,
        "data_collator": data_collator,
        "compute_metrics": compute_metrics,
    }
    trainer_signature = inspect.signature(Trainer.__init__).parameters
    if "tokenizer" in trainer_signature:
        trainer_kwargs["tokenizer"] = tokenizer
    elif "processing_class" in trainer_signature:
        trainer_kwargs["processing_class"] = tokenizer

    trainer = Trainer(**trainer_kwargs)

    print("Training dimulai...")
    trainer.train()

    final_dir = REVISION_MATCH_OUTPUT_DIR / "final_model"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"Training selesai. Model disimpan di: {final_dir}")


if __name__ == "__main__":
    main()
