# Draft Kasar 4.3.2 Tahapan Pengembangan Model AI

Dokumen ini hanya membahas **tahap pengembangan model AI**, bukan alur aplikasi, rekonsiliasi, pengujian sistem, antarmuka, database, atau runtime proof. Fokusnya adalah bagaimana dua model IndoBERT dikembangkan sampai menjadi artefak `final_model`.

Model yang dikembangkan:

1. **IndoBERT NER** untuk ekstraksi entitas operasional.
2. **IndoBERT Sequence Pair Classification** untuk pencocokan pesanan induk dan pesanan susulan.

---

## 1. Penentuan Kebutuhan Model

**Isi singkat:**

Jelaskan bahwa masalah utama pada penelitian adalah teks WhatsApp operasional yang tidak terstruktur. Karena kebutuhan sistem terbagi menjadi dua, maka dikembangkan dua model dengan tugas berbeda.

**Yang perlu ditulis:**

- Model pertama dibutuhkan untuk membaca atribut dari teks.
- Model kedua dibutuhkan untuk menilai kecocokan dua pesan/order.
- Pemisahan dua model dilakukan agar masing-masing model fokus pada tugas yang spesifik.

**Bukti project:**

- `models/indobert_NER/final_model/config.json`
- `models/indobenchmark/indobert-base-p2_15k/final_model/config.json`

---

## 2. Penyusunan Data Latih

**Isi singkat:**

Jelaskan bahwa data latih disusun dari pola teks order operasional. Data dipisahkan menjadi dua jenis dataset sesuai tugas model: dataset NER dan dataset Sequence Pair Classification.

**Yang perlu ditulis:**

- Dataset NER digunakan untuk melatih model mengenali entitas.
- Dataset SPC digunakan untuk melatih model mengenali hubungan cocok/tidak cocok antar dua teks.
- Data dibuat dari variasi format, typo, pesanan awal, pesanan susulan, dan anomali lapangan.

**Bukti project:**

- `data/chat/processed/NER/data_siap_training_CLEAN.json`
- `data/chat/processed/SPC/stage2_completion_matcher_dataset.json`

**Angka yang tersedia:**

- Dataset NER: 1000 data.
- Dataset SPC stage 2: 15000 pasangan data.

---

## 3. Format Dataset NER

**Isi singkat:**

Jelaskan bahwa dataset NER disusun dalam bentuk token dan label. Setiap token diberi label entitas sesuai atribut order.

**Yang perlu ditulis:**

- Format data berisi `tokens`, `ner_tags`, dan `original_text`.
- Model belajar memberi label pada setiap token.
- Label menggunakan pola entitas seperti `B-DRIVER`, `I-DRIVER`, dan `O`.

**Entitas yang dikembangkan:**

- `RO_DATE`
- `LOAD_DATE`
- `TIME`
- `ORIGIN`
- `DESTINATION`
- `UNIT_QTY`
- `UNIT_TYPE`
- `DRIVER`
- `PLATE`
- `PHONE`

**Bukti project:**

- `data/chat/processed/NER/data_siap_training_CLEAN.json`
- `models/indobert_NER/final_model/config.json`

---

## 4. Format Dataset Sequence Pair Classification

**Isi singkat:**

Jelaskan bahwa dataset model kedua dibuat dalam bentuk pasangan teks. Satu data terdiri dari teks pertama, teks kedua, dan label kecocokan.

**Yang perlu ditulis:**

- `text_a` mewakili pesanan induk atau state order.
- `text_b` mewakili pesanan susulan.
- Label model adalah `MATCH` dan `NO_MATCH`.
- Dataset dibuat agar model belajar membedakan pasangan yang benar-benar cocok dan pasangan yang mirip tetapi salah.

**Struktur dataset yang tersedia:**

- `pair_id`
- `text_a`
- `text_b`
- `label`
- `pair_kind`
- `unit_action`
- `source_id`

**Bukti project:**

- `data/chat/processed/SPC/stage2_completion_matcher_dataset.json`

---

## 5. Pra-Pemrosesan Data Latih

**Isi singkat:**

Jelaskan bahwa sebelum training, teks perlu dibuat lebih konsisten agar model dapat belajar dari pola yang lebih stabil.

**Yang perlu ditulis:**

- Membersihkan metadata WhatsApp.
- Mengurangi noise percakapan.
- Menyamakan variasi label field.
- Menjaga makna utama teks agar tidak berubah.

**Contoh normalisasi:**

```text
DRVER -> Driver
Nopoll -> Nopol
No hpp -> No hp
Waktu lodng -> Waktu loading
```

**Bukti project:**

- `src/data_processing/cleaner.py`
- `stage2_pair_visual_test.py`
- Fungsi terkait:
  - `prepare_text_for_ner()`
  - `normalize_ner_field_labels()`
  - `remove_ner_operational_noise()`

---

## 6. Pemilihan Base Model NER

**Isi singkat:**

Jelaskan bahwa model NER menggunakan IndoBERT varian `indolem/indobert-base-uncased`.

**Yang perlu ditulis:**

- Model ini digunakan untuk tugas token classification.
- Varian uncased membantu menghadapi variasi huruf besar/kecil pada chat operasional.
- Arsitektur akhir model adalah `BertForTokenClassification`.

**Bukti project:**

- `models/indobert_NER/final_model/config.json`

**Potongan bukti penting:**

```json
"_name_or_path": "indolem/indobert-base-uncased",
"architectures": ["BertForTokenClassification"]
```

---

## 7. Fine-tuning Model NER

**Isi singkat:**

Jelaskan bahwa fine-tuning dilakukan agar IndoBERT dapat mengenali entitas khusus pada domain logistik.

**Yang perlu ditulis:**

- Input model berupa token.
- Output model berupa label entitas per token.
- Model dilatih untuk mengenali atribut operasional, bukan untuk menghasilkan tabel final.
- Hasil training disimpan ke folder final model.

**Bukti project:**

- `models/indobert_NER/checkpoint-500/trainer_state.json`
- `models/indobert_NER/final_model/`

**Metrik training yang tersedia untuk dicantumkan bila diperlukan:**

- `eval_accuracy`: 0.9980
- `eval_f1`: 0.9964
- `eval_precision`: 0.9945
- `eval_recall`: 0.9983

Catatan: angka ini cukup dicantumkan sebagai ringkasan training, bukan dibahas panjang jika subbab ini hanya fokus pengembangan.

---

## 8. Pemilihan Base Model Sequence Pair Classification

**Isi singkat:**

Jelaskan bahwa model pencocokan menggunakan IndoBERT varian `indobenchmark/indobert-base-p2`.

**Yang perlu ditulis:**

- Model ini digunakan untuk tugas sequence classification.
- Input model berupa pasangan teks.
- Output model berupa label kecocokan.
- Model cocok untuk mempelajari hubungan semantik antara pesanan induk dan susulan.

**Bukti project:**

- `models/indobenchmark/indobert-base-p2_15k/final_model/config.json`

**Potongan bukti penting:**

```json
"architectures": ["BertForSequenceClassification"],
"problem_type": "single_label_classification",
"id2label": {
  "0": "NO_MATCH",
  "1": "MATCH"
}
```

---

## 9. Fine-tuning Model Sequence Pair Classification

**Isi singkat:**

Jelaskan bahwa fine-tuning dilakukan agar model dapat membedakan pasangan pesanan yang cocok dan tidak cocok.

**Yang perlu ditulis:**

- Model menerima dua teks sebagai input.
- Model menghasilkan probabilitas untuk `MATCH` dan `NO_MATCH`.
- Dataset dibuat agar model tidak hanya melihat kemiripan kata, tetapi juga konteks pesanan.
- Model dilatih pada pasangan data yang mencakup kasus cocok, beda tanggal, beda rute, beda lokasi, beda tipe, duplikat, dan slot penuh.

**Bukti project:**

- `models/indobenchmark/indobert-base-p2_15k/checkpoint-7500/trainer_state.json`
- `models/indobenchmark/indobert-base-p2_15k/final_model/`

**Metrik training yang tersedia untuk dicantumkan bila diperlukan:**

- `eval_accuracy`: 0.9123
- `eval_f1_macro`: 0.9123
- `eval_f1_match`: 0.9140
- `eval_precision_match`: 0.8972
- `eval_recall_match`: 0.9313

Catatan: metrik ini hanya ringkasan hasil fine-tuning. Pembahasan evaluasi detail sebaiknya diletakkan pada subbab evaluasi, bukan di sini.

---

## 10. Penyimpanan Artefak Model

**Isi singkat:**

Jelaskan bahwa setelah proses fine-tuning, model disimpan sebagai artefak final agar dapat digunakan kembali oleh sistem.

**Yang perlu ditulis:**

- Artefak final berisi konfigurasi model, tokenizer, vocabulary, dan bobot model.
- Folder final model menjadi sumber utama saat aplikasi melakukan inferensi.
- Pemisahan folder NER dan SPC menunjukkan bahwa keduanya merupakan model berbeda dengan tugas berbeda.

**Bukti project:**

- `models/indobert_NER/final_model/`
- `models/indobenchmark/indobert-base-p2_15k/final_model/`

**File bukti umum:**

- `config.json`
- `tokenizer.json`
- `vocab.txt`
- `special_tokens_map.json`
- file bobot model, seperti `model.safetensors` atau `pytorch_model.bin`

---

## 11. Ringkasan Tahapan Pengembangan

**Isi singkat:**

Bagian ini merangkum bahwa pengembangan model dilakukan secara bertahap dari data mentah, dataset, fine-tuning, sampai penyimpanan artefak model.

**Ringkasan yang dapat ditulis:**

```text
Data operasional dikumpulkan dan disusun menjadi dua dataset.
Dataset pertama digunakan untuk melatih model NER.
Dataset kedua digunakan untuk melatih model Sequence Pair Classification.
Model NER dikembangkan dari indolem/indobert-base-uncased.
Model SPC dikembangkan dari indobenchmark/indobert-base-p2.
Kedua model hasil fine-tuning disimpan sebagai final_model untuk digunakan pada sistem.
```

---

## Susunan Subbab yang Disarankan

Gunakan urutan ini agar pembahasan tetap fokus pada pengembangan model:

1. Penentuan kebutuhan model.
2. Penyusunan data latih.
3. Format dataset NER.
4. Format dataset SPC.
5. Pra-pemrosesan data latih.
6. Pemilihan base model NER.
7. Fine-tuning model NER.
8. Pemilihan base model SPC.
9. Fine-tuning model SPC.
10. Penyimpanan artefak model.
11. Ringkasan tahapan pengembangan.

---

## Draft Narasi Pembuka

Tahapan pengembangan model AI pada penelitian ini dilakukan dengan membagi permasalahan menjadi dua tugas pembelajaran mesin. Tugas pertama adalah ekstraksi entitas dari teks operasional menggunakan model IndoBERT NER, sedangkan tugas kedua adalah pencocokan pesanan induk dan pesanan susulan menggunakan model IndoBERT Sequence Pair Classification. Pemisahan tugas ini dilakukan agar setiap model memiliki fokus pembelajaran yang jelas sesuai kebutuhan sistem.

---

## Draft Narasi Penutup

Berdasarkan tahapan tersebut, pengembangan model AI pada penelitian ini terdiri dari penyusunan dataset, pra-pemrosesan data latih, pemilihan base model, fine-tuning, dan penyimpanan artefak model. Model NER dikembangkan untuk mengenali atribut operasional pada level token, sedangkan model Sequence Pair Classification dikembangkan untuk mempelajari hubungan kecocokan antara dua teks pesanan. Kedua artefak model kemudian disimpan secara terpisah sebagai model final sesuai perannya masing-masing.
