import sys
from pathlib import Path

# Setup Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from src.inference.batch_processor import ChatBatchProcessor

# SIMULASI CHAT MINGGUAN YANG BERANTAKAN (Skenario Terburuk Admin)
chat_mingguan = """
[08:00] Admin A: Pagi semua, jangan lupa absen ya!
[08:05] Admin B: Wkwkwk, kopi mana kopi?
[09:00, 4/2/2026] Akbar Rafay: REQUEST ORDER ONCALL 04 FEBRUARI 2026:
RAFAY
3 unit Cddl 24 Cbm
Lokasi : Megahub
Waktu loading : segera
Rute/tujuan : CGK - JATENG
driver  : KARYADI
Nopol  : AD 8517 BA
No hp  :085865762797
[09:15] Admin A: Siap pak, diproses.
[10:00] Admin C: Info dong, stok ban di gudang aman?
[11:00, 4/2/2026] Akbar Rafay: REQUEST TAMBAHAN
2 UNIT TWB 50 CBM
Lokasi : CIKOKOL
Waktu loading : SEGERA
driver  : AGUS
Nopol  : D 9667 AF
"""

def test_kematangan_ai():
    print("📋 MEMULAI TES REAL CASE: 'SI SARINGAN CERDAS'")
    print("-" * 50)
    
    processor = ChatBatchProcessor()
    
    # 1. Simpan ke file mentah
    with open("minggu_ini.txt", "w", encoding="utf-8") as f:
        f.write(chat_mingguan)
        
    # 2. Jalankan Batch Processor
    df = processor.process_file("minggu_ini.txt", output_excel="tes_final_rafay.xlsx")
    
    if df is not None:
        print(f"\n✅ AI Berhasil Menemukan {len(df)} Orderan dari chat yang berantakan!")
        print("\nIsi Data yang ditemukan:")
        print(df[['UNIT_TYPE', 'ORIGIN', 'DRIVER', 'PLATE']])
    else:
        print("\n❌ Gagal menemukan data.")

if __name__ == "__main__":
    test_kematangan_ai()