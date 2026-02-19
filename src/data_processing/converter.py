import json
import sys
from pathlib import Path
from transformers import AutoTokenizer

# SETUP PATH IMPORT
# membaca 'src.config' meskipun dijalankan dari dalam folder
# Logika: File ini ada di src/data_processing/converter.py 
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config import RAW_LABEL_STUDIO, TRAIN_DATA_UNCLEAN

# KONFIGURASI MODEL 
MODEL_CHECKPOINT = "indolem/indobert-base-uncased"

def align_labels_with_tokens(tokenizer, text, labels_raw):
    tokenized_inputs = tokenizer(text, truncation=True, is_split_into_words=False, return_offsets_mapping=True)
    tokens = tokenizer.convert_ids_to_tokens(tokenized_inputs["input_ids"])
    offset_mapping = tokenized_inputs["offset_mapping"]
    
    # Buat list label kosong 
    aligned_labels = ["O"] * len(tokens)
    
    # Mapping Karakter Label Studio ke Token IndoBERT
    for label_info in labels_raw:
        if 'labels' not in label_info: continue
        
        label_name = label_info['labels'][0]
        start_char = label_info['start']
        end_char = label_info['end']
        
        found_start = False
        for i, (offset_start, offset_end) in enumerate(offset_mapping):
            if offset_start == 0 and offset_end == 0: continue 
            
            if offset_start >= start_char and offset_end <= end_char:
                if not found_start:
                    aligned_labels[i] = f"B-{label_name}"
                    found_start = True
                else:
                    aligned_labels[i] = f"I-{label_name}"

    return tokens, aligned_labels

#PROSES UTAMA
def main():
    print("⏳ Memulai konversi data...")
    print(f"📂 Input: {RAW_LABEL_STUDIO}")
    
    # 1. Validasi Input
    if not RAW_LABEL_STUDIO.exists():
        print(f"❌ ERROR: File input tidak ditemukan di: {RAW_LABEL_STUDIO}")
        print("Pastikan kamu sudah menaruh file 'export_label_studio.json' di folder data/chat/raw/")
        return

    # 2. Load Data JSON
    with open(RAW_LABEL_STUDIO, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # 3. Siapkan Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
    
    processed_data = []
    
    # 4. Loop setiap data
    print(f"🔄 Memproses {len(raw_data)} data...")
    for item in raw_data:
        # Handle struktur data yang mungkin berbeda
        if 'data' in item and 'text' in item['data']:
            text = item['data']['text']
        else:
            continue 

        # Ambil label 
        labels_raw = []
        if 'annotations' in item and len(item['annotations']) > 0:
            labels_raw = [
                x['value'] for x in item['annotations'][0]['result'] 
                if x['type'] == 'labels'
            ]
        elif 'predictions' in item and len(item['predictions']) > 0:
             labels_raw = [
                x['value'] for x in item['predictions'][0]['result'] 
                if x['type'] == 'labels'
            ]

        # Lakukan Alignment
        tokens, ner_tags = align_labels_with_tokens(tokenizer, text, labels_raw)
        
        processed_data.append({
            "id": item['id'],
            "tokens": tokens,
            "ner_tags": ner_tags,
            "original_text": text
        })

    # 5. Simpan Hasil 
    TRAIN_DATA_UNCLEAN.parent.mkdir(parents=True, exist_ok=True)

    with open(TRAIN_DATA_UNCLEAN, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2)
        
    print(f"✅ SELESAI! {len(processed_data)} data berhasil dikonversi.")
    print(f"💾 Output tersimpan di: {TRAIN_DATA_UNCLEAN}")
    
    # Preview Singkat
    if len(processed_data) > 0:
        print("\n🔍 Preview Data Pertama:")
        print(processed_data[0]['tokens'][:10], "...")

if __name__ == "__main__":
    main()