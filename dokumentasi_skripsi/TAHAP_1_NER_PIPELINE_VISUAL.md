# TAHAP 1: EKSTRAKSI INFORMASI (Named Entity Recognition)
## Alur Transformasi Data untuk Diagram Visio

---

## 📊 PIPELINE VISUAL - TAHAP NER

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAHAP 1: EKSTRAKSI INFORMASI (NER)           │
└─────────────────────────────────────────────────────────────────┘
```

### **KOTAK 1: INPUT TEKS MENTAH**
```
📝 Input Data
├─ Sumber: Pesan WhatsApp
├─ Format: Teks Unicode Indonesia
├─ Contoh Input: "Kirim 5 kg kopi arabika ke Jl. Merdeka 45 Jakarta"
└─ Karakteristik: Satu kalimat tunggal, tidak terstruktur
```

**Penjelasan untuk Bagan:**  
> "Pesan WhatsApp pelanggan tentang pesanan logistik yang masuk sebagai teks mentah"

---

### **KOTAK 2: TOKENISASI**
```
🔄 Proses Pembagian Teks
├─ Tool: WordPiece Tokenizer (dari IndoBERT)
├─ Proses: Memecah kalimat menjadi token-token kecil
├─ Contoh Proses:
│  "Kirim 5 kg kopi arabika ke Jl. Merdeka 45 Jakarta"
│  ↓
│  ["Kirim", "5", "kg", "kopi", "arabika", "ke", "Jl", ".", "Merdeka", "45", "Jakarta"]
├─ Output: Urutan token terindeks
└─ Catatan: Setiap token diberi ID numerik
```

**Penjelasan untuk Bagan:**  
> "Memecah kalimat menjadi kata-kata kecil yang bisa diproses model"

---

### **KOTAK 3: EMBEDDING & INPUT PREPARATION**
```
🎯 Konversi Token ke Representasi Numerik
├─ Proses: Token → Angka-angka (Embedding)
├─ Langkah:
│  • Setiap token diubah ke angka yang mewakilinya
│  • Ditambahkan Special Tokens: [CLS] di awal, [SEP] di akhir
│  • Format siap untuk neural network
├─ Output: Daftar angka yang mewakili kalimat
└─ Dimensi: Deretan angka untuk 11 token
```

**Penjelasan untuk Bagan:**  
> "Mengubah setiap kata menjadi angka-angka yang dipahami neural network"

---

### **KOTAK 4: TRANSFORMER LAYERS (IndoBERT)**
```
🧠 Pemahaman Konteks Mendalam
├─ Model: indolem/indobert-base-uncased
├─ Proses Internal:
│  • Layer 1-12: Mempelajari hubungan antar kata
│  • Attention Mechanism: Fokus pada kata mana yang penting
│  • Context Understanding: Memahami konteks pesanan
├─ Input: Deretan angka (embedding)
└─ Output: Representasi semantik setiap token
```

**Penjelasan untuk Bagan:**  
> "Model neural yang sudah terlatih mempelajari makna dan konteks setiap kata dalam pesanan"

---

### **KOTAK 5: CLASSIFIER LAYER (NER Head)**
```
🏷️ Penentuan Label Entitas Logistik
├─ Task: Token Classification
├─ Label Output (8 Entitas):
│  • B-PRODUK / I-PRODUK (Nama barang)
│  • B-KUANTITAS / I-KUANTITAS (Jumlah)
│  • B-LOKASI / I-LOKASI (Alamat tujuan)
│  • B-INSTRUKSI / I-INSTRUKSI (Perintah khusus)
├─ Proses: Setiap token diprediksi labelnya
├─ Skema BIO:
│  • B- (Begin): Permulaan entitas
│  • I- (Inside): Kelanjutan entitas
│  • O (Outside): Bukan entitas
└─ Output: Label untuk setiap token
```

**Penjelasan untuk Bagan:**  
> "Mengklasifikasikan setiap kata ke dalam kategori logistik (produk, jumlah, lokasi, instruksi)"

---

### **KOTAK 6: OUTPUT PREDIKSI**
```
✅ Hasil Ekstraksi Entitas
├─ Format Output:
│  Token          │ Label
│  ───────────────┼─────────────────
│  Kirim          │ B-INSTRUKSI
│  5              │ B-KUANTITAS
│  kg             │ I-KUANTITAS
│  kopi           │ B-PRODUK
│  arabika        │ I-PRODUK
│  ke             │ O
│  Jl             │ B-LOKASI
│  .              │ I-LOKASI
│  Merdeka        │ I-LOKASI
│  45             │ I-LOKASI
│  Jakarta        │ I-LOKASI
├─ Confidence Score: Probabilitas setiap prediksi (0-100%)
└─ Data Terstruktur: Siap untuk tahap pencocokan relasi
```

**Penjelasan untuk Bagan:**  
> "Hasil akhir: Setiap kata sudah diidentifikasi kategorinya sebagai produk, jumlah, lokasi, atau instruksi"

---

## 🎯 RINGKASAN ALUR TAHAP 1

| # | Kotak | Input | Proses | Output |
|---|-------|-------|--------|--------|
| 1 | Input Teks | Pesan WhatsApp | - | Teks mentah |
| 2 | Tokenisasi | Teks kalimat | Pemecahan kata | Daftar token |
| 3 | Embedding | Token | Konversi ke angka | Angka representasi |
| 4 | Transformer | Angka | Pembelajaran konteks | Vektor semantik |
| 5 | Classifier | Vektor | Prediksi label | Probabilitas label |
| 6 | Output | Probabilitas | Konversi ke label | Entitas + Label |

---

## 📐 TEMPLATE UNTUK KOTAK-KOTAK VISIO

**Gunakan template ini untuk menggambar di Visio:**

```
┌──────────────────────────────────┐
│     1️⃣ INPUT TEKS MENTAH         │
│  "Kirim 5kg kopi ke Jakarta"    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│     2️⃣ TOKENISASI                │
│  Memecah teks → Token-token      │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│     3️⃣ EMBEDDING & PREP          │
│  Token → Angka Numerik           │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│     4️⃣ TRANSFORMER               │
│  (IndoBERT-12 Layers)            │
│  Pembelajaran Konteks & Makna    │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│     5️⃣ NER CLASSIFIER             │
│  Prediksi 8 Label Entitas        │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│     6️⃣ OUTPUT                     │
│  Token + Label (BIO Scheme)      │
└──────────────────────────────────┘
```

---

## 💡 CATATAN UNTUK PENJELASAN GAMBAR

**Jika perlu teks tambahan di diagram Anda:**

- **Kotak 1**: "Pesan WhatsApp pelanggan tentang pesanan logistik"
- **Kotak 2**: "WordPiece Tokenizer memecah kalimat menjadi token kecil"
- **Kotak 3**: "Setiap token diubah menjadi angka yang dipahami model"
- **Kotak 4**: "Model IndoBERT mempelajari konteks dan hubungan antar kata"
- **Kotak 5**: "Classifier memprediksi label kategori logistik (BIO Scheme)"
- **Kotak 6**: "Entitas logistik teridentifikasi + Confidence Score"

---

**Panah Antar Kotak:** Satu arah (kiri ke kanan atau atas ke bawah) menunjukkan alur data transformasi.

