# PROMPT GEMINI - MASALAH #2: Revision & Partial Data Refill Problem

**Untuk:** Generate gambaran masalah #2 (Semantic Ambiguity & Data Linking) di BAB 1.3 Identifikasi Masalah Skripsi

---

## PROMPT (Copy-Paste ke Gemini):

```
TASK: Generate deskripsi MASALAH #2 untuk BAB 1.3 skripsi, tentang 
Revision Management & Partial Data Refill Problem di PT. Rafay Logistik.

LANGUAGE: Bahasa Indonesia formal/akademis
LENGTH: 4-5 kalimat (1 paragraf pendek)
STYLE: Professional, konkrit, to-the-point

PROBLEM CONTEXT:
================

Dari raw WhatsApp data PT. Rafay Logistik, terjadi pattern: 
- Pesanan multi-unit (5 unit) posting awal dengan HANYA slot 1 lengkap
- Slot 2-5 KOSONG (hanya waktu & rute, tidak ada driver/plat/phone)
- Kemudian, pesan TERPISAH datang LATER dengan data tambahan:
  * "REVISI DRIVER: Umar Ali, Nopol B 9932 SXW"
  * "REVISI NOPOL BE 8610 DB"
  * "Rev: masih 18:00 CGK-SUB, ganti driver Budi"

PROBLEM YANG TERJADI:
1. Implicit Reference: Revisi mana untuk order mana? 
   - Dari 50+ orders sebelumnya, yang mana?
   - Hanya ada implicit hints: waktu loading, lokasi, rute
   - Multiple candidates possible: bisa match ke 3-5 orders berbeda

2. Ambiguous Matching: Tidak clear reference resolution
   - "REVISI NOPOL BE 8610 DB" → harus find order mana pake plat ini
   - Waktu: 18:00 ada di 20+ orders (CGK-SUB)
   - Lokasi: ARGOPANTES ada di 40+ orders
   - Rute: CGK-SUB ada di 30+ orders
   - Kombinasi match: masih 5-10 candidates!

3. Manual Tracking Error: Admin harus track dan match manually
   - Keep history di spreadsheet
   - Manual matching adalah error-prone
   - Saat volume naik → exponential complexity

4. Scalability: Tidak sustainable saat data naik
   - Current: manageable karena volume rendah
   - Future: 500+ orders = exponential ambiguity
   - Rule-based matching insufficient

DATA EXAMPLES dari raw:
```
[Original Message]:
6 UNIT WB/50 CBM
Lokasi : ARGOPANTES 
Waktu loading : 07:00 07-02-2026
Rute/tujuan : CGK - SUB
driver  : Chandra
Nopol  : L 8601 UH

[Revision Later]:
REVISI DRIVER
driver  : UMAR ALI
Nopol  : B 9932 SXW

---

[Another Example]:
10 UNIT CDDL/24 CBM
Lokasi : ARGOPANTES 
Waktu loading : SEGERA
Rute/tujuan : CGK - JATIM TENTATIF
[KEMUDIAN]: REVISI NOPOL BE 8610 DB

Admin question: Revisi ini untuk unit mana? Waktu loading mana?
```

WHAT THE DESCRIPTION SHOULD COVER:
1. Pattern: Original order → partial data → revision later
2. Problem: Ambiguous reference resolution (multiple candidates)
3. Implicit hints: hanya waktu, lokasi, rute → tidak sufficient
4. Manual effort: error-prone tracking & matching
5. Scalability: tidak sustainable saat data growth

KEYWORDS HARUS ADA:
✅ Multi-slot + Partial data
✅ Implicit revision references
✅ Ambiguous matching problem
✅ Multiple candidates
✅ Manual tracking error-prone
✅ Scalability unsustainable

TONE: Don't catastrophize, tapi jelas masalahnya REAL dan URGENT

OUTPUT FORMAT:
Generate 4-5 kalimat yang bisa langsung copy-paste ke BAB 1.3 skripsi.
Paragraph yang cohesive, academic tone, mudah dipahami.

START WRITING NOW: [ONLY OUTPUT THE 4-5 SENTENCE PARAGRAPH]
```

---

## EXPECTED OUTPUT DARI GEMINI:

Gemini akan menghasilkan sesuatu seperti:

> **"Masalah kedua yang lebih kompleks adalah resolusi referensi implisit dalam pesan revisi data: ketika data partial atau revisi menyusul via WhatsApp terpisah (misal 'REVISI NOPOL BE 8610 DB'), admin harus menentukan revisi ini untuk order/slot mana dari puluhan order sebelumnya. Hanya petunjuk implisit yang tersedia (waktu loading, lokasi, rute tujuan), namun kombinasi ini sering match ke 5-10 candidates berbeda, menyebabkan ambiguitas yang tidak dapat diselesaikan dengan rule-based matching. Upaya manual untuk tracking dan matching revisi menjadi error-prone dan cognitively intensive, terutama ketika volume pesanan meningkat. Skalabilitas sistem manual ini tidak sustainable untuk pertumbuhan data 50-80% per bulan, memerlukan solusi semantic matching berbasis machine learning untuk resolusi referensi otomatis."**

---

## LANGKAH PAKAI:

1. ✅ Copy seluruh PROMPT di atas
2. ✅ Paste ke Gemini (gemini.google.com)
3. ✅ Tunggu output (~2 menit)
4. ✅ Copy hasil Gemini
5. ✅ Paste ke BAB 1.3 Identifikasi Masalah #2
6. ✅ Done!

---

## TIPS REFINEMENT (Jika hasil Gemini kurang sempurna):

Jika perlu adjust, feedback ke Gemini:
- "Tambah 1 konkrit example dari data"
- "Simplify language, kurangi jargon"
- "Lebih emphasize multiple candidates ambiguity"
- "Mention why semantic matching needed"

---

## STRUKTUR BAB 1.3 FINAL (Dengan Masalah 1 + 2):

```markdown
### 1.3 Identifikasi Masalah Operasional PT. Rafay

#### Masalah #1: Data Entry Workload Escalation
[INSERT: Paragraph dari Gemini untuk Masalah 1]

#### Masalah #2: Semantic Ambiguity & Data Linkage Problem
[INSERT: Paragraph hasil Gemini SEKARANG untuk Masalah 2]
```

---

Ready? Copy prompt di atas langsung ke Gemini! 💪
