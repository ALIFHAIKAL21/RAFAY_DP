# 🎯 PROMPT MASTER UNTUK GEMINI - BATASAN MASALAH (BAB 1.4)
## Generate 4-6 Paragraf Akademis Natural

**Status:** Ready to Copy-Paste to Gemini  
**Output Target:** 4-6 paragraf (~400-550 kata) untuk BAB 1.4 Batasan Masalah  
**Tone:** Akademis natural, defensive, logis, koherent dengan BAB 1.2 & 1.3  
**Format:** Copy seluruh section "🔥 PROMPT MASTER UNTUK GEMINI" → Paste ke gemini.google.com

---

## 🔥 PROMPT MASTER UNTUK GEMINI

```
Tugas: Generate 4-6 paragraf akademis untuk section "BATASAN MASALAH" dalam BAB 1 (Pendahuluan) 
untuk thesis project "IDP Rafay v2.0 - Hybrid Machine Learning untuk Order Processing".

KONTEKS PENELITIAN:
- Judul: "Implementasi Hybrid Machine Learning untuk Optimisasi Ekstraksi Data Pesanan 
  dan Matching Revisi pada PT. Rafay Logistik berbasis Arsitektur InDoBERT"
- Problem: Lonjakan eksponensial beban entry data manual + ambiguitas pada revisi/refill pesanan
- Solution: Hybrid approach (NER token-level + Revision Matcher sentence-level + rule-based layer)
- Company: PT. Rafay Logistik (200-300 orders/month, 2 admin, berbasis WhatsApp)
- Current status: Prototype/MVP phase, BELUM production operational

BATASAN MASALAH YANG HARUS DICOVER (Explain dalam paragraf natural, tidak as bullet points):

1. **DATA SOURCE SPECIFICITY**: Project membatasi ekstraksi data HANYA dari pesan WhatsApp tidak 
   terstruktur. Data dari sumber lain (SPK system, driver assignment, vehicle allocation) diasumsikan 
   tersedia terpisah dan bukan target ekstraksi. Multi-source data fusion adalah scope terpisah.

2. **ENTITY SET SPECIFICITY**: NER dioptimalkan untuk 21 entity types spesifik Rafay order structure. 
   Model TIDAK validated untuk struktur order berbeda atau operator logistics lain. Generalization 
   ke operator lain require re-training.

3. **OPERATIONAL READINESS EXCLUSION**: Penelitian fokus pada model accuracy via historical test data, 
   BUKAN operational deployment. Excluded: real-time monitoring, production load testing, workflow 
   integration, UI design, scalability untuk >300 orders/month, business impact measurement. 
   Implementation feasibility adalah scope penelitian terpisah.

4. **REVISION MATCHING ADVISORY SCOPE**: Revision Matcher output adalah TOP-3 RECOMMENDATIONS, 
   bukan automatic matching. Final selection adalah admin responsibility. Tidak cover: auto-selection 
   algorithm, ambiguity resolution, revision history tracking. Decision logic enforcement adalah 
   business logic layer scope.

5. **INCOMPLETE DATA COMPLETION LIMITATION**: Project fokus pada ekstraksi informasi yang TERSEDIA 
   di WhatsApp. Jika field absent di message, project NOT include missing data imputation atau 
   inference dari external data. Admin tetap responsible untuk provide missing info. Missing data 
   resolution adalah data acquisition workflow research scope.

6. **TRANSFER LEARNING ARCHITECTURE**: Project menggunakan pre-trained architecture (InDoBERT) dengan 
   fine-tuning, BUKAN custom architecture design. Advanced architecture exploration (RoBERTa, DeBERTa) 
   TIDAK termasuk scope. Fokus adalah efficacy maximization dari existing architecture untuk domain 
   Rafay-specific. Deep learning architecture innovation adalah future research.

7. **RULE-BASED COMPONENT PRAGMATISM**: Rule-based post-processing layer adalah PRAGMATIC necessity 
   untuk operational characteristics Rafay (format variation, typo pattern, location alias). Rules 
   adalah MANUAL-crafted dari historical observation, BUKAN automatic rule generation. Declarative 
   rule framework & automatic rule learning adalah advanced knowledge engineering research scope.

8. **EVALUATION METRIC ACADEMIC FOCUS**: Performance evaluation menggunakan standard NLP metrics 
   (precision, recall, F1-score) pada historical batch test set, BUKAN business-level metrics 
   (order processing time, admin effort reduction). Business impact ROI adalah management decision 
   scope, bukan research scope.

KONTEKS BISNIS RAFAY (untuk make batasan logis & defensible):
- Current workflow: Order dari klien WhatsApp → admin manual entry ke sistem → sometime incomplete 
  → follow-up via WA untuk missing info → finalisasi dengan multiple unit & staggered loading time
- Order structure: 5 unit average per order × 8-10 fields = 40-50 entry per order
- Data volume: 200-300 orders/month = 8,000-15,000 manual entries → admin capacity bottleneck
- Revision pattern: "REVISI DRIVER: Umar Ali, B 9932 SXW" (minimal context, 5-10 candidate matches)
- Data source: WhatsApp is SINGLE communication channel; SPK & driver/vehicle system adalah separate
- Operational constraint: 2 admin + 10-15 drivers; project is OPTIMIZATION not replacement
- Technology maturity: No in-house ML team → using existing pre-trained model is pragmatic

OUTPUT REQUIREMENTS:
- 4-6 paragraf utuh (tidak bullet points)
- Per paragraph: 2-4 kalimat (natural flow)
- Bahasa akademis formal tapi natural, TIDAK terasa AI-generated
- Simple & mudah dipahami (avoid over-complexity)
- Defensible & logis (setiap batasan CONNECTED to actual limitation/constraint)
- Koherent dengan BAB 1.2 (Latar Belakang) & BAB 1.3 (Identifikasi Masalah)
- Include correlation ke business process Rafay where relevant
- NO artificial constraint; semua batasan logis & realistic


STRUKTUR PARAGRAF YANG DIMINTA:

Paragraf 1: Pembukaan - Define "batasan masalah" concept → introduce hybrid approach limitation
Paragraf 2: Data & Entity Scope - WhatsApp specificity + 21 entity set limitation
Paragraf 3: Operational Phase Boundary - Prototype vs operational, excluded aspects
Paragraf 4: Function Scope - Revision advisory tone, incomplete data handling
Paragraf 5: Technology Choice - Transfer learning vs architecture innovation
Paragraf 6 (optional): Evaluation & Business Scope - Academic metrics vs business measurement

TONE GUIDELINE:
- Defensive but not defensive-tone (logis, bukan berlebihan)
- Acknowledge limitation openly (tidak hidden, not weakness—strategic choice)
- Connect to research feasibility & business reality (realistic scope-setting)
- Avoid: "We couldn't..." (passive), use "Research scope deliberately exclude..." (active)
- Natural disclaimer without apologizing


EXAMPLE OPENING (for reference, generate your own):
"Mengingat kompleksitas operasional PT. Rafay dan karakteristik unik data WhatsApp, penelitian ini 
mendefinisikan batasan masalah yang spesifik untuk memastikan feasibility research sekaligus 
menghasilkan contribution bermakna bagi industri logistics. Batasan masalah mencakup scope data, 
entity set, operational phase, function level, technology choice, dan evaluation metric yang 
deliberate dipilih berdasarkan business context dan research capability."

NOW GENERATE 4-6 PARAGRAF AKADEMIS NATURAL untuk BAB 1.4 Batasan Masalah dengan struktur, content, 
dan tone yang sudah dijelaskan di atas.
```

---

## INSTRUKSI PENGGUNAAN:

### Step 1: Copy Prompt
Salin seluruh text di dalam section "🔥 PROMPT MASTER UNTUK GEMINI" (dimulai dari "Tugas:" hingga akhir)

### Step 2: Paste to Gemini
1. Buka gemini.google.com
2. Create new chat
3. Paste prompt di atas
4. Submit

### Step 3: Review + Integrate
- Gemini akan generate 4-6 paragraf untuk BAB 1.4
- Review hasilnya:
  - ✅ Cover semua 8 batasan logis
  - ✅ Natural academic tone
  - ✅ Koherent dengan BAB 1.2 & 1.3
  - ✅ 4-6 paragraf format
  - ✅ Simple & mudah dipahami
- Paste hasil ke file `BATASAN_MASALAH_FINAL_OUTPUT.md` (di same folder)

### Step 4 (Optional): Refinement
Jika hasilnya kurang perfect, prompt Gemini untuk refinement:
- "Gabungkan paragraf 1-2 jadi lebih concise"
- "Tambah lebih banyak connection ke business Rafay"
- "Kurangi technical jargon di paragraf 3"
- Etc.

---

## 🎁 BONUS: CHECKLIST QUALITY HASIL GEMINI

Setelah Gemini generate, verify:

- [ ] ✅ Data Source Specificity jelas explained (WhatsApp only)
- [ ] ✅ Entity Set 21-type Rafay-specific mentioned
- [ ] ✅ Operational readiness excluded dengan clear
- [ ] ✅ Revision matching top-3 advisory scope explained
- [ ] ✅ Incomplete data handling terdefinisi
- [ ] ✅ Transfer learning pragmatic choice explained
- [ ] ✅ Rule-based manual crafted (bukan auto-gen)
- [ ] ✅ Academic metric fokus (precision, recall, F1) mentioned
- [ ] ✅ Business Rafay correlation terintegrasi natural
- [ ] ✅ Tone akademis natural (bukan defensive/apologetic)
- [ ] ✅ 4-6 paragraf format
- [ ] ✅ Simple & mudah dipahami
- [ ] ✅ Grammatically correct & well-structured

Jika semua ✅, ready untuk advisor review!

---

## 🔗 HUBUNGAN DENGAN FILE LAIN:

**Dependency (refer sebelum Gemini):**
- ANALISIS_BATASAN_MASALAH_BLUEPRINT.md ← Detailed explanation semua 8 batasan
- LATAR_BELAKANG_MASALAH_RINGKAS_DIPERBAIKI.md ← BAB 1.2 reference (untuk koherensi)

**Previous generated (untuk context):**
- README_KONSULTASI_FINAL.md ← BAB 1.3 Identifikasi Masalah (follow-up ke ini)

**Output akan di-save:**
- BATASAN_MASALAH_FINAL_OUTPUT.md ← Hasil Gemini (create setelah Gemini generate)

---

## ⏱️ TIMING:

- Copy-Paste prompt: 2 min
- Gemini generation: ~30-60 detik
- Review hasil: 5-10 min
- Optional refinement: 5-15 min
- Total: ~20-30 min untuk complete BAB 1.4

---

## 📍 NEXT STEP:

1. **Execute Prompt** (copy → paste → submit)
2. **Save Output** ke `BATASAN_MASALAH_FINAL_OUTPUT.md`
3. **Verify checklist** quality
4. **Integrate ke thesis** BAB 1.4
5. **Final step:** BAB 1 COMPLETE (1.1 intro + 1.2 latar + 1.3 identifikasi + 1.4 batasan DONE)

---

**PROMPT MASTER READY TO USE! 🎯**

Copy segala sesuatu di bagian "🔥 PROMPT MASTER UNTUK GEMINI" → Paste ke Gemini → Generate → Done! ✅
