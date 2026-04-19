# 🎯 WORKFLOW GUIDE: Dari Raw Data ke Skripsi Latar Belakang

## OVERVIEW: Anda Sudah Punya

Saya telah membuat 6 dokumen untuk Anda:

```
📂 Dokumentasi Konsultasi Skripsi RAFAY IDP
├── KONSULTASI_SKRIPSI_STRUKTUR.md (9 bab outline + tips)
├── KONSULTASI_SKRIPSI_TECHNICAL.md (Deep-dive teknis per model)
├── KONSULTASI_SKRIPSI_VISUALIZATION.md (Template figure & presentation)
├── ANALISIS_MASALAH_RAFAY_MENDALAM.md ← NEW! (Analisis problem spesifik)
├── PROMPT_GEMINI_PROBLEM_BACKGROUND.md ← NEW! (Prompt untuk Gemini)
└── PROBLEM_SOLUTION_MAPPING.md ← NEW! (Visual mapping & cost-benefit)
```

---

## LANGKAH-LANGKAH PRAKTIS

### LANGKAH 1: Pahami Masalah yang Sebenarnya (15 menit)
```
✅ Baca file: ANALISIS_MASALAH_RAFAY_MENDALAM.md

Fokus pada section:
├─ Section 1 (Data Quality Issues) - pahami 5 tipe masalah
├─ Section 3 (Scalability Analysis) - lihat growth scenarios
├─ Section 4 (Core Problems Mapped) ← Key insight!
│  Ini menjelaskan KENAPA NER + Revision Matcher diperlukan
└─ Section 5 (Realistic Problem Statement) - inilah masalah Anda

Action: Highlight bagian yang resonates dengan reality PT. Rafay
```

### LANGKAH 2: Visualisasi Problem-Solution Mapping (10 menit)
```
✅ Baca file: PROBLEM_SOLUTION_MAPPING.md

Focus pada:
├─ Diagram 1: Current State vs Future State
│  → Understand transformation journey
├─ Diagram 2: Problem Categorization with Examples
│  → See concrete examples dari data yang user kasih
├─ Diagram 3: How NER + Revision Matcher Solve Problems
│  → Clear mapping: Problem → Model → Metric → Impact
└─ Summary Table & Cost-Benefit Analysis
    → Business case untuk thesis

Action: Screenshot diagrams untuk reference saat writing
```

### LANGKAH 3: Siapkan Data Untuk Gemini (15 menit)
```
✅ Collect semua reference data:

├─ Raw data examples dari WhatsApp (sudah ada di ANALISIS file)
├─ Current metrics (200-300 orders/month, 5-8% error, 3-5 min/order)
├─ Business context (2 admins, growth to 500 in 2 years)
├─ Technical target (89% F1 for NER, 90% accuracy for Matcher)
└─ Field definitions (9 critical fields to extract)

Semua sudah ada di ANALISIS_MASALAH_RAFAY_MENDALAM.md
Tinggal reference saat kasih prompt ke Gemini
```

### LANGKAH 4: Generate Latar Belakang Masalah dengan Gemini (10-15 menit)

#### Option A: Copy-Paste Prompt ke Gemini (Recommended)
```
📋 Go to: https://gemini.google.com (atau https://chat.openai.com)

1. Open PROMPT_GEMINI_PROBLEM_BACKGROUND.md
2. Copy seluruh "PROMPT MASTER" section
3. Paste ke Gemini/ChatGPT
4. Wait for output (2-5 minutes)
5. Copy hasil ke file baru: "BAB_1_LATAR_BELAKANG_DRAFT.md"
```

#### Option B: Gunakan Gemini Advanced Mode (dengan file upload)
```
1. Convert ANALISIS_MASALAH_RAFAY_MENDALAM.md ke PDF
2. Upload ke Gemini Advanced
3. Ask: "Based on this problem analysis, generate problem background statement for thesis"
4. Let Gemini extract context & generate
5. Result biasanya lebih contextual & accurate
```

### LANGKAH 5: Edit & Refine Output Gemini (20-30 menit)

#### Quality Checklist:
```
□ Panjang: 2000-3000 kata (check word count)
□ Struktur: Ada 5-6 sub-sections (1.1 Latar, 1.2 Masalah, 1.3 Gap, etc.)
□ Real data: Minimal 3-4 konkret examples dari raw data
□ Both models: InDoBERT NER + Revision Matcher mentioned & explained
□ Scalability: Growth story (200 → 500 → 2000 orders) ada
□ Business angle: 5-8% error, 3-5 min/order, bottleneck at 300 orders
□ Tech angle: Rule-based insufficient, NLP/BERT necessary
□ Tone: Academic, clear, not marketing-y
□ Citations: Placeholder untuk papers (fill in later after lit review)
□ Flow: Logical progression general → specific → technical
```

#### Common Edits Needed:
```
Fix 1: Gemini might be too generic
└─ Solution: Add specific PT. Rafay numbers & names
    "di perusahaan X" → "di PT. Rafay Logistik"
    "admin" → "2 admin PT. Rafay"

Fix 2: Gemini might overemphasize one model
└─ Solution: Ensure both NER & Revision Matcher equally discussed

Fix 3: Gemini might miss the "scalability story"
└─ Solution: Add paragraph about growth trajectory

Fix 4: Language quality
└─ Solution: Proofread, fix grammar, improve sentence structure

Fix 5: Too technical or too simple
└─ Solution: Adjust technical level to match your thesis format
```

### LANGKAH 6: Integration ke Thesis BAB 1 (30-45 menit)

```
📝 Final Thesis Structure:

BAB 1: PENDAHULUAN
├── 1.1 Latar Belakang (use Gemini output here)
├── 1.2 Rumusan Masalah (extract from your analysis)
├── 1.3 Tujuan Penelitian (refine from KONSULTASI_STRUKTUR.md)
├── 1.4 Manfaat Penelitian (copy from KONSULTASI_STRUKTUR.md, adapt)
└── 1.5 Batasan Penelitian (define scope)

Action steps:
1. Copy Gemini output into 1.1
2. Draft 1.2 based on ANALISIS file (4 main problems listed)
3. Copy 1.3 from KONSULTASI_SKRIPSI_STRUKTUR.md (tujuan penelitian)
4. Adapt 1.4 dari KONSULTASI file
5. Define 1.5 (what you're NOT covering)
```

---

## TIMELINE RECOMMENDATION

```
Week 1 - Problem Understanding & Framing
├─ Day 1 (Mon): Read ANALISIS + PROBLEM-SOLUTION files (30 min)
├─ Day 2 (Tue): Prepare Gemini prompt + collect data references (30 min)
├─ Day 3 (Wed): Generate problem background with Gemini (20 min)
├─ Day 4 (Thu): Edit & refine output (45 min)
├─ Day 5 (Fri): Integrate into thesis BAB 1 draft (45 min)
└─ End of week: BAB 1 Pendahuluan DONE ✓

Week 2 - Literature Review (parallel track)
├─ Start collecting 50+ papers (BERT, NER, semantic matching)
├─ Add citations to problem background
├─ Prepare BAB 2 (Tinjauan Pustaka)
└─ Cross-reference with problem background
```

---

## EXPECTED OUTPUT EXAMPLE

Dari Gemini, Anda akan dapat sesuatu seperti:

```markdown
# BAB 1: PENDAHULUAN

## 1.1 Latar Belakang

### Konteks Industri Logistik Indonesia
Industri logistik Indonesia mengalami transformasi digital yang pesat...
[~400 words about logistics industry, WhatsApp usage, data entry challenges]

### PT. Rafay Logistik: Operasi Saat Ini
PT. Rafay Logistik adalah perusahaan ekspedisi yang melayani...
[~300 words about company, 200-300 orders/month, 2 admins, manual process]

### Identifikasi Masalah Spesifik

#### Masalah #1: Inkonsistensi Data dan Typo
Dari analisis chat operasional PT. Rafay, ditemukan...
[~400 words with concrete examples]

#### Masalah #2: Kompleksitas Multi-Slot Order
Pola ordering di PT. Rafay menunjukkan struktur unik...
[~400 words with example]

#### Masalah #3: Manajemen Revisi Data
Revisi order sering datang tanpa konteks eksplisit...
[~300 words]

#### Masalah #4: Bottleneck Skalabilitas
Dengan pertumbuhan bisnis yang diproyeksikan...
[~300 words about growth scenario]

### Kesenjangan Teknologi (Technical Gap)
Pendekatan berbasis rule/regex tidak cukup menangani...
[~300 words about why NLP/BERT approach needed]

### Potensial Solusi dengan RAFAY IDP
Proyek RAFAY IDP menggunakan dua model spesialis...
[~400 words about InsoBERT NER + Revision Matcher]
[Include metrics: 89% F1, 90% accuracy, 92% coverage]

## 1.2 Rumusan Masalah

1. Bagaimana mengekstrak informasi logistik terstruktur dari chat...
2. Bagaimana mencocokkan order revisi dengan order historis...
3. [etc - 4-5 research questions]

## 1.3 Tujuan Penelitian
[copy from KONSULTASI file]

## 1.4 Manfaat Penelitian
[copy from KONSULTASI file]

## 1.5 Batasan Penelitian
[your own scope definition]
```

---

## TROUBLESHOOTING

### Issue #1: Gemini Output Terlalu Panjang/Pendek
```
Solution:
- Panjang: Trigger dengan prompt "Keep it to max 2500 words"
- Pendek: Trigger dengan "Expand each problem to 300-400 words"
- Atau: Gunakan follow-up: "Kan you expand section 1.2? Add more technical depth"
```

### Issue #2: Gemini Forget About Revision Matcher
```
Solution:
- Add emphasis di prompt: "[IMPORTANT] Both InDoBERT NER AND Revision Matcher must be discussed equally"
- Or follow-up: "Please rewrite section where both models are equally featured"
```

### Issue #3: Output Terasa Generic
```
Solution:
- Add more specific details from PT. Rafay to prompt
- Include exact numbers (200-300 orders, 5-8% error, etc.)
- Use specific examples from raw data
```

### Issue #4: Tidak Match dengan Universitas's Style Guide
```
Solution:
- After Gemini output, do manual edit untuk style adjustment
- Or add to prompt: "Use formal academic Indonesian style suitable for [your university]"
```

---

## PRO TIPS

### Tip #1: Chain Multiple Prompts
```
Instead of one giant prompt, use sequence:
1. First prompt: Generate "Konteks Industri Logistik" part only
2. Second prompt: "Diberikan konteks ini, buatkan PT. Rafay background"
3. Third prompt: "Diberikan masalah ini, buatkan technical gap section"
4. Combine all outputs

Result: More coherent, better flow, depth pada each section
```

### Tip #2: Use Version Control
```
git init your thesis folder
├─ BAB_1_LATAR_v1.md (Gemini first output)
├─ BAB_1_LATAR_v2.md (After first edit)
├─ BAB_1_LATAR_v3.md (Peer review feedback)
└─ BAB_1_LATAR_FINAL.md (Final version)

Easier to track changes & revert if needed
```

### Tip #3: Get Peer Feedback Early
```
Share BAB 1 draft with:
├─ Your advisor/pembimbing
├─ Another student (from different project)
└─ Someone from PT. Rafay (verify accuracy)

Then incorporate feedback into refinement round
```

### Tip #4: Cross-Reference with KONSULTASI Files
```
When writing BAB 2-9, constantly reference:
├─ KONSULTASI_SKRIPSI_STRUKTUR.md (for outline & tips)
├─ KONSULTASI_SKRIPSI_TECHNICAL.md (for detailed experiment design)
└─ KONSULTASI_SKRIPSI_VISUALIZATION.md (for figure templates)

Coherence across all chapters
```

---

## NEXT STEPS AFTER BAB 1

Once BAB 1 is done:

```
✅ BAB 1 DONE: Pendahuluan (20-30 halaman)

⏭️ BAB 2: Tinjauan Pustaka (40-50 halaman)
   ├─ BERT fundamentals (Devlin et al., 2018)
   ├─ NER approaches (classical vs neural)
   ├─ Semantic matching & similarity
   ├─ Logistics NLP (if papers available)
   └─ Related work comparison table

⏭️ BAB 3: Metodologi (30-40 halaman)
   ├─ Use KONSULTASI_SKRIPSI_TECHNICAL.md as guide
   ├─ System architecture
   ├─ Model details (architecture, training config)
   ├─ Experimental design
   └─ Evaluation metrics

⏭️ BAB 4-5: Model Development
   ├─ Training procedure
   ├─ Hyperparameter tuning
   ├─ Results per model

... and so on
```

---

## FINAL CHECKLIST

Before submitting BAB 1 to advisor:

```
□ Reading: Is it clear & understandable for someone unfamiliar with PT. Rafay?
□ Structure: Does it flow logically from general → specific → technical?
□ Examples: Are there 3-4 concrete examples from raw data?
□ Both models: Are NER + Revision Matcher both mentioned?
□ Business case: Is growth bottleneck/ROI clear?
□ Academic tone: Is it suitable for university thesis?
□ Numbers: Are all metrics (200 orders, 5-8% error, etc.) accurate?
□ Grammar: Checked spelling & grammar?
□ Length: Is it within expected range (2000-3000 words)?
□ Citations: Are placeholder citations added (to fill after lit review)?
□ Advisor feedback: Has advisor seen & approved scope?
```

---

## CONTACT POINT: IF STUCK

If problems arise during this process:

1. **Problem with Gemini output**: Re-read PROBLEM_SOLUTION_MAPPING.md (concrete examples there)
2. **Problem with structure**: Re-read KONSULTASI_SKRIPSI_STRUKTUR.md (BAB 1 template there)
3. **Problem with technical depth**: Re-read KONSULTASI_SKRIPSI_TECHNICAL.md (detailed explanations there)
4. **Problem with visualization**: Use KONSULTASI_SKRIPSI_VISUALIZATION.md (templates)
5. **Everything**: Go back to ANALISIS_MASALAH_RAFAY_MENDALAM.md (reference material)

---

*You now have a complete workflow from raw problem → structured thesis. Good luck! 🚀*
