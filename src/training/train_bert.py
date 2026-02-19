import json
import sys
import numpy as np
from pathlib import Path
from datasets import Dataset
import evaluate
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification, 
    TrainingArguments, 
    Trainer,
    DataCollatorForTokenClassification
)

# --- 1. SETUP IMPORT PATH ---
# Agar bisa import 'src.config' dari dalam folder training
# Posisi: src/training/train_bert.py -> Mundur 3 langkah ke Root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import TRAIN_DATA_CLEAN, BERT_OUTPUT_DIR, BATCH_SIZE, EPOCHS, LEARNING_RATE

# --- 2. KONFIGURASI MODEL ---
MODEL_CHECKPOINT = "indolem/indobert-base-uncased"

def compute_metrics(p, label_list):
    """Menghitung akurasi, presisi, recall, dan F1"""
    seqeval = evaluate.load("seqeval")
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = seqeval.compute(predictions=true_predictions, references=true_labels)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }

def main():
    print("🚀 Memulai Training IndoBERT...")
    print(f"📂 Input Data: {TRAIN_DATA_CLEAN}")
    
    # Validasi File
    if not TRAIN_DATA_CLEAN.exists():
        print(f"❌ ERROR: File data bersih tidak ditemukan di: {TRAIN_DATA_CLEAN}")
        print("👉 Jalankan: python -m src.data_processing.cleaner dulu!")
        return

    # 1. Load Dataset
    with open(TRAIN_DATA_CLEAN, "r") as f:
        data = json.load(f)

    # 2. Siapkan Label List
    label_list = set()
    for item in data:
        label_list.update(item["ner_tags"])
    label_list = sorted(list(label_list))
    if "O" in label_list: # Pastikan O di index 0
        label_list.remove("O")
        label_list.insert(0, "O")

    label2id = {l: i for i, l in enumerate(label_list)}
    id2label = {i: l for i, l in enumerate(label_list)}
    
    print(f"🏷️ Jumlah Label: {len(label_list)}")

    # 3. Split Dataset
    hf_dataset = Dataset.from_list(data)
    dataset_split = hf_dataset.train_test_split(test_size=0.2)
    
    # 4. Tokenizer & Model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
    model = AutoModelForTokenClassification.from_pretrained(
        MODEL_CHECKPOINT,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id
    )
    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    # 5. Preprocessing (Align Labels)
    def tokenize_and_align_labels(examples):
        tokenized_inputs = tokenizer(
            examples["original_text"], 
            truncation=True, 
            is_split_into_words=False,
            padding="max_length", 
            max_length=128
        )
        
        labels = []
        for i, label_raw in enumerate(examples["ner_tags"]):
            # Konversi label string ke ID angka
            label_ids = [label2id[l] for l in label_raw]
            
            # Padding -100 agar tidak dihitung loss-nya
            if len(label_ids) < 128:
                label_ids += [-100] * (128 - len(label_ids))
            else:
                label_ids = label_ids[:128]
            labels.append(label_ids)
            
        # Timpa input_ids dengan token yang sudah kita hasilkan dari pre-processing sebelumnya
        # untuk menjamin konsistensi
        final_input_ids = []
        for tokens in examples["tokens"]:
            ids = tokenizer.convert_tokens_to_ids(tokens)
            if len(ids) < 128:
                ids += [tokenizer.pad_token_id] * (128 - len(ids))
            else:
                ids = ids[:128]
            final_input_ids.append(ids)

        tokenized_inputs["input_ids"] = final_input_ids
        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    tokenized_datasets = dataset_split.map(tokenize_and_align_labels, batched=True)

   # 6. Training Arguments
    args = TrainingArguments(
        output_dir=str(BERT_OUTPUT_DIR),
        eval_strategy="epoch",    # Cek performa setiap selesai 1 epoch
        save_strategy="epoch",          # Simpan checkpoint setiap selesai 1 epoch
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=0.01,
        save_total_limit=2,             # Hanya simpan 2 model terbaik (hemat storage laptop)
        logging_dir='./logs',           # Folder logs untuk Tensorboard
        logging_steps=10,               # Update log setiap 10 steps (biar kelihatan progress bar jalan)
        
        # --- 🔥 SETTINGAN KHUSUS RTX 4050 🔥 ---
        fp16=True,                      # WAJIB! Mengaktifkan Mixed Precision (Training 2x lebih cepat & hemat RAM)
        dataloader_num_workers=2,       # Mempercepat loading data ke GPU (Ubah ke 0 jika error di Windows)
        
        # --- BEST PRACTICE ---
        load_best_model_at_end=True,    # Di akhir training, otomatis load model dengan skor terbaik (bukan yang terakhir)
        metric_for_best_model="f1",     # Patokan model terbaik adalah F1 Score tertinggi
        greater_is_better=True,         # Semakin tinggi F1, semakin bagus
    )

    # 7. Trainer
    trainer = Trainer(
        model,
        args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["test"],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=lambda p: compute_metrics(p, label_list)
    )

    print("🔥 Mulai Training...")
    trainer.train()
    
    print("✅ Training Selesai! Menyimpan model...")
    trainer.save_model(str(BERT_OUTPUT_DIR / "final_model"))
    tokenizer.save_pretrained(str(BERT_OUTPUT_DIR / "final_model"))
    print(f"💾 Model tersimpan di: {BERT_OUTPUT_DIR}/final_model")

if __name__ == "__main__":
    main()