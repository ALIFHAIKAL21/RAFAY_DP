import sys
import os
import re
from pathlib import Path

# Setup Path biar bisa import modul src
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.inference.batch_processor import ChatBatchProcessor

# DATA REAL CASE RAFAY (PERSIS SEPERTI CHAT KAMU)
raw_chat_rafay = """
[20.06, 4/2/2026] Akbar Rafay: REQUEST ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : segera
Rute/tujuan : CGK - JATENG
driver  : KARYADI
Nopol  : AD 8517 BA
No hp  :085865762797
[20.06, 4/2/2026] Akbar Rafay: REQUEST ORDER ULANG ONCALL

5 UNIT TWB 50 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  :
Nopol  :
No hp  :

Waktu loading : 18:00
Rute/tujuan : CGK - SUB
driver  : m syaichoni
Nopol  : N 8872 Rk
No hp  : +62 812-3189-5971

Waktu loading : 21:00
Rute/tujuan : CGK - SUB
driver  :
Nopol  :
No hp  :

Waktu loading : 00:00
Rute/tujuan : CGK - SUB
driver  :
Nopol  :
No hp  :

Waktu loading : 03:00 05/02/2026
Rute/tujuan : CGK -SUB
driver  : Lailan
Nopol  : S 9272 UP
No hp  : +62 878-8686-1780
[20.06, 4/2/2026] Akbar Rafay: REQUEST TAMBAHAN ORDER ONCALL 04 FEBRUARI 2026:

RAFAY
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
Rute/tujuan : CGK - SUB
driver  : AGUS
Nopol  : D 9667 AF
No hp  :08817021866
"""

def run_proof_test():
    print("\n🔥 MEMULAI 'THE FINAL EXAM' UNTUK INDOBERT 🔥")
    print("="*60)
    
    # Inisialisasi Processor
    processor = ChatBatchProcessor()
    
    # 1. UJI SPLITTING (Memecah Chat Panjang)
    print(f"\n1️⃣  MENGUJI LOGIKA PEMOTONGAN CHAT...")
    chunks = processor.smart_split(raw_chat_rafay)
    print(f"   ➤ Total Potongan Chat: {len(chunks)} bagian.")
    
    # 2. UJI EKSTRAKSI (Cek Apakah Data Tertukar?)
    print(f"\n2️⃣  MENGUJI KECERDASAN EKSTRAKSI (Forensik Data)...")
    
    syaichoni_passed = False
    lailan_passed = False
    
    for i, chunk in enumerate(chunks):
        if processor.is_junk(chunk):
            continue
            
        # Clean HP bug (+62 jadi 0)
        clean_text = chunk.replace("+62", "0").replace("-", "")
        
        # Predict pakai IndoBERT
        res = processor.pipeline.predict(clean_text)
        
        if res:
            driver = str(res.get('DRIVER', '-')).lower()
            plate = str(res.get('PLATE', '-')).lower()
            
            # Cek Syaichoni
            if "syaichoni" in driver:
                print(f"\n   🕵️‍♂️  CEK DATA SYAICHONI (Chunk #{i+1}):")
                print(f"      Driver Terdeteksi: {res.get('DRIVER')}")
                print(f"      Plat Terdeteksi  : {res.get('PLATE')}")
                
                if "n 8872 rk" in plate:
                    print("      ✅ STATUS: LULUS (Plat Benar!)")
                    syaichoni_passed = True
                else:
                    print(f"      ❌ STATUS: GAGAL (Plat Salah! Seharusnya N 8872 RK)")

            # Cek Lailan
            if "lailan" in driver:
                print(f"\n   🕵️‍♂️  CEK DATA LAILAN (Chunk #{i+1}):")
                print(f"      Driver Terdeteksi: {res.get('DRIVER')}")
                print(f"      Plat Terdeteksi  : {res.get('PLATE')}")
                
                if "s 9272 up" in plate:
                    print("      ✅ STATUS: LULUS (Plat Benar!)")
                    lailan_passed = True
                else:
                    print(f"      ❌ STATUS: GAGAL (Plat Salah! Seharusnya S 9272 UP)")
    
    print("\n" + "="*60)
    print("KESIMPULAN AKHIR:")
    if syaichoni_passed and lailan_passed:
        print("🎉 SELAMAT! MODEL SUDAH AMAN & FINAL.")
        print("   Tidak perlu training ulang. Lanjut ke Bab 4 Skripsi.")
    else:
        print("⚠️ BAHAYA! MASIH ADA DATA TERTUKAR.")
        print("   Cek kembali regex splitter kamu.")
    print("="*60)

if __name__ == "__main__":
    run_proof_test()