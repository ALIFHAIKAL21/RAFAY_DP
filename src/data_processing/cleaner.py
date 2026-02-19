import json
import sys
from pathlib import Path

# SETUP IMPORT PATH 
# membaca 'src.config' meskipun dijalankan dari folder dalam
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config import TRAIN_DATA_UNCLEAN, TRAIN_DATA_CLEAN

def clean_stutter(token):
    """
    Memperbaiki kata gagap/nempel: "DediDedi" -> "Dedi"
    """
    mid = len(token) // 2
    if len(token) > 4 and token[:mid] == token[mid:]:
        return token[:mid]
    return token

def main():
    print(f"Memulai Pembersihan Data...")
    print(f"Input: {TRAIN_DATA_UNCLEAN}")
    
    # Cek file ada atau tidak
    if not TRAIN_DATA_UNCLEAN.exists():
        print(f"ERROR: File input tidak ditemukan di: {TRAIN_DATA_UNCLEAN}")
        return

    with open(TRAIN_DATA_UNCLEAN, 'r') as f:
        dataset = json.load(f)
    
    corrections_count = 0
    
    for entry in dataset:
        tokens = entry['tokens']
        tags = entry['ner_tags']
        
        new_tokens = []
        new_tags = []
        
        for t, tag in zip(tokens, tags):
            original_token = t
            
            # ATURAN 1: FIX NOMOR HP KEPANJANGAN 
            if t.startswith("08") and t.isdigit() and len(t) > 13:
                t = t[:12] # Ambil 12 digit pertama
                if "PHONE" not in tag:
                    tag = "B-PHONE"
                corrections_count += 1
                
            # ATURAN 2: FIX LABEL DATE -> PHONE 
            if t.startswith("08") and t.isdigit() and "DATE" in tag:
                tag = "B-PHONE"
                corrections_count += 1

            # ATURAN 3: FIX STUTTER 
            t = clean_stutter(t)
            if t != original_token:
                corrections_count += 1

            new_tokens.append(t)
            new_tags.append(tag)
            
        entry['tokens'] = new_tokens
        entry['ner_tags'] = new_tags

    # Pastikan folder output ada
    TRAIN_DATA_CLEAN.parent.mkdir(parents=True, exist_ok=True)

    with open(TRAIN_DATA_CLEAN, 'w') as f:
        json.dump(dataset, f, indent=2)
        
    print(f"SELESAI! {corrections_count} perbaikan dilakukan.")
    print(f"Output tersimpan di: {TRAIN_DATA_CLEAN}")

if __name__ == "__main__":
    main()