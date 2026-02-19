import torch
import numpy as np
import sys
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification

# --- SETUP IMPORT PATH ---
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.config import BERT_OUTPUT_DIR

class IndoBERTInference:
    def __init__(self, model_path=None):
        # Jika path tidak ditentukan, pakai model hasil training terakhir
        self.model_path = model_path if model_path else BERT_OUTPUT_DIR / "final_model"
        
        print(f"[LOADING] Memuat model dari: {self.model_path}")

        # Cek device (Pakai RTX 4050 mu kalau bisa)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[DEVICE] Running on: {self.device}")

        # Load Model & Tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_path)
            self.model.to(self.device)
            self.model.eval() # Mode evaluasi (matikan dropout)
            
            # Ambil mapping Label ID ke Nama Label (misal: 0 -> B-DRIVER)
            self.id2label = self.model.config.id2label
            print("[OK] Model siap digunakan!")
        except Exception as e:
            print(f"[ERROR] Gagal memuat model: {e}")
            sys.exit(1)

    def predict(self, text):
        # 1. Tokenisasi Input
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=128
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # 2. Prediksi (Inference)
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # 3. Ambil ID dengan probabilitas tertinggi
        logits = outputs.logits
        predictions = torch.argmax(logits, dim=2)[0].cpu().numpy()
        
        # 4. Ambil token aslinya
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        
        # 5. Gabungkan Subword (Reconstruct Words)
        # IndoBERT memecah kata (misal: "Surabaya" -> "Sur", "##aba", "##ya")
        # Kita harus gabungkan lagi biar enak dibaca manusia.
        
        entities = []
        current_word = ""
        current_label = None
        
        for token, pred_id in zip(tokens, predictions):
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            
            label = self.id2label[pred_id]
            
            # Jika token adalah subword (diawali ##), gabung ke kata sebelumnya
            if token.startswith("##"):
                current_word += token[2:] # Hapus ##
                # Label ikut yang depan
            else:
                # Jika ada kata sebelumnya yang sudah jadi, simpan dulu
                if current_word:
                    entities.append({"token": current_word, "label": current_label})
                
                # Reset untuk kata baru
                current_word = token
                current_label = label
        
        # Simpan kata terakhir
        if current_word:
            entities.append({"token": current_word, "label": current_label})
            
        return self._format_json(entities)

    def _format_json(self, raw_entities):
        """Merapikan output menjadi JSON bersih"""
        result = {}
        
        # Logika penggabungan token B-LABEL dan I-LABEL
        # Misal: [B-DRIVER: Dedi], [I-DRIVER: Putra] -> "DRIVER": "Dedi Putra"
        
        current_key = None
        buffer_text = []
        
        for item in raw_entities:
            label = item['label']
            word = item['token']
            
            if label == "O":
                continue
                
            prefix = label[0] # B atau I
            category = label[2:] # DRIVER, DATE, dll
            
            if prefix == "B":
                # Jika sebelumnya ada buffer, simpan dulu
                if current_key:
                    # Simpan data sebelumnya (gabungkan list kata jadi string)
                    full_text = " ".join(buffer_text)
                    result[current_key] = full_text
                
                # Mulai baru
                current_key = category
                buffer_text = [word]
                
            elif prefix == "I" and current_key == category:
                # Lanjutkan kata sebelumnya
                buffer_text.append(word)
        
        # Jangan lupa simpan yang terakhir
        if current_key and buffer_text:
            result[current_key] = " ".join(buffer_text)
            
        return result

# --- AREA TESTING (MAIN) ---
if __name__ == "__main__":
    # Inisialisasi Pipeline
    pipeline = IndoBERTInference()
    
    print("\n" + "="*50)
    print("🤖 TES MANUAL INDOBERT (Ketik 'exit' untuk keluar)")
    print("="*50)
    
    while True:
        user_input = input("\n📝 Masukkan Chat Order: ")
        if user_input.lower() in ['exit', 'keluar']:
            break
            
        if not user_input.strip():
            continue
            
        # Lakukan Prediksi
        hasil = pipeline.predict(user_input)
        
        # Tampilkan Hasil
        print("\n📊 HASIL EKSTRAKSI:")
        for k, v in hasil.items():
            print(f"   ➤ {k.ljust(15)} : {v}")