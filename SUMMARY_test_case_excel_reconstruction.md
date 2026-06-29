# Summary: test_case_excel_reconstruction.txt

## 📊 Statistik File

- **Total Request Order (Blok Chat)**: 29 request
- **Total Unit Individual**: 91 unit
- **Periode**: 02 April 2026 - 30 April 2026 (29 hari)
- **Format**: Chat mentah simulasi (rekonstruksi dari Excel)

## 🎯 Tujuan File Ini

File ini dibuat untuk **validasi manual** dengan admin lapangan:
1. Admin bisa menghitung manual: berapa request order (blok) dan berapa unit
2. Hasil manual dibandingkan dengan output sistem
3. Menghitung tingkat kesepakatan (agreement rate)

## 📋 Expected Ground Truth

Jika sistem bekerja dengan benar, seharusnya mengekstrak:

### **Jumlah Blok Order: 29 request**

### **Total Unit: 91 unit**

### **Expected Entities per Unit: 9 entitas**
1. Tanggal RO (per request)
2. Waktu/Tanggal Loading (per unit)
3. Lokasi Pickup (per unit)
4. Rute/Tujuan (per unit)
5. Jumlah Unit (per request, contoh: 2 UNIT, 5 UNIT)
6. Tipe Kendaraan (per request/unit)
7. Driver (per unit)
8. Nomor Plat (per unit)
9. Nomor HP (per unit)

### **Total Expected Entities: 91 unit × 9 = 819 entitas**

**Note:** Satu request order bisa berisi multiple unit (2-7 unit), sehingga:
- 29 blok chat = 29 "REQUEST ORDER ONCALL"
- 91 row data = 91 unit individual dengan driver/plat berbeda

## 🔬 Cara Validasi

### **Step 1: Hitung Manual (oleh Admin)**
Minta admin mengisi form:
- Jumlah blok order (hitung "REQUEST ORDER ONCALL"): [ ___ ]
- Total unit individual (driver/plat yang berbeda): [ ___ ]
- Untuk setiap unit, catat 9 entitas di atas

### **Step 2: Run Sistem**
```bash
# Jalankan sistem NER dengan file ini sebagai input
python stage2_pair_visual_test.py
# atau
python run_ner_test_bukti.py
```

### **Step 3: Bandingkan**
| Metrik | Manual (Admin) | Sistem | Match? |
|--------|----------------|--------|--------|
| Jumlah Blok Order | [ ___ ] (expected: 29) | [ ___ ] | [ ] |
| Total Unit | [ ___ ] (expected: 91) | [ ___ ] | [ ] |
| Total Entitas | [ ___ ] (expected: 819) | [ ___ ] | [ ] |

## ⚠️ Catatan Penting

1. **Format Clean**: File ini dibuat dengan format yang relatif bersih (standar)
2. **Tidak ada typo**: Untuk memudahkan validasi manual
3. **Tidak ada noise**: Tidak ada metadata chat, emoji, atau noise
4. **Konsisten**: Setiap order memiliki struktur yang sama

## 💡 Tips untuk Admin Validator

Saat menghitung manual, perhatikan:
- Setiap "REQUEST ORDER ONCALL" = 1 order baru
- Hitung semua atribut yang terisi (tanggal, lokasi, driver, plat, dll)
- Jika ada atribut yang kosong, jangan hitung

## 📊 Distribusi Tipe Kendaraan (Expected)

Berdasarkan data Excel asli:
- CDDL 24 CBM: ~70 order
- TRONTON 50 CBM: ~19 order
- FUSOLONG 50 CBM: ~2 order

## 🎓 Cara Pakai untuk Skripsi

1. Minta admin isi form validasi untuk file ini
2. Run sistem dengan file ini
3. Buat tabel perbandingan
4. Hitung agreement rate
5. Masukkan ke Bab 4 sebagai bukti validasi

## ✅ Expected Result

Jika sistem bekerja dengan benar:
- **29 blok order** terdeteksi (29 kali "REQUEST ORDER ONCALL")
- **91 row data** di tabel output (91 unit dengan driver/plat berbeda)
- **819 entitas** total
- Agreement rate: 100% (819/819 entitas match)
- Tidak ada false positive
- Tidak ada false negative

## 💡 Contoh Struktur di File

```
REQUEST ORDER ONCALL 04 APRIL 2026      ← 1 blok order

3 UNIT TRONTON 50 CBM                    ← Jumlah unit dalam request ini
Lokasi : ANGKE POGLAR + ARGOPANTES
Waktu loading : 05-04-2026
Rute/tujuan : PKU
Driver : Wandrianto                      ← Unit 1
Nopol : BK 8326 VY
No hp : 081273367151

Lokasi : ARGOPANTES
Waktu loading : 05-04-2026
Rute/tujuan : PKU
Driver : Robbi Adam                      ← Unit 2
Nopol : BM 9187 AU
No hp : 081367325483

Lokasi : ARGOPANTES
Waktu loading : 06-04-2026
Rute/tujuan : PKU
Driver : M. Ruspianto                    ← Unit 3
Nopol : BM 8359 AU
No hp : 0812689907
```

**Perhitungan:**
- Blok order: 1
- Unit dalam blok: 3
- Row data di tabel: 3
- Entitas per unit: 9
- Total entitas blok ini: 3 × 9 = 27 entitas

---

**Generated Date**: 2026-06-25
**Purpose**: Validasi Manual vs Sistem
**Status**: Ready for validation
