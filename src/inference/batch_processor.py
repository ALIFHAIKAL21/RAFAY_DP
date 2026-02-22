import re
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Setup Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.inference.pipeline import IndoBERTInference

class ChatBatchProcessor:
    def __init__(self):
        print("[LOADING] Memuat Model IndoBERT untuk Batch Processing...")
        self.pipeline = IndoBERTInference()
        
        # Kata kunci wajib ada (kalau nggak ada ini, dianggap chat sampah/bercanda)
        self.keywords = ["unit", "loading", "tujuan", "kirim", "muat", "driver", "nopol", "request"]

    def is_junk(self, text):
        """Cek apakah chat ini sampah atau orderan beneran"""
        text_lower = text.lower()
        # Kalau tidak mengandung satupun keyword logistik 
        if not any(k in text_lower for k in self.keywords):
            return True
        # Kalau terlalu pendek (kurang dari 10 huruf) 
        if len(text) < 10:
            return True
        return False

    def smart_split(self, raw_text):
        """
        Memecah chat panjang menjadi potongan order kecil.
        FIX: Menambahkan \s* agar tahan terhadap spasi/indentasi.
        """
        # 1. Normalisasi enter biar gampang dipisah
        clean_text = raw_text.replace("\r", "")
        
        # 2. Regex Splitter TERBARU (ANTI GUMPAL)
        pattern = r"(\[.*?\]|(?:\n|^)\s*(?=Waktu loading)|(?:\n|^)\s*(?=REQUEST))"
        
        chunks = re.split(pattern, clean_text)
        
        # Gabungkan kembali delimiter dengan isinya
        final_chunks = []
        current_chunk = ""
        
        for chunk in chunks:
            if not chunk: continue
            
            # Jika chunk adalah delimiter, jadikan awal baru
            if re.match(pattern, chunk, re.DOTALL):
                if current_chunk:
                    final_chunks.append(current_chunk.strip())
                current_chunk = chunk
            else:
                current_chunk += chunk
                
        if current_chunk:
            final_chunks.append(current_chunk.strip())
            
        return final_chunks

    def process_file(self, file_path, output_excel="output_orderan.xlsx"):
        """Baca file txt, proses, simpan ke Excel"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = f.read()
        except FileNotFoundError:
            print(f"[ERROR] File tidak ditemukan: {file_path}")
            return None

        print(f"Membaca data mentah... ({len(raw_data)} karakter)")

        # 1. SPLIT (Pecah jadi potongan kecil)
        chunks = self.smart_split(raw_data)
        print(f"Dipecah menjadi {len(chunks)} potongan chat.")

        valid_orders = []
        current_timestamp = None  # State-based timestamp tracking

        # 2. FILTER & PREDICT
        print("Memulai Ekstraksi AI...")
        for i, text in enumerate(chunks):
            # Bersihkan spasi ganda & baris kosong
            text = text.strip()
            if not text: continue

            # Extract timestamp jika ada pattern [HH.MM, DD/MM/YYYY]
            timestamp_match = re.search(r'\[(\d{2}[.,:]\d{2}\s*,\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\]', text)
            if timestamp_match:
                current_timestamp = f"[{timestamp_match.group(1)}]"

            # Cek Sampah
            if self.is_junk(text):
                print(f"Skip Sampah: {text[:30]}...")
                continue

            # Jika chunk tidak punya timestamp tapi ada REQUEST, attach current_timestamp
            if "request" in text.lower() and not timestamp_match and current_timestamp:
                text = f"{current_timestamp} {text}"

            # Pre-processing No HP (Fix bug +62 jadi 0)
            text_clean = text.replace("+62", "0").replace("-", "")

            # Ekstraksi IndoBERT
            result = self.pipeline.predict(text_clean)

            if result:
                # Tambahkan teks asli buat validasi manual admin
                result['Original_Text'] = text
                valid_orders.append(result)
                print(f"[OK] Order #{len(valid_orders)} Terdeteksi!")
            
        # 3. EXPORT KE EXCEL
        if valid_orders:
            df = pd.DataFrame(valid_orders)
            
            # Rapikan urutan kolom (biar enak dibaca admin)
            cols = ['DATE', 'UNIT_QTY', 'UNIT_TYPE', 'ORIGIN', 'DESTINATION', 'DRIVER', 'PLATE', 'TIME', 'Original_Text']
            # Ambil kolom yg ada aja + sisanya
            final_cols = [c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]
            df = df[final_cols]
            
            df.to_excel(output_excel, index=False)
            print(f"SUKSES! {len(valid_orders)} Orderan disimpan di: {output_excel}")
            return df
        else:
            print("Tidak ada orderan valid ditemukan.")
            return None

#TESTING MANUAL (Opsional) 
if __name__ == "__main__":
    # buat test kalau dijalankan langsung
    sample_text = """
    [20.06, 4/2/2026] Akbar Rafay: REQUEST ORDER ONCALL 04 FEBRUARI 2026:
    3 unit Cddl 24 Cbm
    Lokasi : Megahub
    Waktu loading : segera
    Rute/tujuan : CGK - JATENG
    
    [20.06, 4/2/2026] Akbar Rafay: REQUEST ORDER ULANG ONCALL
    5 UNIT TWB 50 CBM
    Lokasi : ARGOPANTES 
    
    Waktu loading : 18:00
    Rute/tujuan : CGK - SUB
    driver  : m syaichoni
    Nopol  : N 8872 Rk
    
    Waktu loading : 03:00 05/02/2026
    Rute/tujuan : CGK -SUB
    driver  : Lailan
    """
    
    with open("chat_dump.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)
        
    processor = ChatBatchProcessor()
    processor.process_file("chat_dump.txt")