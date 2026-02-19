import json
import random
import sys
from pathlib import Path

# Setup Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import TRAIN_DATA_CLEAN

OUTPUT_AUGMENTED = TRAIN_DATA_CLEAN.parent / "data_augmented.json"

# Templat Variasi Kata Pengantar
TEMPLATES = {
    "ORIGIN": ["muat di", "dari", "posisi", "ambil di", "loading di"],
    "DESTINATION": ["kirim ke", "tujuan", "arah", "drop di", "bongkar di"],
    "DRIVER": ["driver", "sopir", "sama pak", "drivernya", "supir"],
    "TIME": ["jam", "pukul", "loading jam", "muat jam"],
    "DATE": ["tgl", "tanggal", "hari", "untuk tanggal"]
}

def augment_text(entry):
    tokens = entry['tokens']
    tags = entry['ner_tags']
    
    new_tokens = []
    new_tags = []
    
    skip_next = False
    
    for i, (token, tag) in enumerate(zip(tokens, tags)):
        if skip_next:
            skip_next = False
            continue
            
        # Cek apakah ini tanda titik dua ":" yang menjadi pemisah label
        if token == ":" and i < len(tags)-1 and tags[i+1].startswith("B-"):
            label_type = tags[i+1].split("-")[1] 
            
            # 50% Kemungkinan kita ganti ":" dengan kata sambung natural
            if label_type in TEMPLATES and random.random() > 0.5:
                # Pilih kata sambung acak (misal: "muat di")
                replacement = random.choice(TEMPLATES[label_type])
                
                # Memasukkan kata sambung sebagai token O
                for word in replacement.split():
                    new_tokens.append(word)
                    new_tags.append("O")
                
                # Jangan masukkan ":" ke data baru 
                continue
        
        # Masukkan token asli
        new_tokens.append(token)
        new_tags.append(tag)
        
    return {
        "id": entry['id'] + 9000, #Generate id asli biar ga tabrakan
        "tokens": new_tokens,
        "ner_tags": new_tags,
        "original_text": " ".join(new_tokens) # Rekonstruksi teks 
    }

def main():
    print(f"Memulai Data Augmentation...")
    print(f"Input: {TRAIN_DATA_CLEAN}")
    
    with open(TRAIN_DATA_CLEAN, 'r') as f:
        data = json.load(f)
    
    augmented_data = []
    
    # Masukkan data asli 
    augmented_data.extend(data)
    
    # Generate data variasi
    print("⚡ Generating variasi bahasa natural...")
    for item in data:
        #  buat 2 variasi untuk setiap data asli
        for _ in range(2): 
            aug_item = augment_text(item)
            augmented_data.append(aug_item)
            
    # Shuffle biar training merata
    random.shuffle(augmented_data)
    
    with open(OUTPUT_AUGMENTED, 'w') as f:
        json.dump(augmented_data, f, indent=2)
        
    print(f"✅ SELESAI! Dataset membengkak dari {len(data)} menjadi {len(augmented_data)} data.")
    print(f"💾 Disimpan di: {OUTPUT_AUGMENTED}")
    print("\n👉 LANGKAH SELANJUTNYA:")
    print("1. Buka src/config.py -> Ubah TRAIN_DATA_CLEAN ke file baru ini.")
    print("2. Jalankan training ulang: python -m src.training.train_bert")

if __name__ == "__main__":
    main()