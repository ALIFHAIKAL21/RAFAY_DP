# TAHAP 2: PENCOCOKAN RELASI DATA (Sentence-Pair Classification)
## Alur Transformasi Data untuk Diagram Visio

---

## 📊 PIPELINE VISUAL - TAHAP PENCOCOKAN RELASI

```
┌─────────────────────────────────────────────────────────────────┐
│              TAHAP 2: PENCOCOKAN RELASI DATA                    │
│           (Apakah Pesanan Lanjutan Cocok dengan Pesanan Induk?) │
└─────────────────────────────────────────────────────────────────┘
```

### **KOTAK 1: INPUT PASANGAN KALIMAT**
```
📝 Input Data (Dua Kalimat)
├─ Kalimat A (Pesanan Induk):
│  Contoh: "Kirim 5 kg kopi arabika premium ke Jl. Merdeka 45 Jakarta"
├─ Kalimat B (Pesanan Susulan/Revisi):
│  Contoh: "Tambah 3 kg kopi arabika yang sama ke alamat sebelumnya"
├─ Task: Mencocokkan apakah kedua pesanan COCOK (same entity) atau TIDAK COCOK
└─ Karakteristik: Dua kalimat terpisah, konteks berbeda tetapi mungkin terkait
```

**Penjelasan untuk Bagan:**  
> "Dua pesan WhatsApp dari pelanggan: satu pesanan awal dan satu pesanan revisi/lanjutan"

---

### **KOTAK 2: TOKENISASI PASANGAN**
```
🔄 Proses Pembagian Teks (Dua Kalimat)
├─ Tool: WordPiece Tokenizer (dari IndoBERT)
├─ Proses:
│  Kalimat A → ["Kirim", "5", "kg", "kopi", "arabika", "premium", "ke", "Jl", ".", "Merdeka", "45", "Jakarta"]
│  Kalimat B → ["Tambah", "3", "kg", "kopi", "arabika", "yang", "sama", "ke", "alamat", "sebelumnya"]
├─ Penggabungan: Token A + [SEP] + Token B
├─ Output: Urutan token pasangan terindeks
└─ Catatan: Separator [SEP] menandai batas antar kalimat
```

**Penjelasan untuk Bagan:**  
> "Memecah kedua kalimat menjadi token-token kecil dan menggabungnya dengan separator"

---

### **KOTAK 3: EMBEDDING & SEQUENCE PAIR SETUP**
```
🎯 Konversi Pasangan Token ke Numerik
├─ Proses: Token A & B → Angka-angka Representasi
├─ Langkah:
│  • Kalimat A: Token → Embedding numerik
│  • Separator: [SEP] → Token khusus
│  • Kalimat B: Token → Embedding numerik
│  • Segment IDs: Tandai token milik kalimat A atau B
│  • Special Tokens: [CLS] di awal, [SEP] di tengah, [SEP] di akhir
├─ Output: Dua deretan angka yang mewakili pasangan kalimat
└─ Dimensi: Angka untuk ~22 token gabungan
```

**Penjelasan untuk Bagan:**  
> "Mengubah dua kalimat menjadi angka-angka yang dipahami model, dengan penanda untuk setiap kalimat"

---

### **KOTAK 4: TRANSFORMER LAYERS (IndoBERT)**
```
🧠 Pemahaman Hubungan Dua Kalimat
├─ Model: indobenchmark/indobert-base-p2
├─ Proses Internal:
│  • Layer 1-12: Mempelajari hubungan ANTAR kalimat
│  • Attention: Fokus pada kata-kata yang menghubungkan pesanan
│  • Context: Memahami apakah pesanan lanjutan merujuk pesanan induk
│  • Semantic Matching: Membandingkan kesamaan entitas (produk, lokasi)
├─ Input: Dua deretan angka (embedding pasangan)
└─ Output: Representasi semantik gabungan kedua kalimat
```

**Penjelasan untuk Bagan:**  
> "Model neural yang sudah terlatih membandingkan kedua pesan dan memahami hubungannya"

---

### **KOTAK 5: SEQUENCE CLASSIFIER (Matching Head)**
```
🏷️ Penentuan Kesesuaian Pesanan
├─ Task: Sequence-Pair Classification
├─ Label Output (2 Kelas):
│  • Class 1: COCOK (Entailment)
│    ✓ Pesanan lanjutan mengacu entitas yang sama dengan pesanan induk
│    ✓ Contoh: "Tambah kopi arabika yang sama ke alamat sebelumnya"
│       (sama-sama produk: kopi arabika, sama lokasi)
│
│  • Class 0: TIDAK COCOK (Non-Entailment)
│    ✗ Pesanan lanjutan tidak terkait atau merujuk entitas berbeda
│    ✗ Contoh: "Tambah 2 kg gula putih ke alamat lain"
│       (produk berbeda, lokasi berbeda)
│
├─ Proses: Classifier memprediksi Class dan Confidence Score
└─ Output: Probabilitas untuk setiap class (0-100%)
```

**Penjelasan untuk Bagan:**  
> "Classifier memutuskan apakah pesanan lanjutan COCOK dengan pesanan induk berdasarkan entitas (produk, lokasi, dll)"

---

### **KOTAK 6: OUTPUT PREDIKSI & SKOR KEPERCAYAAN**
```
✅ Hasil Pencocokan Relasi
├─ Output Format:
│  Pesanan Induk: "Kirim 5 kg kopi arabika ke Jl. Merdeka 45 Jakarta"
│  Pesanan Lanjutan: "Tambah 3 kg kopi arabika ke alamat sebelumnya"
│  ├─ Prediksi: ✓ COCOK (Entailment)
│  ├─ Skor Cocok: 92.5% (kepercayaan tinggi)
│  └─ Skor Tidak Cocok: 7.5%
│
├─ Interpretasi:
│  Model yakin 92.5% bahwa kedua pesanan merujuk entitas yang sama
│  (sama-sama: kopi arabika, sama lokasi: Jl. Merdeka 45 Jakarta)
│
└─ Keputusan Bisnis:
   Jika Skor Cocok > Threshold (misal 80%): GABUNGKAN pesanan
   Jika Skor Cocok ≤ Threshold: PISAHKAN sebagai pesanan baru
```

**Penjelasan untuk Bagan:**  
> "Hasil akhir: Probabilitas apakah kedua pesanan COCOK atau TIDAK COCOK, dengan tingkat kepercayaan"

---

## 🎯 RINGKASAN ALUR TAHAP 2

| # | Kotak | Input | Proses | Output |
|---|-------|-------|--------|--------|
| 1 | Input Pasangan | 2 Pesan WhatsApp | - | Dua teks mentah |
| 2 | Tokenisasi | Dua kalimat | Pemecahan + penggabungan | Daftar token pasangan |
| 3 | Embedding | Token pasangan | Konversi ke angka | Angka representasi dua kalimat |
| 4 | Transformer | Angka | Pembelajaran relasi | Vektor semantik pasangan |
| 5 | Classifier | Vektor | Prediksi kesesuaian | Probabilitas Cocok/Tidak Cocok |
| 6 | Output | Probabilitas | Konversi keputusan | Label + Confidence Score |

---

## 📐 TEMPLATE UNTUK KOTAK-KOTAK VISIO

**Gunakan template ini untuk menggambar di Visio:**

```
┌──────────────────────────────────────┐
│   1️⃣ INPUT PASANGAN KALIMAT         │
│  Pesan Induk + Pesan Lanjutan       │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   2️⃣ TOKENISASI PASANGAN             │
│  Memecah & Gabung → Token-token      │
│          dengan [SEP]                │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   3️⃣ EMBEDDING & SETUP               │
│  Pasangan Token → Angka Numerik      │
│       dengan Segment IDs             │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   4️⃣ TRANSFORMER (IndoBERT-P2)       │
│  Mempelajari Hubungan Antar Kalimat  │
│   (12 Layers Deep Understanding)     │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   5️⃣ SEQUENCE CLASSIFIER             │
│  Prediksi Kesesuaian:                │
│  ✓ COCOK atau ✗ TIDAK COCOK         │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   6️⃣ OUTPUT HASIL                    │
│  Label + Confidence Score (%)        │
│  Keputusan: Gabung atau Pisah?       │
└──────────────────────────────────────┘
```

---

## 💡 CATATAN UNTUK PENJELASAN GAMBAR

**Jika perlu teks tambahan di diagram Anda:**

- **Kotak 1**: "Pesan WhatsApp pesanan induk + pesan revisi atau pesanan lanjutan"
- **Kotak 2**: "WordPiece Tokenizer memecah dan menggabungkan dua kalimat dengan separator"
- **Kotak 3**: "Setiap token diubah menjadi angka, dengan penanda kalimat mana yang mana"
- **Kotak 4**: "Model IndoBERT mempelajari hubungan dan kesamaan makna antar kedua pesan"
- **Kotak 5**: "Classifier memprediksi: Apakah kedua pesanan COCOK (merujuk entitas sama)?"
- **Kotak 6**: "Hasil: Prediksi kesesuaian + skor kepercayaan untuk pengambilan keputusan"

---

## 🎯 DECISION THRESHOLD (Opsional untuk Diagram)

**Jika ingin menambahkan decision logic:**

```
Output Classifier:
  Skor Cocok = 92.5%
         │
         ├─ > 80% (Threshold) → ✓ GABUNGKAN PESANAN
         │
         └─ ≤ 80% → ✗ PISAHKAN SEBAGAI PESANAN BARU
```

**Penjelasan:** "Jika model yakin pesanan cocok (>80%), sistem secara otomatis menggabungkan pesanan lanjutan dengan pesanan induk"

---

## 🔗 HUBUNGAN ANTAR TAHAP

```
TAHAP 1 (NER)              →        TAHAP 2 (Sequence-Pair)
┌──────────────────┐                ┌──────────────────┐
│ Input: Pesan A   │                │ Input: Pesan A   │
│ Output:          │                │         + Pesan B│
│ • Produk: Kopi  │────────────────→│ Output:          │
│ • Lokasi: Jkt   │                 │ Cocok/Tidak      │
│ • Qty: 5kg       │                │ Cocok?           │
└──────────────────┘                └──────────────────┘
     (Entitas)                       (Relationship)
```

**Alur Bisnis Lengkap:**
1. Pesan masuk → Ekstraksi entitas (TAHAP 1)
2. Ada pesan lanjutan? → Bandingkan dengan pesan sebelumnya (TAHAP 2)
3. Jika cocok → Merge pesanan; Jika tidak → Pesanan baru

