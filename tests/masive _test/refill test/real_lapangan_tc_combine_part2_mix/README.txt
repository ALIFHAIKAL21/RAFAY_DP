Test set: Real-lapangan refill mix (turunan pola tc_combine_part2)
Folder: tests/masive _test/refill test/real_lapangan_tc_combine_part2_mix

Tujuan:
- Meniru pola grup asli: campuran NEW ORDER + PARTIAL + REFILL + REVISI ringan.
- Bukan data sintetis "rapi", tapi sengaja ada variasi format, typo kecil, dan style chat lapangan.

File:
1) tc_day1_seed_real_part2_mix.txt
   - Seed day-1.
   - Berisi order campuran assigned + partial (masih banyak slot kosong).
   - Konteks mengikuti pola tc_combine_part2 (ARGOPANTES/CIKOKOL, CGK-SUB/PKU/MES/JATIM).

2) tc_day2_refill_mix_real_part2.txt
   - Day-2.
   - Berisi refill slot partial dari day-1 (isi driver/nopol/no hp) + sebagian order baru.
   - Ada 1 contoh revisi field (nopol) agar uji refill+revisi jalan bareng.

Saran uji:
1. Jalankan day1 dulu, simpan output baseline.
2. Jalankan day1+day2 (gabung) untuk lihat apakah partial terisi.
3. Pantau:
   - jumlah PARTIAL turun
   - jumlah ASSIGNED naik
   - tidak ada duplikasi slot yang sudah terisi

Command contoh (app copy ML refill):
.\venv\Scripts\python.exe tests\run_refill_test_app_copy.py --day1 "tests/masive _test/refill test/real_lapangan_tc_combine_part2_mix/tc_day1_seed_real_part2_mix.txt" --day2 "tests/masive _test/refill test/real_lapangan_tc_combine_part2_mix/tc_day2_refill_mix_real_part2.txt"

