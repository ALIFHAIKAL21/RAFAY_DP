# 📝 PROMPT GEMINI - LATAR BELAKANG MASALAH (2 PARAGRAF AKHIR - PENDEKATAN SOLUSI)

**Status:** Ready to copy-paste ke Gemini  
**Output Expected:** 2 paragraf akhir (±1200-1800 words)  
**Language:** Bahasa Indonesia formal/akademis  
**Purpose:** Generate 2 paragraf terakhir dari BAB 1.2 Latar Belakang Masalah yang menjelaskan pendekatan solusi dengan detail model

---

## 📌 INPUT DARI LATAR BELAKANG YANG SUDAH ADA (3 PARAGRAF):

```
Seiring pesatnya perkembangan industri logistik, efisiensi pengelolaan informasi 
menjadi kunci utama dalam menjaga kelancaran rantai pasok dan daya saing perusahaan. 
PT. Rafay Logistik, sebagai entitas yang bergerak dalam jasa transportasi, memanfaatkan 
platform komunikasi digital seperti WhatsApp untuk memfasilitasi koordinasi pesanan 
secara real-time. Namun, penggunaan pesan teks tidak terstruktur ini membawa tantangan 
tersendiri dalam proses dokumentasi dan administrasi internal. Ketergantungan pada 
komunikasi manual yang intensif mulai menunjukkan celah kerentanan seiring dengan 
meningkatnya kompleksitas transaksi operasional, yang menuntut akurasi data tinggi 
di tengah volume pekerjaan yang terus bertambah secara signifikan.

Masalah utama operasional berakar pada karakteristik pesanan multi-unit yang memicu 
lonjakan beban entri data eksponensial dalam proses pemindahan informasi dari WhatsApp 
ke Excel. Dalam praktiknya, satu pesan mentah sering kali memuat instruksi untuk beberapa 
unit armada sekaligus; sebagai contoh, satu pesanan berisi lima unit akan menghasilkan 
lima baris data terpisah di Excel yang masing-masing membutuhkan pengisian sepuluh field 
informasi. Hal ini berarti admin harus mengekstraksi dan memvalidasi hingga 50 entri data 
dari satu pesan tunggal secara manual. Saat ini, dua staf admin mengelola ratusan hingga 
ribuan entri setiap bulan, di mana proses konversi satu pesan pesanan multi-unit tersebut 
membutuhkan waktu rata-rata tercepat sekitar 3 hingga 5 menit agar seluruh data terinput 
dengan akurat. Berdasarkan konfirmasi dari pemilik perusahaan terkait rencana ekspansi 
kerja sama bisnis di masa mendatang, peningkatan volume pesanan dipastikan akan segera 
melampaui ambang batas kapasitas operasional manusia. Kondisi unsustainable scalability 
ini berisiko memicu kelelahan kognitif (cognitive load) yang dapat melumpuhkan akurasi 
operasional serta menghambat proses pengambilan keputusan manajerial.

Kondisi operasional perusahaan kian kompleks akibat karakteristik aliran data yang 
bersifat dinamis, parsial, dan asinkron, khususnya dalam pengelolaan pesanan yang 
informasinya dikirimkan secara bertahap. Dalam praktiknya, instruksi pelengkapan data 
susulan (refill) maupun revisi krusial seperti perubahan identitas pengemudi atau nomor 
kendaraan sering kali diterima melalui pesan singkat tanpa disertai rujukan identitas 
pesanan induk yang eksplisit. Fenomena data yang terfragmentasi ini memaksa staf admin 
untuk melakukan penelusuran riwayat obrolan secara manual guna mencocokkan konteks 
informasi di antara puluhan pesanan aktif dengan rute yang serupa. Ketidakteraturan 
proses pelacakan ini tidak hanya memakan waktu operasional, tetapi juga sangat rentan 
memicu kesalahan penempatan informasi (merge conflicts). Hal tersebut sekaligus menyingkap 
kelemahan mendasar sistem pencatatan konvensional dalam menangani ambiguitas relasi data, 
yang diprediksi akan menjadi hambatan besar dalam menghadapi lonjakan volume data di 
masa mendatang.
```

---

## 🎯 PROMPT MASTER (COPY-PASTE KE GEMINI):

```
TASK: Generate 2 PARAGRAF AKHIR LATAR BELAKANG MASALAH untuk BAB 1.2 skripsi 
RAFAY IDP V2.0 yang menghubungkan MASALAH OPERASIONAL → SOLUSI PENDEKATAN ML → 
DETAIL MODEL TEKNIS yang digunakan.

OUTPUT: Exactly 2 paragraf (bukan bullet points, text paragraf penuh)
LENGTH: ~600-900 kata per-paragraf (total 1200-1800 kata)
LANGUAGE: Bahasa Indonesia formal/akademis
STYLE: Profesional, naratif, technical-yet-accessible

POSITIONING:
- Paragraf 1: Bridge dari masalah → Motivasi penggunaan ML + hybrid approach
- Paragraf 2: Detail teknis model yang digunakan (nama, arsitektur, spesifikasi)
- Both paragraphs smoothly transition ke BAB 2 (Literature Review)

========================================================================

KONTEKS MASALAH (SUDAH DIJELASKAN DI 3 PARAGRAF SEBELUMNYA):

Masalah #1: Data Entry Workload Escalation
- Pesanan multi-unit: 5 unit × 10 field = 50 entries per pesan
- 2 admin ~ 200-300 orders/month = 10,000-15,000 entries/month
- Processing: 3-5 menit per order manual
- Problem: Volume akan exceed kapasitas 2 admin dalam 3-6 bulan
- Root cause: UNSTRUCTURED TEXT → STRUCTURED EXTRACTION belum otomatis

Masalah #2: Semantic Ambiguity & Partial Data
- Pesanan multi-slot: Slot 1 komplit, Slot 2-5 partial (empty driver, plat)
- Revisi/refill: "REVISI DRIVER: Umar Ali, B 9932 SXW" tanpa eksplisit order reference
- Problem: Admin harus manual matching 5-10 kandidat orders
- Root cause: IMPLICIT REFERENCES + PARTIAL DATA → requires semantic understanding
- Not solvable dengan rule-based (terlalu banyak ambiguity)

========================================================================

SOLUSI YANG DIUSULKAN: HYBRID ML + RULE-BASED APPROACH

Pendekatan:
Kombinasi 2 machine learning models (InDoBERT-based) + rule-based post-processing:

1. MODEL NER (Named Entity Recognition) → Solve Masalah #1
   - Ekstraksi 21 entity types dari unstructured WhatsApp message
   - Output: 10-12 structured fields per unit order
   - Mengurangi manual extraction work dari 3-5 min → < 1 min

2. MODEL REVISION MATCHER (Semantic Similarity) → Solve Masalah #2
   - Matching incoming revision dengan candidate orders
   - Binary classification: MATCH or NO_MATCH
   - Mengurangi manual ambiguity resolution dari 5-10 candidates → top-3 recommended

3. RULE-BASED REFINEMENT LAYER
   - Post-processing untuk standardize format
   - Phone validation (Indonesian format)
   - Location fuzzy matching (typo tolerance)
   - Date/time parsing (multiple format support)
   - Rule-based boosts ML accuracy dari 82% → 91%+

========================================================================

PARAGRAF 1: BRIDGE DARI MASALAH KE SOLUSI (Motivasi Pendekatan)
===============================================================

THEME: "Why ML + why hybrid, not pure rule-based"

STRUCTURE:
1. Problem restatement (looping kembali ke 2 masalah)
2. Why rule-based alone insufficient
3. Why pure ML alone insufficient + Why hybrid necessary
4. Positioning of proposed approach

KEY POINTS PARA MASUKKAN:

1. PROBLEM RESTATEMENT:
   - Masalah #1: Ekstraksi 50+ entries dari 1 pesan unstructured
     Tidak feasible dengan rule-based selama format label inconsistent (15+ variations)
   - Masalah #2: Semantic ambiguity matching
     Tidak feasible dengan rule-based, requires understanding context & similarity

2. WHY RULE-BASED INSUFFICIENT:
   - Format label variations: 15+ ways to write "DRIVER:" (Sopir:, PENGEMUDI:, dst)
   - Typo overload: Lokasi typo (ARGPNTES vs ARGOPANTES), Phone prefix variations
   - No semantic understanding: Cannot match "REVISI DRIVER: Umar" ke order dengan context
   - Cannot handle implicit references: REVISION tanpa parent order ID eksplisit

3. WHY PURE ML INSUFFICIENT:
   - Data real Rafay: Noisy, label inconsistent, partial entries
   - Accuracy ceiling pure ML: ~82% (false positives 15-20%)
   - Small training dataset (200-300 orders)
   - Need domain-specific refinement

4. WHY HYBRID NECESSARY:
   - ML untuk pattern recognition & semantic understanding
   - Rule-based untuk domain-specific standardization & validation
   - Combined: 91%+ accuracy vs 82% pure ML
   - Better for logistics domain: Safety-critical decisions need confidence

5. APPROACH POSITIONING:
   - Hybrid approach: "Optimal integration antara ML + domain logic"
   - Enable: Reduce manual work 3-5 min → < 1 min per order
   - Future-proof: Can scale ke 500+ orders/month dengan human validation
   - Practical engineering: Proven approach untuk domain-specific extraction

FLOW & CONNECTORS:
- "Menghadapi tantangan ganda ini..."
- "Pendekatan rule-based murni..."
- "Namun, pendekatan machine learning tanpa polesan domain-specific..."
- "Oleh karenanya, penelitian ini mengusulkan..."
- "Dengan integrasi strategis antara..."

========================================================================

PARAGRAF 2: DETAIL MODEL TEKNIS (Architecture & Specifications)
================================================================

THEME: "Model details dengan technical precision"

STRUCTURE:
1. Architecture overview (3 model structure)
2. Model #1: NER (IndoBERT Token Classification) - detail lengkap
3. Model #2: Revision Matcher (Binary Classifier) - detail lengkap
4. Rule-based layer integration
5. Transition ke BAB 2

KEY POINTS PARA MASUKKAN:

1. ARCHITECTURE OVERVIEW:
   - Sistem menggunakan 2 fine-tuned InDoBERT models + rule-based layer
   - Pipeline: NER → Event Classification (optional) → Revision Matching
   - Framework: PyTorch + Transformers library (HuggingFace)

2. MODEL #1 - NER (ENTITY RECOGNITION):
   **Nama Lengkap Model:**
   - Model: `indobert_NER/final_model` (stored in models directory)
   - Base Model: `indolem/indobert-base-uncased`
   - Type: Token Classification (Named Entity Recognition) 
   - Purpose: Extract 21 entity types dari unstructured WhatsApp text

   **Task & Architecture:**
   - Predicts BIO tags (Begin-Inside-Outside) untuk setiap token
   - Reconstructs words dari subword pieces (misal: "Surabaya" → "Sur", "##aba", "##ya")
   - Hidden size: 768, Attention heads: 12, Layers: 12
   - Vocab size: 50,000 (Indonesian-specific)
   - Max sequence length: 128 tokens

   **21 Entity Labels (BIO Scheme):**
   - Date fields: B-DATE, I-DATE
   - Location: B-ORIGIN, I-ORIGIN, B-DESTINATION, I-DESTINATION
   - Time: B-TIME, I-TIME
   - Vehicle: B-PLATE, I-PLATE, B-UNIT_TYPE, I-UNIT_TYPE, B-UNIT_QTY, I-UNIT_QTY
   - Driver: B-DRIVER, I-DRIVER
   - Contact: B-PHONE, I-PHONE
   - Other: B-REASON, I-REASON, O (Outside)

   **Training Configuration:**
   - Dataset: ~200-300 orders (2 months Feb-Mar 2026)
   - Data split: 80% train / 20% test (stratified)
   - Batch size: 8
   - Epochs: 5
   - Learning rate: 2e-5 (AdamW optimizer)
   - Mixed precision: fp16 if GPU available
   - Best model selection: F1 score (seqeval metric)

   **Output Format:**
   ```
   {
       "UNIT_QTY": "5",
       "UNIT_TYPE": "TWB",
       "ORIGIN": "ARGOPANTES",
       "DESTINATION": "CGK, SUB",
       "DRIVER": "M. Ibnu",
       "PLATE": "L 9511 AL",
       "PHONE": "082191633212",
       "TIME": "18:00",
       "DATE": "06/02/2026"
   }
   ```

3. MODEL #2 - REVISION MATCHER (SEMANTIC SIMILARITY):
   **Nama Lengkap Model:**
   - Model: `indobert_revision_matcher/final_model`
   - Base Model: `indobenchmark/indobert-base-p2`
   - Type: Sequence-Pair Classification (Binary classifier with siamese topology)
   - Purpose: Match incoming revision/refill messages dengan candidate orders

   **Task & Architecture:**
   - Processes TWO input sentences simultaneously (text_a, text_b)
   - BERT concatenates inputs with [SEP] token separator
   - Predicts: MATCH (1) or NO_MATCH (0)
   - Hidden size: 768, Attention heads: 12, Layers: 12
   - Max sequence length: 256 tokens (for concatenated pair)

   **Binary Classification Labels:**
   - NO_MATCH (id: 0): Revisi tidak match dengan candidate
   - MATCH (id: 1): Revisi matches dengan candidate

   **Training Configuration:**
   - Dataset: ~50+ revision-order pairs (tahap2 data)
   - Data split: 80% train / 20% test (stratified)
   - Batch size: 8
   - Epochs: 4
   - Learning rate: 2e-5
   - Best model: F1 score (match label only - pos_label=1)
   - Threshold for precision: confidence > 0.8 untuk recommend

   **Inference Output:**
   ```
   {
       "label": "MATCH",
       "confidence_score": 0.95,
       "match_probability": 0.94
   }
   ```

   **Usage:**
   - Input text_a: Incoming revision message (e.g., "REVISI DRIVER: Umar Ali, B 9932 SXW")
   - Input text_b: Candidate order (full structured RO context)
   - Output: Top-3 ranked candidates (score descending)
   - Admin validation: Manual review if top score < 0.80 confidence

4. RULE-BASED REFINEMENT LAYER:
   - Post-processing untuk NER output
   - Components:
     * Format standardization: Detect & normalize field labels
     * Phone validation: Indonesian format (0/62 prefix, spacing normalization)
     * Location fuzzy matching: Typo tolerance untuk lokasi (ARGPNTES → ARGOPANTES)
     * Date/time parsing: Support multiple formats (DD-MM, MM-DD, slash/dash)
   - Net effect: Boosts combined ML accuracy dari ~82% (pure ML) → 91%+

5. INTEGRATION FLOW:
   Input (WhatsApp message)
     ↓
   Pre-processing (text normalization)
     ↓
   NER model prediction (21 entity labels)
     ↓
   Event classification (optional: NEW_ORDER vs UPDATE/REVISION)
     ↓
   Rule-based refinement (standardization + validation)
     ↓
   If REVISION detected → Revision Matcher
     ├─ Generate candidate order pool
     ├─ Score each candidate (MATCH probability)
     └─ Return top-3 recommendations
     ↓
   Output: Structured data + confidence scores
     ↓
   Human-in-the-loop validation (admin review)

========================================================================

## 📌 CRITICAL TECHNICAL TERMS TO INCLUDE:

MUST APPEAR dalam output:
- "IndoBERT" / "indobert-base-uncased" / "indobenchmark/indobert-base-p2"
- "Token classification" / "Named Entity Recognition (NER)"
- "BIO tagging scheme" / "Begin-Inside-Outside"
- "Sequence-pair classification" / "Siamese topology" / "semantic matching"
- "Fine-tuned" / "Transfer learning"
- "21 entity types" / "21 labels"
- "Binary classification" / "MATCH / NO_MATCH"
- "Hybrid approach" / "machine learning + rule-based"
- "Max sequence length 128" (NER) / "256" (Revision Matcher)
- "Batch size 8" / "5 epochs" (NER) / "4 epochs" (Revision Matcher)
- "Learning rate 2e-5" / "AdamW optimizer"
- "F1 score" / "seqeval metric"
- "Domain-specific refinement" / "rule-based post-processing"
- "Confidence threshold" / "human-in-the-loop validation"

NUMBERS/METRICS TO INCLUDE:
- 200-300 training orders
- 2 months (Feb-Mar 2026)
- 21 entity labels
- 80/20 train/test split
- 91%+ accuracy (with rules)
- 82% pure ML baseline
- Top-3 candidate recommendation

========================================================================

## 📌 PARAGRAF STRUCTURE EXPECTATIONS:

**Paragraf 1 (~600-900 kata):**
- Opening 1-2 sentences: Situasi masalah ganda
- 3-4 sentences: Why rule-based insufficient
- 3-4 sentences: Why pure ML insufficient + Why hybrid necessary
- 3-4 sentences: Approach positioning + benefits
- Closing 1-2 sentences: Transition to detailed model

**Paragraf 2 (~600-900 kata):**
- Opening 1-2 sentences: Architecture overview (2 models + rules)
- 4-5 sentences: MODEL 1 DETAIL (NER - all specs)
- 4-5 sentences: MODEL 2 DETAIL (Revision Matcher - all specs)
- 2-3 sentences: Rule-based layer description
- 2-3 sentences: Integration flow diagram (textual description)
- Closing 1-2 sentences: Transition ke BAB 2 (Literature Review)

---

## 🎯 TONE & LANGUAGE CHECKLIST:

**TONE:**
- Profesional akademis (formal, structured)
- Technical precision (model names, architectures exact)
- Yet accessible (explain BERT components simply)
- Confident (not apologetic about design choices)
- Narrative flow (smooth connectors between ideas)

**SENTENCE STRUCTURE:**
- Mix short (clarity) + long (detail) sentences
- Use connectors: "Oleh karenanya", "Dengan demikian", "Sebagai konsekuensi"
- Active voice preferred: "Model melakukan ekstraksi..." not "ekstraksi dilakukan..."
- Technical terms: Explain on first mention (e.g., "BIO tagging scheme (Begin-Inside-Outside)")

**KEYWORDS CHECKLIST:**
- [ ] "IndoBERT" mentioned at least 3x
- [ ] "Token classification" / "NER" explained
- [ ] "BIO tagging" / "BIO scheme" mentioned
- [ ] "21 entity types" specified
- [ ] "Sequence-pair classification" / "semantic matching"
- [ ] "Binary classification" / "MATCH" / "NO_MATCH"
- [ ] "Hybrid approach" / "rule-based refinement"
- [ ] "91%+" accuracy mentioned
- [ ] "200-300 orders" dataset size mentioned
- [ ] "5 epochs" (NER) / "4 epochs" (Revision Matcher)
- [ ] "Max sequence length" (128 or 256) mentioned
- [ ] "Learning rate 2e-5" specified
- [ ] "Human-in-the-loop validation"
- [ ] "Confidence threshold/score"
- [ ] "Transfer learning" approach

---

## ✅ OUTPUT FORMAT REQUIREMENTS:

```
[Exactly 2 paragraf, no bullet points or headers in output]
[Each paragraph 300-450 words]
[Text flows smoothly between paragraphs]
[All technical specifications included (not approximated)]
[Transition sentence ke BAB 2 at end]
[Academic tone throughout]
```

---

## 📋 REVIEW CHECKLIST (Post-Generation):

**Completeness:**
- [ ] Paragraf 1 menjelaskan why hybrid approach necessary?
- [ ] Paragraph 2 memberikan detail LENGKAP model NER?
- [ ] Paragraph 2 memberikan detail LENGKAP model Revision Matcher?
- [ ] Semua 21 entity labels tercakup (or grouped logically)?
- [ ] Rule-based layer dijelaskan?
- [ ] Integration flow ada?
- [ ] Transition ke BAB 2 ada?

**Technical Accuracy:**
- [ ] Model names exact: "indolem/indobert-base-uncased" vs "indobenchmark/indobert-base-p2"?
- [ ] Architecture details correct (768, 12 heads, 12 layers)?
- [ ] Training config correct (batch 8, epochs 5/4, lr 2e-5)?
- [ ] Entity labels correct (21 total, BIO scheme)?
- [ ] Sequence lengths correct (128 vs 256)?
- [ ] Metrics correct (F1 score, seqeval)?

**Narrative & Flow:**
- [ ] Smooth transition dari masalah ke solusi?
- [ ] Smooth transition dari Paragraf 1 ke 2?
- [ ] Smooth transition dari Paragraf 2 ke BAB 2?
- [ ] Tone consistent (academic, technical, confident)?
- [ ] Jargon diexplain (not assumed knowledge)?
- [ ] Length ~1200-1800 kata total?

**Cohesion:**
- [ ] Paragraf 1 focus: why hybrid?
- [ ] Paragraf 2 focus: how (technical details)?
- [ ] Both tied to problem statements dari 3 paragraf sebelumnya?
- [ ] Setup clear untuk BAB 2 (literature review)?

---

## 💬 REFINEMENT GUIDANCE:

Jika TERLALU TEKNIS → Minta re-prompt: "Jelaskan model architecture dengan lebih accessible, kurangi jargon teknis"

Jika KURANG DETAIL → Minta re-prompt: "Tambahin detail spesifikasi architecture (hidden size, heads, layers, vocab size)"

Jika TIDAK MENTION SPECIFIC MODELS → Re-prompt: "Sebutkan base model exact names: indolem/indobert-base-uncased untuk NER, indobenchmark/indobert-base-p2 untuk Revision Matcher"

Jika TIDAK FLOW BAIK → Edit manual untuk smoothen connectors

Jika TONE APOLOGETIC → Re-word dari "we couldn't..." ke "this approach focuses on..."

---

## 🚀 READY TO EXECUTE:

**Copy from "TASK: Generate 2 PARAGRAF..." to "[Academic tone throughout]"**

→ Paste ke Gemini

→ Generate!

✅ **Expected time:** 3-5 minutes (copy + paste + wait)

✅ **Expected length:** 2 paragraf, ~1200-1800 kata

✅ **Next step:** Integrate ke latar belakang masalah BAB 1.2 thesis Anda

---

## 📚 REFERENCE TO YOUR CURRENT LATAR BELAKANG:

Paragraf 1-3 sudah ada (lihat INPUT section di atas).
Generate output ini akan menambah 2 paragraf akhir (Paragraf 4-5) dari BAB 1.2.

Final structure BAB 1.2 akan jadi:
- Paragraf 1: Industry context + Rafay intro
- Paragraf 2: Problem #1 (Data Entry Workload)
- Paragraf 3: Problem #2 (Semantic Ambiguity)
- **Paragraf 4: Solution approach → Why hybrid [YOUR OUTPUT 1]**
- **Paragraf 5: Technical model details [YOUR OUTPUT 2]**

---

## ⚡ EXECUTION STEPS:

1. **Copy prompt** (dari "TASK: Generate..." hingga "...tone throughout]")
2. **Paste ke gemini.google.com** (new chat)
3. **Submit** → Wait 3-5 minutes
4. **Review** with quality checklist
5. **Copy output** → Append ke latar belakang masalah existing
6. **Verify** struktur flow BAB 1.2 (5 paragraf cohesive)
7. **Done!** BAB 1.2 Latar Belakang Masalah complete
```

---

**READY TO EXECUTE?**

→ Copy prompt above ke Gemini → Generate 2 paragraf akhir latar belakang!

Setelah generate, saya siap bantu refine/integrate ke thesis Anda. 🎯
