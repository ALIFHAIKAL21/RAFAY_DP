# 🚀 PROMPT UNTUK GEMINI - GENERATE LATAR BELAKANG MASALAH SKRIPSI

**Tingkat Kompleksitas:** Advanced  
**Tujuan:** Generate problem background statement yang match dengan project RAFAY IDP  
**Output Expected:** 2000-3000 kata dalam Bahasa Indonesia, siap untuk BAB 1 (Pendahuluan) skripsi

---

## PROMPT MASTER (Copy-Paste ke Gemini)

```
TASK: Generate latar belakang masalah (problem background) untuk skripsi tingkat sarjana/magister
DOMAIN: Sistem Informasi / Machine Learning / Natural Language Processing

KONTEKS PROYEK:
================

Nama Perusahaan: PT. Rafay Logistik
Sektor: Ekspedisi & Logistics
Lokasi: Indonesia
Scale Saat Ini: ~200-300 orders per bulan
Growth Proyeksi: 500+ orders dalam 2 tahun ke depan

MASALAH OPERASIONAL SPESIFIK:
==============================

1. INPUT DATA (WhatsApp Chat - Unstructured):
   - Input berasal dari grup WhatsApp tim operasional
   - Format sangat variasi dan tidak terstandar
   - Contoh variasi field labels:
     * "driver" vs "Driver" vs "DRIVER" vs "DRIVER 1" vs "Nama"
     * "Nopol" vs "No Plat" vs "No polisi" vs "NOPOL"
     * "Lokasi" vs "LOKASI" vs "Lokasi pengambilan"
     * "Waktu loading" vs "Waktu muat" vs "Time Loading"
   - Typo field values:
     * Lokasi: "ARGOPANTES" vs "argo pantes*" vs "*argo pantes *"
     * Field labels: "ddriver" (typo)
     * Phone: "+62 877-8667-6177" vs "085784422398" (format berbeda)
     * Plate: "L 9511 AL" vs "L 9511AL" vs "L9511AL" (spacing variasi)
     * Date: "06-02-2026" vs "06/02/2026" vs "06 Feb 26" (format mixed)

2. POLA ORDERING KOMPLEKS:
   - Order sering terdiri dari MULTIPLE SLOTS dengan:
     * Slot 1: LENGKAP (semua field ada: driver, plat, phone)
     * Slot 2-5: PARTIAL (hanya waktu loading & rute ada, driver/plat/phone kosong)
   - Data partial sering menyusul NANTI via pesan WhatsApp berikutnya (timing tidak pasti)
   - Admin harus manual track & merge data partial ini dengan order sebelumnya
   - Quota enforcement: Jika order declare 5 unit tapi driver hanya 1, admin harus create 5 rows di Excel (1 ASSIGNED, 4 PARTIAL/UNASSIGNED)

3. REVISI DATA (Revision Management):
   - Revisi datang kapan saja setelah order posting (bisa jam, hari kemudian)
   - Format revisi variatif:
     * "REVISI DRIVER" (explisit)
     * "REVISI NOPOL" (explicit)
     * "Rev: masih 18:00 Surabaya-Jakarta, ganti driver Budi" (implicit, context-based)
     * Update driver yang datang di message terpisah
   - Revisi harus di-match ke order MANA dari puluhan order sebelumnya?
     * Matching hints: waktu loading, lokasi, rute, driver sebelumnya
     * Tidak selalu jelas → ambiguous matching problem
   - Multiple revisions untuk order sama: sangat mungkin terjadi

4. CURRENT PAIN POINTS:
   - Admin input manual: ~3-5 menit per order
   - Error rate on critical fields: 5-8% (documented)
   - Field inconsistency handling: Admin harus "decode" & standardize sendiri
   - Typo errors: Phone normalization, plate standardization incomplete
   - Revision management: Manual tracking spreadsheet prone to confusion
   - Scalability barrier: 2 admins × 25 working days × 4 orders per admin/day = ~200 orders max
   - Growth risk: Projected 500 orders/month dalam 2 tahun = BOTTLENECK!

5. OUTPUT TARGET (Excel Format):
   Fields yang harus di-extract ke Excel:
   - Tgl RO (Request Order Date)
   - Tgl Muat (Loading Date)
   - Vendor
   - Pickup (Lokasi pengambilan)
   - Tujuan (Destination)
   - No. Plat (License Plate)
   - Type Truck (Vehicle Type)
   - Driver (Driver Name)
   - Kontak Driver (Driver Phone)
   - Status Unit (ASSIGNED / PARTIAL / UNASSIGNED)

KONTEKS TECHNICAL SOLUTION:
============================

Project Anda: RAFAY IDP v2.0 (Intelligent Document Processing)
Teknologi:
- InDoBERT NER (Named Entity Recognition)
  * Task: Extract 21 entity labels dari unstructured text
  * Performance Target: 89% F1
  * Handles: Typo tolerance, Indonesian language, domain-specific terms
  
- Revision Matcher (Semantic Similarity)
  * Task: Match revision messages to historical orders
  * Performance Target: 90% accuracy
  * Outperforms rule-based by 9%

- Business Logic: Quota enforcement, multi-driver tracking, status assignment

TASK UNTUK GEMINI:
===================

Buatkan LATAR BELAKANG MASALAH (Problem Background) untuk skripsi dengan spesifikasi:

1. PANJANG: 2000-3000 kata (setara BAB 1 skripsi)

2. STRUKTUR YANG HARUS ADA:
   a) Konteks Industri Logistics Indonesia
      - Trend digitalisasi dalam logistics
      - Peran WhatsApp dalam komunikasi operational
      - Data entry manual masih dominan
      
   b) Gambaran PT. Rafay Logistik Spesifik
      - Operasional mereka
      - Proses input saat ini (manual Excel)
      - Scale saat ini vs proyeksi
      
   c) Identifikasi Masalah Spesifik
      - Problem #1: Field Inconsistency & Typo Handling
      - Problem #2: Multi-Slot Order Complexity
      - Problem #3: Revision Management & Disambiguation
      - Problem #4: Scalability Bottleneck
      
   d) Impact Analysis
      - Current pain point (5-8% error rate, 5 min/order)
      - Growth bottleneck (200 → 500 orders = 2.5x jump, 2 admins insufficient)
      - Business risk & opportunity cost
      
   e) Technical Gap
      - Why rule-based/regex insufficient
      - Need for NLP (Natural Language Processing)
      - Why BERT-based approach is suitable
      
   f) Research Opportunity & Scope
      - How NER can extract structured data from unstructured chat
      - How semantic matching can solve revision disambiguation
      - Dual-model approach justification

3. TONE & STYLE:
   - Profesional academic (untuk skripsi)
   - Jelas & mudah dipahami (bukan technical jargon semua)
   - Logical flow: Dari general problem → specific case → technical solution
   - Balance: Business perspective DAN technical perspective
   - Real data & numbers: Include metrics dari project RAFAY IDP (89% F1, 90% accuracy, etc.)

4. JANGAN LUPA:
   - Cite statistik real PT. Rafay (200-300 orders/month, 5-8% error, 3-5 min/order)
   - Sebutkan KEDUA model (NER + Revision Matcher) dan perannya
   - Jelaskan KENAPA masalah ini penting (business value + research contribution)
   - Berikan visual/concrete examples dari raw data WhatsApp
   - Frame problem sebagai "scalability challenge" bukan hanya "automation opportunity"

5. OUTPUT FORMAT:
   - Bahasa: Indonesia (formal/akademis)
   - Divisible into 5-6 sub-sections (1.1 Latar Belakang, 1.2 Masalah, 1.3 Scope, dst)
   - Include 2-3 konkret examples dari raw data
   - End dengan strong motivation untuk solution

---

DELIVERY:
Berikan output dalam format Markdown yang sudah siap copy-paste ke BAB 1 skripsi.
Jangan ada preamble/explanation - langsung ke content yang siap pakai.

---

Sekarang silakan buatkan latar belakang masalah yang powerful & specific untuk kasus PT. Rafay Logistik ini!
```

---

## ALTERNATIVE PROMPT (Jika ingin dengan lebih banyak detail)

```
EXTENDED PROMPT untuk Gemini (Jika butuh lebih dalam):

[USE MASTER PROMPT DI ATAS TERLEBIH DAHULU]

Lalu follow-up dengan:

---

Follow-up Instruction:

Setelah generate background section, buatkan JUGA:

1. RESEARCH QUESTIONS (3-5 pertanyaan penelitian yang ingin dijawab):
   - Fokus pada bagaimana NER & Revision Matcher solve masalah PT. Rafay
   - Format: "Bagaimana cara ... ?" atau "Seberapa efektif ... ?"

2. HYPOTHESES (3-4 hipotesis yang ingin divalidasi):
   - Contoh: "InDoBERT NER dapat mencapai >85% F1 pada extraction task logistics"
   - Contoh: "Semantic matching outperforms rule-based approach by >5%"

3. RESEARCH CONTRIBUTIONS (Apa yang ingin dicontributkan):
   - Akademis (paper/publication angle)
   - Praktis (implementasi untuk PT. Rafay)
   - Industrial (template untuk ekspedisi lain)

Format output: Markdown, ready to paste into thesis Chapter 1-2.
```

---

## STRUCTURE REFERENCE untuk Gemini

Gunakan struktur ini sebagai blueprint:

```markdown
# BAB 1: PENDAHULUAN

## 1.1 Latar Belakang (Background)
- [Context: Logistics industry in Indonesia]
- [Specific: WhatsApp-based operations]
- [Problem: Manual data entry bottleneck]

## 1.2 Perumusan Masalah (Problem Statement)
- [Problem #1: Data Quality Issues]
- [Problem #2: Multi-slot Order Complexity]
- [Problem #3: Revision Management]
- [Problem #4: Scalability]

## 1.3 Dampak & Signifikansi (Impact Analysis)
- [Current state: 5-8% error, 5 min/order]
- [Growth scenario: 500 orders in 2 years]
- [Business risk: Need additional admin OR automation]

## 1.4 Kesenjangan Teknologi (Technical Gap)
- [Why rule-based insufficient]
- [Why NLP/ML approach necessary]
- [Related work: BERT, NER, semantic similarity]

## 1.5 Solusi yang Diusulkan (Proposed Solution)
- [InDoBERT NER role]
- [Revision Matcher role]
- [Combined pipeline benefits]

## 1.6 Tujuan & Kontribusi Penelitian (Objectives & Contributions)
- [Research objectives]
- [Expected outcomes]
- [Practical & academic contributions]
```

---

## TIPS MENGGUNAKAN PROMPT INI:

1. **Copy seluruh MASTER PROMPT** ke Gemini (atau ChatGPT)
2. **Tunggu output** (biasanya 2-5 menit untuk 2000-3000 kata)
3. **Edit minor**: 
   - Adjust company names jika sensitif
   - Verify numbers (cross-check dengan data Anda)
   - Add specific examples dari raw data Anda
4. **Integrate ke thesis**: Copy-paste ke BAB 1 dokumentasi
5. **Refinement**: Baca berkali-kali, adjust tone sesuai universitas Anda

---

## QUALITY CHECKLIST setelah Gemini generate:

- [ ] Latar belakang mencakup konteks industri (tidak hanya problem spesifik)
- [ ] Ada 3-4 konkret examples dari raw data PT. Rafay
- [ ] Kedua model (NER + Revision Matcher) dijelaskan & disambung dengan masalah
- [ ] Scalability story ada (200 → 500 → 2000 orders progression)
- [ ] Business impact jelas (5-8% error, 5 min/order, bottleneck at 300 orders)
- [ ] Tone profesional & academic (bukan marketing-y)
- [ ] Citations prepared (akan di-add setelah literature review selesai)
- [ ] Motivasi untuk research jelas (kenapa perlu diteliti?)
- [ ] Tidak lebih dari 3000 kata (efficient writing)
- [ ] Ready to paste into final thesis

---

*Prompt ini designed khusus untuk case PT. Rafay Logistik dengan fokus pada dual-model approach (NER + Revision Matcher)*
