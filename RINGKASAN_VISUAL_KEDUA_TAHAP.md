# RINGKASAN VISUAL KEDUA TAHAP
## Bagan Arsitektur Sistem untuk Skripsi (Kerangka Pemikiran)

---

## 📋 ALUR LENGKAP SISTEM (Input → Output)

```
═══════════════════════════════════════════════════════════════════════════════
                    SISTEM EKSTRAKSI & PENCOCOKAN PESANAN LOGISTIK
═══════════════════════════════════════════════════════════════════════════════

                               TAHAP 1: EKSTRAKSI INFORMASI
                                  (Named Entity Recognition)

┌─────────────────────────────────────────────────────────────────────────┐
│  INPUT: Pesan WhatsApp Tunggal                                          │
│  Contoh: "Kirim 5 kg kopi arabika ke Jl. Merdeka 45 Jakarta"           │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ① TOKENISASI: Memecah teks → Token-token kecil                         │
│  ["Kirim", "5", "kg", "kopi", "arabika", ..., "Jakarta"]              │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ② EMBEDDING: Ubah token → Representasi numerik                        │
│  Setiap kata menjadi angka-angka yang dipahami model                    │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ③ TRANSFORMER (IndoBERT): Pembelajaran konteks mendalam               │
│  12 layers yang memahami makna dan hubungan antar kata                 │
│  ★ Model: indolem/indobert-base-uncased                                │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ④ CLASSIFIER (NER Head): Prediksi label untuk setiap token            │
│  Token → Label entitas logistik (Produk, Qty, Lokasi, Instruksi)      │
│  Skema BIO (Begin-Inside-Outside)                                      │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT: Entitas Teridentifikasi (8 Label)                              │
│  ✓ PRODUK: Kopi arabika                                                │
│  ✓ KUANTITAS: 5 kg                                                     │
│  ✓ LOKASI: Jl. Merdeka 45 Jakarta                                      │
│  ✓ INSTRUKSI: Kirim                                                    │
│  (+ Confidence Score untuk setiap prediksi)                             │
└─────────────────────────┬──────────────────────────────────────────────┘
                          │
                          │ [Data Terstruktur untuk Tahap 2]
                          │
     ╔════════════════════╩════════════════════╗
     │                                         │
     │ Apakah ada pesanan lanjutan/revisi?   │
     │                                         │
     └────────────┬────────────────────────────┘
                  │
                  ▼ (YA) Pesanan lanjutan masuk
                  
┌─────────────────────────────────────────────────────────────────────────┐
│                  TAHAP 2: PENCOCOKAN RELASI DATA
│               (Sequence-Pair Classification / Entailment)
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  INPUT: Pasangan Kalimat                                                │
│  Pesan Induk: "Kirim 5 kg kopi arabika ke Jl. Merdeka 45 Jakarta"     │
│  Pesan Lanjutan: "Tambah 3 kg kopi arabika ke alamat sebelumnya"      │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ① TOKENISASI PASANGAN: Memecah 2 kalimat → Gabung dengan [SEP]       │
│  [Token A] + [SEP] + [Token B]                                         │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ② EMBEDDING PASANGAN: Ubah 2 kalimat → Angka representasi             │
│  Ditambah Segment IDs untuk membedakan kalimat A vs B                   │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ③ TRANSFORMER (IndoBERT-P2): Pembelajaran hubungan antar kalimat     │
│  12 layers yang memahami apakah kedua pesan terkait/cocok               │
│  ★ Model: indobenchmark/indobert-base-p2                               │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ④ CLASSIFIER (Sequence-Pair Head): Prediksi kesesuaian                │
│  Apakah pesan lanjutan COCOK dengan pesan induk?                        │
│  Keputusan: Entailment (Cocok) vs Non-Entailment (Tidak Cocok)         │
└────────────────────────┬──────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT: Prediksi Kesesuaian + Confidence Score                         │
│  ✓ COCOK: 92.5% (sama produk, sama lokasi)                            │
│  ✗ TIDAK COCOK: 7.5%                                                   │
│                                                                          │
│  KEPUTUSAN BISNIS:                                                     │
│  → Jika Cocok > 80%: GABUNGKAN pesanan (merge ke order induk)         │
│  → Jika Cocok ≤ 80%: PISAHKAN sebagai pesanan baru                   │
└─────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
```

---

## 🎨 VERSI RINGKAS UNTUK DIAGRAM (6 KOTAK UTAMA)

### **TAHAP 1: NER (3 Kotak Inti + Input/Output)**

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ INPUT TEKS   │  →   │  TOKENISASI  │  →   │  EMBEDDING & │  →   │TRANSFORMER   │
│   MENTAH     │      │              │      │   PREP       │      │ (IndoBERT)   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                                                                           │
                                                                           ▼
                                                              ┌──────────────────────┐
                                                              │  NER CLASSIFIER      │
                                                              │  (8 Label Entities)  │
                                                              └──────────────┬───────┘
                                                                            │
                                                                            ▼
                                                              ┌──────────────────────┐
                                                              │  OUTPUT: Entitas     │
                                                              │  + Confidence Score  │
                                                              └──────────────────────┘
```

### **TAHAP 2: Sequence-Pair Classification (3 Kotak Inti + Input/Output)**

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ INPUT PAIR   │  →   │  TOKENISASI  │  →   │  EMBEDDING & │  →   │TRANSFORMER   │
│ (2 Kalimat)  │      │   PASANGAN   │      │  PASANGAN    │      │ (IndoBERT-P2)│
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
                                                                           │
                                                                           ▼
                                                              ┌──────────────────────┐
                                                              │ SEQUENCE CLASSIFIER  │
                                                              │ (Cocok/Tidak Cocok)  │
                                                              └──────────────┬───────┘
                                                                            │
                                                                            ▼
                                                              ┌──────────────────────┐
                                                              │  OUTPUT: Prediksi    │
                                                              │  + Confidence Score  │
                                                              └──────────────────────┘
```

---

## 📊 TABEL PERBANDINGAN KEDUA TAHAP

| Aspek | TAHAP 1: NER | TAHAP 2: Sequence-Pair |
|-------|--------------|------------------------|
| **Input** | 1 kalimat (pesan tunggal) | 2 kalimat (pasangan) |
| **Model** | indolem/indobert-base-uncased | indobenchmark/indobert-base-p2 |
| **Task** | Token Classification | Sequence-Pair Classification |
| **Output Label** | 8 label entitas (BIO) | 2 kelas (Cocok/Tidak Cocok) |
| **Tujuan** | Ekstraksi informasi terstruktur | Penentuan relasi/kesesuaian |
| **Contoh Output** | Produk, Qty, Lokasi, Instruksi | Entailment score: 92.5% |
| **Keputusan Bisnis** | Data untuk database | Merge vs split order |

---

## 🔧 PARAMETER PENTING (Tanpa Detail Teknis)

### Untuk TAHAP 1 (NER):
- **Tokenizer**: WordPiece (subset kata-kata)
- **Model Depth**: 12 transformer layers
- **Output**: 8 label kategori logistik
- **Confidence**: Probabilitas per token (0-100%)

### Untuk TAHAP 2 (Sequence-Pair):
- **Tokenizer**: WordPiece + Separator [SEP]
- **Model Depth**: 12 transformer layers
- **Output**: 2 class predictions (Cocok/Tidak Cocok)
- **Threshold Decision**: Biasanya >80% untuk merge order

---

## 💡 TEMPLATE TEXT UNTUK BAGAN VISIO

**Untuk setiap kotak di diagram Anda, gunakan text sesederhana ini:**

### TAHAP 1:
1. **Input**: "Pesan WhatsApp pelanggan (teks mentah)"
2. **Tokenisasi**: "Memecah kalimat → daftar token"
3. **Embedding**: "Token → angka representasi"
4. **Transformer**: "Model neural mempelajari konteks makna"
5. **Classifier**: "Prediksi label kategori logistik"
6. **Output**: "Entitas teridentifikasi + skor kepercayaan"

### TAHAP 2:
1. **Input**: "Dua pesan: pesanan induk + pesanan revisi"
2. **Tokenisasi**: "Memecah & gabung → token pasangan"
3. **Embedding**: "Pasangan token → angka representasi"
4. **Transformer**: "Model neural mempelajari hubungan antar pesan"
5. **Classifier**: "Prediksi: Cocok atau Tidak Cocok?"
6. **Output**: "Prediksi kesesuaian + skor kepercayaan"

---

## 🎯 CATATAN UNTUK SKRIPSI

### Bagian yang cocok untuk BAB METODOLOGI:

**KERANGKA PEMIKIRAN SISTEM:**
- Sistem terdiri dari **2 tahap pipeline** yang berurutan
- Tahap 1 fokus pada **ekstraksi informasi** (structured entity recognition)
- Tahap 2 fokus pada **pencocokan relasi** (semantic similarity)
- Kedua tahap menggunakan **model IndoBERT yang sudah pre-trained** dari Hugging Face
- Arsitektur mengikuti standar NLP modern (Transformer-based)

### Keunggulan Pendekatan:
1. **Modular**: Kedua tahap dapat dikembangkan/dievaluasi terpisah
2. **Transfer Learning**: Menggunakan model pre-trained, tidak training dari nol
3. **Interpretable**: Output setiap tahap jelas (entitas vs relasi)
4. **Scalable**: Mudah ditambah label atau kelas baru

---

## 📌 CATATAN FINAL

- **Jangan terlalu detail** di diagram: fokus pada **alur transformasi data** (Input → Output)
- **Highlight box penting**: Tokenisasi, Transformer, Classifier
- **Panah menunjukkan alur**: Data mengalir dari kiri ke kanan (atau atas ke bawah)
- **Warna saran**:
  - 🟦 Input: Biru (data mentah)
  - 🟩 Processing: Hijau (tahap transformasi)
  - 🟥 Output: Merah (hasil prediksi)
- **Font**: Sederhana agar mudah dibaca ketika di-print untuk skripsi

---

## ✅ FILE YANG SUDAH DISIAPKAN

Dua file detail sudah dibuat:
1. **TAHAP_1_NER_PIPELINE_VISUAL.md** → Detail ekstraksi informasi (6 kotak)
2. **TAHAP_2_SEQUENCE_PAIR_PIPELINE_VISUAL.md** → Detail pencocokan relasi (6 kotak)

Gunakan file-file ini sebagai referensi saat membuat diagram di Visio!

