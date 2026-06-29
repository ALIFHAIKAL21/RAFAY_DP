# Draft Penjelasan Flowchart Sistem

Dokumen ini adalah draft ringkas untuk menjelaskan flowchart sistem pada Bab 4. Isinya dibuat sederhana agar mudah dikembangkan lagi menjadi paragraf formal.

## Inti Sistem

Sistem ini memproses teks order dari WhatsApp menjadi data operasional yang terstruktur. Terdapat dua model deep learning yang digunakan:

1. **Model 1: IndoBERT NER**
   Bertugas mengekstrak entitas dari teks, seperti tanggal RO, lokasi pickup, tujuan, tipe unit, waktu loading, driver, nomor polisi, dan nomor HP.

2. **Model 2: IndoBERT Sequence Pair Classification**
   Bertugas menilai apakah pesanan susulan cocok dengan pesanan induk yang sudah tersimpan di database.

NER digunakan untuk mengambil isi data. Sequence Pair Classification digunakan untuk menentukan kecocokan pesanan induk dan susulan.

## Penjelasan Per Langkah Flowchart

### 1. Input Teks Mentah

Sistem menerima teks mentah dari WhatsApp. Format pesan dapat berbeda-beda karena berasal dari percakapan operasional lapangan.

Contoh nyata:

```text
Akbar Rafay: REQUEST ORDER ONCALL 01 MEI 2026

2 UNIT TWB 50 CBM
Lokasi : CIKARANG
Waktu loading : 06:00/ 02-05-2026
Rute/tujuan : CGK - SUB
Driver : Asep
Nopol : L 1411 YA
No hp : +62 821-120-0000
```

Pada tahap ini data masih berbentuk teks bebas, belum bisa langsung masuk ke tabel operasional.

### 2. Preprocessing

Preprocessing membersihkan teks agar lebih stabil sebelum diproses model. Tahap ini menangani noise seperti metadata WhatsApp, spasi berlebih, typo label field, dan variasi penulisan.

Contoh:

```text
Waktu lodng : 07:00
DRVER : Dedi
No hpp : 08151207919
```

Setelah dinormalisasi menjadi bentuk yang lebih konsisten:

```text
Waktu loading : 07:00
Driver : Dedi
No hp : 08151207919
```

Di project, proses ini diwakili oleh fungsi seperti `prepare_text_for_ner()`.

### 3. Split / Segmentasi Blok Pesan

Jika user memasukkan banyak pesanan sekaligus, sistem tidak memprosesnya sebagai satu teks besar. Sistem memecah input menjadi beberapa blok order.

Contoh:

```text
REQUEST ORDER ONCALL 20 MEI 2026
...

REQUEST ORDER ULANG ONCALL 20 MEI 2026
...
```

Kedua pesan tersebut dipisahkan menjadi blok berbeda. Tujuannya agar pesanan induk dan pesanan susulan bisa diproses secara berurutan.

Di project, proses ini diwakili oleh `split_new_order_messages()`.

### 4. Model 1: NER

Setiap blok pesan diproses oleh model IndoBERT NER. Model ini tidak menentukan apakah pesan adalah pesanan induk atau susulan. Model hanya menandai entitas.

Contoh hasil ekstraksi:

```text
CIKARANG -> Pickup
CGK - SUB -> Tujuan
Asep -> Driver
L 1411 YA -> No. Plat
082112000000 -> Kontak Driver
```

Jadi fungsi utama Model 1 adalah mengubah teks bebas menjadi atribut operasional.

Di project, proses prediksi NER diwakili oleh `ner_predict_spans_with_scores()`.

### 5. Post-processing Hasil NER

Hasil NER masih berupa token atau potongan entitas. Post-processing menyusun hasil tersebut menjadi baris data operasional.

Output akhirnya berbentuk seperti tabel:

```text
Tgl RO | Tgl Muat | Pickup | Tujuan | No. Plat | Type Truck | Driver | Kontak Driver
```

Tahap ini penting karena database dan tampilan website membutuhkan data yang sudah berbentuk row, bukan token mentah.

Di project, proses ini diwakili oleh `rows_from_new_order_text()`.

### 6. Identifikasi Jenis Pesanan

Setelah data menjadi terstruktur, sistem menentukan konteks pesan: apakah termasuk pesanan induk/awal atau pesanan susulan.

Keputusan ini dilakukan oleh logika sistem, bukan oleh model NER.

Dasar identifikasi dapat berupa:

- kata seperti `REQUEST ORDER`
- kata seperti `ORDER ULANG`, `TAMBAHAN`, atau `SUSULAN`
- kondisi data di database
- apakah ada order lama yang relevan dan masih belum lengkap

Di flowchart, tahap ini menggunakan bentuk belah ketupat karena menghasilkan cabang keputusan.

### 7. Pesanan Induk / Awal Masuk ke Local DB

Jika blok pesan adalah pesanan induk, hasil ekstraksi disimpan ke database sebagai state pesanan.

Database tidak hanya menyimpan data, tetapi juga menjadi state order. Artinya database menyimpan kondisi terbaru dari pesanan, misalnya:

- jumlah unit target
- unit yang sudah terisi
- slot kosong
- driver yang sudah tercatat
- nomor polisi yang sudah tercatat

Contoh:

```text
5 UNIT TWB 50 CBM
Lokasi : CIKARANG
Rute/tujuan : CGK - SUB
Driver pertama sudah ada
4 slot lain masih kosong
```

Data tersebut disimpan sebagai pesanan induk yang nantinya bisa dilengkapi oleh pesanan susulan.

### 8. Pembentukan Kandidat Pasangan Pesanan

Jika blok pesan adalah pesanan susulan, sistem tidak langsung menyimpannya ke database. Sistem terlebih dahulu mengambil kandidat pesanan induk dari Local DB.

Kandidat biasanya berasal dari order yang:

- masih memiliki slot kosong
- memiliki konteks mirip dengan susulan
- memiliki tanggal RO, pickup, tujuan, atau tipe unit yang relevan

Kemudian sistem membentuk pasangan:

```text
Pesanan induk dari DB + Pesanan susulan baru
```

Contoh:

```text
Kandidat Induk:
06 FEB 2026 | CIKARANG | CGK - SUB | TWB 50 CBM | terisi 3/5

Pesanan Susulan:
REQUEST ORDER ULANG ONCALL 06 FEB 2026
CIKARANG
CGK - SUB
Driver : Reza
Nopol : D 9033 ZZ
```

Pasangan seperti inilah yang diberikan ke Model 2.

Di project, proses ini diwakili oleh `build_stage2_order_candidates()` dan `build_stage2_match_preview()`.

### 9. Model 2: Sequence Pair Classification

Model 2 menerima pasangan pesanan induk dan susulan. Tugasnya adalah memprediksi apakah keduanya cocok.

Output model berupa:

```text
MATCH
```

atau:

```text
NO_MATCH
```

Model 2 digunakan karena rule biasa tidak selalu cukup untuk menangani teks WhatsApp yang tidak rapi.

Contoh variasi yang sering muncul:

```text
REQUEST / REQEST / REQUESTT / REQUER
JATIM TENTATIVE / JATIM TENTATIF
CGK-SUB / CGK - SUB
Waktu loading / Waktu lodng / Waktu loding
```

Di project, proses prediksi pasangan diwakili oleh `predict_pairs()`.

### 10. Hasil Prediksi

Jika Model 2 menghasilkan MATCH, sistem menganggap pesanan susulan kemungkinan besar milik pesanan induk tertentu.

Jika hasilnya NO_MATCH, sistem tidak memaksa penggabungan. Pesanan dapat disimpan sebagai pesanan baru atau ditahan sebagai audit ketidakcocokan.

Tahap ini penting untuk mencegah susulan masuk ke order yang salah.

### 11. Merge Pesanan

Jika hasilnya MATCH, sistem tetap melakukan validasi aturan bisnis sebelum merge.

Validasi ini mencakup:

- tanggal RO cocok
- pickup cocok
- tujuan cocok
- tipe truck cocok
- slot kosong masih tersedia
- driver, nopol, atau nomor HP tidak duplikat

Jika lolos validasi, hasil ekstraksi NER dari pesanan susulan digunakan untuk mengisi slot kosong pada pesanan induk.

Contoh:

```text
Sebelum susulan:
5 unit target, terisi 3, kosong 2

Susulan masuk:
2 driver baru

Sesudah merge:
5 unit target, terisi 5, kosong 0
```

Di project, keputusan merge dan validasi diwakili oleh `stage2_plan_for_candidate()` dan proses penyimpanan akhir oleh `sync_extraction_to_db()`.

### 12. Simpan sebagai Pesanan Baru / Audit Ketidakcocokan

Jika hasilnya NO_MATCH atau terjadi konflik, sistem tidak menggabungkan susulan ke pesanan induk.

Contoh konflik:

```text
Pesanan induk:
06 FEB 2026 | CIKARANG | CGK - SUB

Pesanan susulan:
06 FEB 2026 | ARGOPANTES | CGK - MES
```

Walaupun sama-sama order susulan, konteks lokasi dan tujuan berbeda. Sistem dapat menyimpan sebagai pesanan baru atau menahan data untuk audit.

### 13. Antarmuka Web

Hasil proses ditampilkan di antarmuka berbasis Streamlit. Antarmuka ini membantu user melihat:

- preview tabel output
- analitik ekstraksi
- analitik pencocokan
- score kepercayaan model
- hasil merge atau status audit

Tahap ini penting karena user operasional perlu melihat hasil akhir secara langsung, bukan hanya file mentah.

### 14. Download Output

Setelah data selesai diproses, user dapat mengunduh output dalam format Excel. Output ini digunakan sebagai hasil akhir operasional atau bahan evaluasi sistem.

## Kenapa Pesanan Induk Harus Masuk DB Dulu?

Pesanan induk perlu masuk DB lebih dulu karena sistem membutuhkan state order. State ini berisi kondisi terbaru dari pesanan, bukan hanya teks mentah.

Contoh informasi state:

```text
Qty target: 5
Terisi: 3
Sisa slot: 2
Driver terdaftar: A, B, C
```

Tanpa state DB, sistem tidak tahu apakah pesanan susulan harus:

- mengisi slot kosong
- dianggap duplikat
- dianggap order baru
- ditahan karena konflik

Karena itu, walaupun user memasukkan pesanan induk dan susulan secara bersamaan, sistem tetap memprosesnya per blok secara berurutan.

## Kenapa Tidak Cukup Rule-Based?

Rule-based tetap digunakan, tetapi hanya untuk membantu sistem mengambil kandidat dari database dan melakukan validasi bisnis.

Keputusan kecocokan akhir tetap membutuhkan Model 2 karena data WhatsApp sangat bervariasi.

Contoh masalah yang sulit ditangani rule sederhana:

```text
Header typo:
REQEST ORDER ULANG
REQUESTT ORDER
REQUER ORDER

Format rute beda:
CGK-SUB
CGK - SUB

Istilah beda:
JATIM TENTATIVE
JATIM TENTATIF

Pesan susulan tidak lengkap:
bang ini tambahan buat argopantes pku ya
```

Dengan model Sequence Pair Classification, sistem dapat menilai kecocokan berdasarkan konteks pasangan pesan, bukan hanya pencocokan kata yang kaku.

## Ringkasan Sederhana

Alur sistem dapat diringkas sebagai berikut:

```text
NER mengambil isi data dari teks.
Post-processing mengubah hasil NER menjadi tabel.
Sistem menentukan apakah data adalah induk atau susulan.
Pesanan induk disimpan sebagai state di database.
Pesanan susulan dicocokkan dengan state induk menggunakan Model 2.
Jika MATCH dan lolos validasi, data digabung.
Jika NO_MATCH atau konflik, data disimpan sebagai order baru atau audit.
```

## Draft Prompt untuk Gemini

Gunakan instruksi berikut jika ingin mengembangkan dokumen ini menjadi paragraf skripsi:

```text
Tolong ubah draft penjelasan flowchart ini menjadi paragraf akademik Bab 4 bagian Perancangan dan Implementasi Sistem. Gunakan bahasa Indonesia formal, sederhana, dan mudah dipahami dosen penguji. Jangan terlalu teknis, tetapi tetap jelaskan peran dua model deep learning: IndoBERT NER untuk ekstraksi entitas dan IndoBERT Sequence Pair Classification untuk pencocokan pesanan induk dan susulan. Jelaskan juga bahwa database berperan sebagai state pesanan, bukan hanya tempat penyimpanan.
```
