# 📝 PROMPT GEMINI - BAB 1.4 BATASAN MASALAH (4-6 Paragraf)

**Status:** Ready to copy-paste ke Gemini  
**Output Expected:** 4-6 paragraf (±1500-2500 words)  
**Language:** Bahasa Indonesia formal/akademis  
**Purpose:** Generate scope limitations yang realistic & logic untuk skripsi

---

## 🎯 PROMPT MASTER (COPY-PASTE KE GEMINI):

```
TASK: Generate BATASAN MASALAH (BAB 1.4) untuk skripsi RAFAY IDP V2.0 yang 
mendeskripsikan scope penelitian, keterbatasan teknis, dan boundary penelitian 
yang LOGIS dan REALISTIS.

OUTPUT: 4-6 paragraf (bukan bullet points, text paragraf penuh)
LENGTH: ~1500-2500 kata total
LANGUAGE: Bahasa Indonesia formal/akademis
STYLE: Profesional, konkrit, defensive (menjelaskan WHY batasan ini necessary)

CRITICAL NOTE: Batasan masalah bukan untuk "justify shortcomings" tapi untuk 
"define research scope with intention". Format harus "Penelitian ini fokus pada 
X, tidak mencakup Y, karena Z."

========================================================================

POIN 1: HYBRID APPROACH (ML + RULE-BASED)
==========================================

BASE STATEMENT:
"Penelitian ini menggunakan pendekatan hybrid yang menggabungkan machine learning 
(InDoBERT NER + Revision Matcher) dengan rule-based post-processing untuk 
refinement. Pendekatan ini bukan pure machine learning research, melainkan 
engineering-oriented application yang dirancang khusus untuk menangani 
karakteristik noise dan formatinkonsistenan dalam data operasional Rafay."

EXPAND WITH DETAILS:

1. HYBRID APPROACH JUSTIFICATION:
   - Data real Rafay: 15+ field label variations, typos, partial entries
   - Pure ML tanpa rule-based → accuracy ceiling terbatas (false positives 15-20%)
   - Kombinasi ML + rule dikurasi berdasarkan domain knowledge Rafay:
     * Format standardization rules (detect field labels)
     * Phone validation regex (Indonesian format)
     * Location fuzzy matching rules (typo tolerance)
     * Date/time parsing rules (multiple formats)
   - Rule-based refinement: meningkatkan extraction accuracy dari 82% → 91%

2. SCOPE LIMITATION:
   - Tidak fokus pada "pure NLP/ML algorithm innovation"
   - Fokus pada "practical AI application untuk domain spesifik"
   - Rule-based komponennya adalah "necessary foundation" bukan "research artifact"
   - Trade-off: generalizability vs applicability (chosen: applicability)

3. WHAT THIS MEANS:
   - ML models tidak bisa standalone (perlu rule-based layer)
   - Research bukan tentang "better NER algorithm" tapi "better integration"
   - Transferability ke domain lain: terbatas (rules Rafay-specific)
   - Contribution: proven pipeline untuk domain-specific extraction, bukan algo innovation

---

POIN 2: DATA SOURCE SCOPE (WHITE-LISTED ONLY)
==============================================

BASE STATEMENT:
"Data yang diekstraksi terbatas HANYA pada informasi yang bersumber dari 
pesan WhatsApp REQUEST ORDER. Data dari sumber lain (SPK, invoice database, 
sistem tracking eksternal, dll) di-ASUMSIKAN sudah tersedia atau di-SKIP dari 
pipeline ekstraksi. Penelitian ini fokus pada masalah extraction, bukan data 
source integration."

EXPAND WITH DETAILS:

1. DATA SOURCE YANG DI-COVER:

   ✅ WHITE-LISTED (Dari WhatsApp):
   - Identifier fields: tgl_ro, lokasi_pickup, rute_tujuan
   - Unit fields: jenis_truck, volume_cbm, jumlah_unit
   - Operational fields: waktu_loading, driver_name, nopol (plat), kontak_driver
   - Revision/Refill data: dari pesan terpisah "REVISI DRIVER", "REVISI NOPOL"
   
   ❌ OUT-OF-SCOPE (Dari sumber lain):
   - SPK number (dari sistem tickets, tidak di-WA)
   - Shipper/consignee details (dari database, tidak di-WA)
   - Route optimization (dari GPS/maps API)
   - Historical pricing (dari accounting system)
   - Real-time vehicle tracking (dari telematics)

2. WHY THIS LIMITATION:
   - Integration dengan multiple system = out of scope
   - Research fokus: "extract structured data dari unstructured text"
   - Not: "build enterprise data integration system"
   - Data fusion dari multiple sources = future work

3. FIELD EXTRACTION SCOPE:
   - Input: Raw WhatsApp message (unstructured, multiple formats)
   - Output: 10-12 structured fields per unit order
   - NOT output: 50+ fields yang ada di database Rafay
   - Rationale: mengurangi scope ke "most critical + extractable from WA"

---

POIN 3: OPERASIONAL MATURITY (R&D, BUKAN PRODUCTION)
=====================================================

BASE STATEMENT:
"Project ini berada pada fase Research & Development dengan fokus pada 
proof-of-concept dan validation. Sistem BELUM diintegrasikan ke dalam pipeline 
operasional real-time PT. Rafay, dan masih memerlukan validasi manual serta 
human-in-the-loop decision making. Deployment dan optimization untuk production 
scale merupakan scope pekerjaan future engineering, bukan bagian dari penelitian 
ini."

EXPAND WITH DETAILS:

1. CURRENT MATURITY STATE:
   - Phase: R&D / POC (tidak production-ready)
   - Usage: Offline batch processing (not real-time streaming)
   - Validation: Manual human review masih required
   - Integration: Standalone pipeline (tidak integrate dengan WhatsApp API)
   - Monitoring: Limited (tidak ada production observability)

2. WHAT'S NOT INCLUDED IN THIS RESEARCH:
   - Real-time API integration dengan WhatsApp Business API
   - Production observability (monitoring, alerting, logging)
   - Edge case handling untuk scale operational 1000+ orders/bulan
   - Failover mechanism / backup systems
   - Security hardening (credential management, data encryption)
   - Load testing dan performance optimization
   - A/B testing dalam operational context

3. HUMAN-IN-THE-LOOP REQUIREMENT:
   - System output: recommendations/suggestions (confidence scores)
   - Decision: masih dilakukan oleh human operator
   - Feedback loop: manual, bukan automated retraining
   - Rationale: safety-critical (logistics decisions) → human validation necessary

4. TIMELINE SCOPE:
   - Training data: Feb-Mar 2026 only (limited temporal coverage)
   - Validation: 2-3 bulan testing
   - Not covering: seasonal variations, year-long operational patterns

---

POIN 4: EXTRACTION SCOPE (WA FIELDS ONLY, SPECIFIC SUBSET)
===========================================================

BASE STATEMENT:
"Penelitian ini HANYA menangani ekstraksi field-field tertentu yang DAPAT 
diekstraksi dari format unstructured WhatsApp message. Field-field yang 
memerlukan external data source lookup (SPK, database reference) atau memerlukan 
keputusan business logic yang kompleks di-SKIP dari scope ekstraksi. Focus 
adalah pada 'what can we reasonably extract from raw text', bukan 'what we 
ideally want'."

EXPAND WITH DETAILS:

1. FIELD EXTRACTION MATRIX:

   EXTRACTABLE dari WA (In-scope):
   ✅ tgl_ro (date inference dari message timestamp)
   ✅ unit_count (numeric extraction)
   ✅ truck_type (entity recognition: TWB/CDDL/Tronton)
   ✅ volume_cbm (numeric + unit extraction)
   ✅ pickup_location (NER location entity)
   ✅ route_destination (NER + rute parsing)
   ✅ loading_time (time extraction + date parsing)
   ✅ driver_name (NER person entity)
   ✅ vehicle_plate (pattern recognition: nopol format)
   ✅ contact_phone (pattern recognition: Indo phone format)
   ✅ revision_references (semantic matching dari "REVISI X" messages)

   TIDAK EXTRACTABLE (Out-of-scope):
   ❌ spk_number (harus lookup ke database)
   ❌ shipper_name (harus ekstensif domain knowledge)
   ❌ shipper_contact (bukan di WA, dari database)
   ❌ priority_level (memerlukan business decision)
   ❌ cost_estimate (harus calculation engine)
   ❌ margin_analysis (memerlukan aksess pricing database)
   ❌ vehicle_availability (hanya di internal sistem)

2. PARTIAL DATA HANDLING:
   - Banyak WA message dengan incomplete data (field kosong)
   - Extraction tetap dilakukan untuk available fields
   - Missing fields di-flag sebagai NULL (tidak di-hallucinate)
   - Refill/Revision messages menambah informasi partial data

3. MULTI-SLOT ORDER COMPLEXITY:
   - Order dapat memiliki 2-10 "slots" (time windows dengan driver assignment)
   - Ekstraksi dilakukan per-slot
   - Partial slot (hanya rute/waktu, driver kosong) di-handle dengan "awaiting refill"
   - Revision matcher menghubungkan partial Data dengan refill messages

---

POIN TAMBAHAN: TEKNOLOGI & ARCHITECTURE SCOPE
==============================================

1. MODEL ARCHITECTURE:
   - Only using off-the-shelf InDoBERT (tidak fine-tuning dari scratch)
   - Transfer learning approach (minimize training data needed)
   - Not exploring: LLM approaches, BERT-style model from scratch, ensembling methods
   - Single-model-per-task paradigm (NER + Revision Matcher separate)

2. TRAINING DATA SCOPE:
   - Size: ~200-300 orders/2 months collect + labeling
   - Quality: manual annotation (limited budget untuk data labeling)
   - Diversity: limited (mainly Feb-Mar 2026 patterns)
   - NOT including: historical data 1+ tahun, seasonal variations
   - Validation set: ~20% dari data

3. INFRASTRUCTURE SCOPE:
   - Stack: PostgreSQL + SQLAlchemy + Streamlit (sudah existing)
   - Not including: cloud scaling, containerization, CI/CD pipeline
   - Deployment: local/server-based (not cloud)
   - Compute: standard GPU (tidak menggunakan TPU/specialized hardware)

4. LANGUAGE SCOPE:
   - Fokus: Bahasa Indonesia dengan Sundanese/Javanese code-mixing
   - Not including: multi-language support
   - Dialects: Jakarta/Surabaya regional variations (captured dalam training data)

---

POIN TAMBAHAN: RESEARCH CONTRIBUTION SCOPE
============================================

WHAT THIS RESEARCH IS:
✅ Applied ML engineering untuk domain logistics operasional
✅ Proof-of-concept hybrid ML+rules architecture
✅ Domain-specific dataset dan baseline models
✅ Practical pipeline untuk semi-automated data extraction

WHAT THIS RESEARCH IS NOT:
❌ Novel ML algorithm development
❌ General-purpose NER/extraction framework
❌ Production deployment dengan guarantees SLA
❌ Cost-benefit analysis lengkap (financial ROI)
❌ Comparative study terhadap existing logistics software

========================================================================

## 📌 PARAGRAF STRUCTURE EXPECTATIONS:

**Paragraf 1 (Overview):** Jelaskan "penelitian ini fokus pada X, tidak mencakup Y"
- Hybrid ML+rules approach
- Domain-specific untuk Rafay
- R&D phase, bukan production

**Paragraf 2 (Data & Field Scope):** Jelaskan DUA batasan:
- Data source: hanya WhatsApp (tidak SPK, database, etc)
- Field scope: 10-12 fields extractable, tidak 50+ fields butuh
- Kenapa limitation ini logical: practical extraction focus

**Paragraf 3 (Technology & Scale Scope):** Jelaskan "what we're not doing"
- Transfer learning (bukan model from scratch)
- Limited training data (200-300 orders, 2 months, bukan 1+ tahun)
- Offline batch, bukan real-time streaming
- Local deployment, bukan cloud scale

**Paragraf 4 (Operasional Limitations):** Jelaskan maturity & human-in-the-loop
- R&D phase, bukan production ready
- Manual validation required
- Safety-critical (logistics) → human decision making necessary
- Single pipeline, bukan enterprise integration

**Paragraf 5 (Optional - Contribution Clarity):** Clarify what research ADALAH
- Applied engineering (bukan algorithm innovation)
- Proof-of-concept untuk domain-specific extraction
- Baseline models + dataset untuk logistics
- Rationale: practical value vs academic novelty trade-off

---

## 🎯 TONE & KEYWORDS CHECKLIST:

**MUST INCLUDE TERMS:**
- "Penelitian ini fokus pada"
- "Tidak mencakup" / "Out-of-scope"
- "Karena" (reasoning untuk why limitation is logical)
- "Domain-specific" 
- "R&D phase"
- "Hybrid approach"
- "WhatsApp extraction only"
- "10 field scope"
- "Manual validation"
- "Transfer learning"
- "Applied engineering"
- "Proof-of-concept"
- "Future work" (acknowledge what comes next)

**TONE:**
- Confident (tidak apologetic tentang limitations)
- Matter-of-fact (state batasan as design decision, not shortcoming)
- Practical (justify setiap batasan dengan reason bisnis/teknis)
- Academic (formal language tapi accessible)

---

## ✅ OUTPUT REQUIREMENTS:

```
[Hanya output 4-6 paragraf. Jangan ada bullet points, headers, atau explanations]
[Setiap paragraf 200-400 kata]
[Include semua 4 poin + 1-2 poin tambahan]
[Gunakan connectors yang smooth (Oleh karena itu, Sebagai konsekuensi, dst)]
[Every limitation harus ada REASON WHY, bukan hanya "WHAT"]
```

---

## 📋 4-STEP USAGE GUIDE:

**Step 1:** Copy seluruh section "TASK: Generate BATASAN MASALAH..." hingga "[OUTPUT ONLY...]"

**Step 2:** Buka gemini.google.com, buat chat baru

**Step 3:** Paste prompt, submit (tunggu ~30-60 detik response)

**Step 4:** Review output:
- ✅ Apakah 4-6 paragraf (tidak bullet)?
- ✅ Apakah semua 4 poin tercakup?
- ✅ Apakah ada ROW (reasoning) untuk setiap batasan?
- ✅ Apakah tone confident, bukan apologetic?
- ✅ Apakah semua 10+ keywords tersedia?
- ✅ Apakah paragraph structure align dengan expectations?

Jika ada yang kurang → copy output ke file, edit manual, atau re-prompt dengan clarification.

---

## 💡 QUALITY CHECKLIST (Post-Generation):

**Completeness:**
- [ ] Hybrid ML+rules philosophy jelas
- [ ] Data source scope jelas (only WhatsApp)
- [ ] Field extraction scope jelas (10 fields, not 50)
- [ ] R&D vs production boundary jelas
- [ ] Human-in-the-loop requirement jelas
- [ ] Transfer learning approach disebutkan
- [ ] Domain-specific limitation acknowledged

**Logical Consistency:**
- [ ] Setiap batasan punya reasoning (tidak arbitrary)
- [ ] Batasan koherent dengan masalah yang diidentifikasi sebelumnya
- [ ] Tidak ada kontradiksi dengan BAB 1.3 (Identifikasi Masalah)
- [ ] Trade-off dijelaskan (scope depth vs breadth)

**Tone & Language:**
- [ ] Confident (designing scope, bukan excusing limitations)
- [ ] Formal academic (tapi accessible)
- [ ] Goal-oriented (these limits enable THIS research)
- [ ] Bukan defensive tone

**Cohesion:**
- [ ] Smooth flow antara topic-topic
- [ ] Clear connectors between limitations
- [ ] Concluding statement yang tie everything together
- [ ] Bridge ke BAB 2 (literature review) yang logical

---

## 💬 REFINEMENT GUIDANCE:

Jika output TERLALU TEKNIS → Prompt ulang dengan "Gunakan bahasa lebih accessible, batasi jargon teknis"

Jika output TERLALU PERMISSIVE → Prompt ulang dengan "Tegaskan batasan yang lebih dalam, jangan soft"

Jika output TIDAK COVER SEMUA 4 POIN → Copy-paste output, add manual sections untuk poin missing

Jika TONE TERASA APOLOGETIC → Edit trigger words dari "we cannot do..." menjadi "this research focuses on..."

---

## 🚀 READY TO EXECUTE:

**Copy from "TASK: Generate BATASAN MASALAH..." to "[OUTPUT ONLY THE PARAGRAPHS]"**

→ Paste ke Gemini

→ Generate!

✅ **Expected time:** 2-3 minutes (copy + paste + review)

✅ **Expected output:** 4-6 paragraf yang comprehensive, defensive, professional

✅ **Next step (setelah diterima):** Integrate ke BAB 1.4 thesis Anda

---

## 📚 REFERENCE TO SUPPORT DOCS:

Jika butuh mendalam sebelum generate:
- Lihat: MASALAH_1_DATA_ENTRY_WORKLOAD.md (untuk problem context)
- Lihat: PROMPT_GEMINI_MASALAH_2_REVISION_PARTIAL.md (untuk 2nd problem scope)
- Lihat: KONSULTASI_SKRIPSI_STRUKTUR.md (untuk BAB 1 section context)
```

---

**Ready to execute?**

1. **Copy prompt** (dari "TASK: Generate..." hingga "...PARAGRAPHS]")
2. **Paste ke [gemini.google.com](https://gemini.google.com)**
3. **Generate** → Review dengan quality checklist
4. **Integrate** ke BAB 1.4 thesis Anda

Nuansa penting: Batasan Masalah BUKAN untuk "justify shortcomings", tapi untuk "define research scope with intention". Setiap batasan harus ada reasoning, bukan hanya statement.