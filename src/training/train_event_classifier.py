import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import (
    EVENT_BATCH_SIZE,
    EVENT_EPOCHS,
    EVENT_LEARNING_RATE,
    EVENT_MAX_SEQ_LEN,
    EVENT_MODEL_CHECKPOINT,
    EVENT_OUTPUT_DIR,
    EVENT_TRAIN_DATA,
)


CANONICAL_ORDER = ["NEW_ORDER", "UPDATE", "NON_ORDER"]


def build_label_maps(labels_found):
    ordered = [l for l in CANONICAL_ORDER if l in labels_found]
    for extra in sorted(labels_found):
        if extra not in ordered:
            ordered.append(extra)
    label2id = {l: i for i, l in enumerate(ordered)}
    id2label = {i: l for l, i in label2id.items()}
    return ordered, label2id, id2label


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    acc = accuracy_score(labels, preds)
    return {
        "accuracy": acc,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
    }


def main():
    print("Memulai training Event Classifier...")
    print(f"Input data : {EVENT_TRAIN_DATA}")
    print(f"Checkpoint : {EVENT_MODEL_CHECKPOINT}")
    print(f"Output dir : {EVENT_OUTPUT_DIR}")

    if not EVENT_TRAIN_DATA.exists():
        print(f"ERROR: file dataset tidak ditemukan: {EVENT_TRAIN_DATA}")
        print("Jalankan dulu: python -m src.data_processing.prepare_event_dataset")
        return

    with open(EVENT_TRAIN_DATA, "r", encoding="utf-8") as f:
        rows = json.load(f)

    rows = [r for r in rows if str(r.get("text", "")).strip() and str(r.get("label", "")).strip()]
    if len(rows) < 20:
        print("ERROR: data terlalu sedikit. Minimal 20 baris.")
        return

    labels_found = sorted({str(r["label"]).strip().upper() for r in rows})
    if len(labels_found) < 2:
        print(f"ERROR: kelas label kurang dari 2: {labels_found}")
        return

    label_list, label2id, id2label = build_label_maps(labels_found)
    print(f"Label list: {label_list}")

    data = [
        {
            "text": str(r["text"]),
            "label_id": label2id[str(r["label"]).strip().upper()],
        }
        for r in rows
        if str(r["label"]).strip().upper() in label2id
    ]

    y = [d["label_id"] for d in data]
    stratify = y if len(set(y)) > 1 else None
    train_rows, test_rows = train_test_split(
        data,
        test_size=0.2,
        random_state=42,
        stratify=stratify,
    )

    train_ds = Dataset.from_list(train_rows)
    test_ds = Dataset.from_list(test_rows)

    tokenizer = AutoTokenizer.from_pretrained(EVENT_MODEL_CHECKPOINT)
    model = AutoModelForSequenceClassification.from_pretrained(
        EVENT_MODEL_CHECKPOINT,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
    )

    def tokenize_fn(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            max_length=EVENT_MAX_SEQ_LEN,
        )

    train_ds = train_ds.map(tokenize_fn, batched=True)
    test_ds = test_ds.map(tokenize_fn, batched=True)

    train_ds = train_ds.rename_column("label_id", "labels")
    test_ds = test_ds.rename_column("label_id", "labels")

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    EVENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(
        output_dir=str(EVENT_OUTPUT_DIR),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=EVENT_LEARNING_RATE,
        per_device_train_batch_size=EVENT_BATCH_SIZE,
        per_device_eval_batch_size=EVENT_BATCH_SIZE,
        num_train_epochs=EVENT_EPOCHS,
        weight_decay=0.01,
        logging_dir=str(ROOT_DIR / "logs"),
        logging_steps=10,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),
        dataloader_num_workers=0,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print("Training dimulai...")
    trainer.train()

    final_dir = EVENT_OUTPUT_DIR / "final_model"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"Training selesai. Model disimpan di: {final_dir}")


if __name__ == "__main__":
    main()
