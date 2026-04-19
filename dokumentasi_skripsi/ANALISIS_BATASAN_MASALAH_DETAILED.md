# 📊 ANALISIS KORELASI BISNIS RAFAY → PROJECT SCOPE → BATASAN LOGIS

**Author:** Rafay IDP Documentation  
**Date:** April 2026  
**Purpose:** Map business requirements → project capabilities → research scope boundaries

---

## BAGIAN 1: PEMETAAN BISNIS RAFAY vs PROJECT CAPABILITY

### A. Business Process Rafay (Sekarang)

```
WhatsApp Message (REQUEST ORDER)
    ↓
Admin Decode & Standardize (2-3 min)
    ↓
Excel Input & Manual Validation (2-3 min)
    ↓
Database Entry
    ↓
Operational Execution
```

**Pain Points Existing:**
- Manual decode: 5-8% error rate
- Typo overload: 15+ field label variations
- Time burden: 2-3 menit per order
- Capacity buffer: 2 admin → cannot scale to 500+ orders

**Your Project Solution:**
```
WhatsApp Message (REQUEST ORDER)
    ↓
[RAFAY IDP PIPELINE]
  - NER Extraction (AI)
  - Rule-Based Refinement (Domain Logic)
  - Revision Matcher (Semantic Matching)
    ↓
Structured Data (with confidence scores)
    ↓
Human Validation (Admin only verifies, not decodes)
    ↓
Database Entry
    ↓
Operational Execution
```

**Expected Improvement:**
- Reduce manual work: 2-3 min → <1 min
- Reduce error rate: 5-8% → 2-3%
- Increase capacity: 2 admin berhasil handle 500+ orders dengan ML assist

---

## BAGIAN 2: MAPPING 4 POIN USER → BATASAN LOGIS

### Poin #1: HYBRID ML + RULE-BASED (Bukan Pure ML)

**Penyebab:**

| Bisnis Reality | Technical Need | Design Decision |
|---|---|---|
| 15+ field label variations dalam WA | Pattern matching insufficient | Rule-based label detection + NER confidence scoring |
| Phone typo overload (missing 0, 62 prefix, spacing) | NER alone: false positives | Rule-based validation (regex + prefix standardization) |
| Date format chaos (DD-MM, MM-DD, slashes, dashes) | NER datetime: ambiguous | Rule-based parser untuk common formats |
| Partial order + later revisions | NER missing context | Semantic matcher + rule untuk revision linking |

**Kekurangan yang jadi Batasan:**
- ❌ Pure deep learning approach TIDAK CUKUP untuk Rafay noise level
- ❌ Jika pure ML: accuracy plateau di 82-85% (tidak usable)
- ❌ Rule-based component adalah NECESSARY, bukan "compromise"

**Batasan Logis untuk Skripsi:**
```
"Penelitian ini menggunakan pendekatan HYBRID karena karakteristik data Rafay 
memerlukan domain-specific refinement yang tidak bisa ditangani oleh pure ML. 
Oleh karenanya, fokus penelitian BUKAN pada 'push ML algorithm to limit', 
tapi pada 'optimal integration point antara ML dan domain logic'. Konsekuensinya, 
research ini tidak berkontribusi pada algoritma ML baru, melainkan pada 
APPLICATION ENGINEERING untuk domain spesifik."
```

---

### Poin #2: HANYA DATA WA (Tidak Semua Sumber)

**Penyebab:**

| Business Requirement | Data Source | Scope Decision |
|---|---|---|
| Shipper name & address | Dari WA (sometimes) + Database shipper table (mainly) | ONLY WA extraction, database lookup = out-of-scope |
| SPK (Service Package Kit) number | TIDAK di WA, hanya di internal ticket system | SKIP dari research |
| Vehicle real-time location | GPS telematics API (third-party) | Not extractable dari text |
| Pricing & cost estimate | Calculation engine (complex business logic) | Out-of-scope |
| Historical similar orders | Database lookup (reference matching) | Not ML extraction |

**Alasan Scope Pembatasan:**

1. **Ekstraksi ML = Text Mining** (dari unstructured text)
   - WA message = unstructured text ✅ dapat di-extract
   - SPK number = tidak ada di text ❌ harus lookup
   - Database reference = structured query ❌ bukan extraction

2. **Integration Complexity**
   - Integrate dengan 5+ data sources = enterprise data architecture work
   - NOT research scope = future engineering pipeline
   - Research scope = focus pada "ML extraction dari available text"

3. **Data Quality Control**
   - WA data: dalam kontrol Rafay (format bisa di-standardize)
   - External API: third-party quality (tidak kontrol)
   - Database: legacy system dengan data quality issues
   - Focus: minimize variables = maximize extraction confidence

**Kekurangan yang jadi Batasan:**
- ❌ Research TIDAK COVER full data integration
- ❌ TIDAK ADDRESS enterprise data fusion
- ❌ TIDAK INCLUDE API/database integration patterns

**Batasan Logis untuk Skripsi:**
```
"Ekstraksi terbatas pada data yang TERSEDIA DALAM format unstructured WA message. 
Data dari sumber lain (SPK database, vehicle tracking, pricing engine) di-asumsi 
tersedia atau di-SKIP dari pipeline. Scope ini dipilih karena (1) fokus penelitian 
pada text extraction, bukan data integration; (2) minimisasi variable eksternal 
yang kompleks; (3) memungkinkan proof-of-concept yang tangible dalam batas waktu 
research. Data fusion dari multiple sources merupakan future engineering work."
```

---

### Poin #3: BELUM OPERASIONAL PENUH (R&D Phase)

**Penyebab:**

| Operational Aspect | Current State | Scope Boundary |
|---|---|---|
| Real-time processing | Batch mode (offline) | Research: batch sufficient |
| WhatsApp integration | Manual message copy-paste | Production: API integration needed |
| Validation | Manual human review | Production: automated QA pipeline |
| Monitoring | Ad-hoc testing | Production: observability stack |
| Scale testing | 200-300 orders tested | Production: 1000+ load verified |
| Data recency | Feb-Mar 2026 only | Production: 1+ year patterns |

**Alasan Scope Pembatasan:**

1. **Timeline & Resource**
   - R&D research: 6-8 bulan target
   - Production deployment: 3-6 bulan engineering AFTER research
   - Current project: dalam R&D phase (POC validation)

2. **Validation Strategy**
   - R&D: Manual validation sufficient (quality over speed)
   - Production: Real-time processing requirement incompatible with research timeline
   - Batch processing = acceptable for POC, enables focus on model quality

3. **Data Coverage**
   - Research data: 2 months collected (Feb-Mar 2026)
   - Production validation: 12+ months operational pattern needed
   - Seasonal variation, holiday impact, volume surge: not in dataset yet

**Kekurangan yang jadi Batasan:**
- ❌ TIDAK READY untuk operational deployment
- ❌ TIDAK SCALED ke 1000+ orders volume
- ❌ TIDAK INTEGRATED ke real-time message queue
- ❌ TIDAK COVER long-tail operational edge cases (seasonal, holiday surges)

**Batasan Logis untuk Skripsi:**
```
"Sistem berada dalam fase Research & Development dengan fokus pada validation 
model accuracy dan feasibility, BUKAN production deployment. Oleh karenanya, 
batasan ini mencakup: (1) offline batch processing (bukan real-time streaming); 
(2) manual human validation (bukan automated decision); (3) training data terbatas 
2 bulan (bukan 12+ bulan operational patterns); (4) skala testing 200-300 orders 
(bukan 1000+ load validation). Integration ke operational pipeline dan scale-up 
merupakan fase engineering SETELAH penelitian complete. Scope ini dipilih untuk 
memastikan penelitian fokus pada QUALITY over SCALE pada tahap ini."
```

---

### Poin #4: HANYA EXTRACT DATA WA UNTUK FIELD TERTENTU

**Penyebab:**

| Field Type | Extractable? | Scope Decision | Reason |
|---|---|---|---|
| Date, location, route | ✅ YES (direct text) | IN-SCOPE | Named entity recognition doable |
| Driver name, phone | ✅ YES (direct text) | IN-SCOPE | NER + regex pattern matching |
| Vehicle plate (nopol) | ✅ YES (format pattern) | IN-SCOPE | Rule-based regex + validation |
| Unit type (TWB/CDDL) | ✅ YES (classification) | IN-SCOPE | Entity classification doable |
| SPK number | ❌ NO (not in WA) | OUT-OF-SCOPE | Database lookup required |
| Shipper details | ⚠️ PARTIAL (sometimes in WA) | OUT-OF-SCOPE | Unreliable source (use DB) |
| Pricing | ❌ NO (not in WA) | OUT-OF-SCOPE | Require calculation engine |
| Margin/profitability | ❌ NO (not in WA) | OUT-OF-SCOPE | Business decision logic |

**Alasan Scope Pembatasan:**

1. **What ML Can Extract**
   - Named Entity Recognition (NER): person, location, route, vehicle type
   - Pattern Matching: phone, plate, date, numeric values
   - Semantic Similarity: revision references, partial order matching
   
   **Cannot Extract (No text source):**
   - Database references (SPK, historical orders, shipper master)
   - Business logic (pricing, margin, priority rules)
   - Real-time data (vehicle location, availability)

2. **Data Quality Hierarchy**
   - Most reliable: Direct observable text (driver name, plate, date)
   - Medium reliable: Pattern-based (phone, location - typo variations present)
   - Least reliable: Inferred (shipper from partial clues, business rules)
   - Out-of-scope: Domain knowledge lookups (SPK exists? shipper active?)

3. **Research Scope Tightening**
   - Original requirement: 50+ fields per order
   - Realistically extractable from text: 10-12 fields
   - Choose: **realistic implementation** over **aspirational requirements**

**Kekurangan yang jadi Batasan:**
- ❌ NOT COVERING 50+ field requirement dari database
- ❌ NOT INCLUDING data fusion dari multiple sources
- ❌ NOT EXTRACTING business-critical fields seperti SPK, shipper validation
- ❌ NOT ADDRESSING "why some fields missing" pada output

**Batasan Logis untuk Skripsi:**
```
"Penelitian ini fokus pada ekstraksi 10-12 field YANG DAPAT DIEKSTRAKSI dari 
format unstructured WhatsApp message. Field-field lain (SPK, shipper validation, 
pricing) memerlukan external data source atau business decision logic, yang 
di-separate dari scope text extraction ini. Pembatasan ini INTENTIONAL karena: 
(1) memungkinkan model fokus pada HIGH-QUALITY extraction untuk doable fields; 
(2) menghindari complexity explosion dari data source integration; (3) mendefinisikan 
clear boundary antara 'text extraction research' vs 'enterprise data integration 
engineering'. Implikasi: system output adalah 'structured data + NULL indicators', 
bukan 'complete order record' - downstream processing (database enrichment) 
menangani complementary fields."
```

---

## BAGIAN 3: KEKURANGAN TAMBAHAN (Beyond 4 Poin)

Dari analisis architecture Rafay + project state, ada **2 kekurangan logis tambahan** untuk dijadikan batasan:

### Kekurangan Tambahan #1: MODEL GENERALIZATION (Vendor-Specific Design)

**Konteks:**
- Models trained on Rafay data patterns specifically
- Rule-based layer: Rafay format, Rafay location names, Rafay business logic
- Transfer ke vendor lain: akan butuh retraining + rule recalibration

**Logis jadi Batasan:**
```
"Model dan rule-based layer dirancang KHUSUS untuk karakteristik operasional 
PT. Rafay Logistik, tidak untuk general-purpose logistics extraction. Transfer 
ke vendor lain atau domain berbeda akan memerlukan retraining model dan 
recalibration rule-based layer. Oleh karena itu, kontribusi research ini 
adalah PROOF-OF-CONCEPT untuk domain-specific application engineering, 
BUKAN general-purpose framework development. Generalization merupakan scope 
future work."
```

### Kekurangan Tambahan #2: SEMANTIC REVISION MATCHING (Limited to Available Context)

**Konteks:**
- Partial order + revision matching relies on available text context
- Ambiguity tolerance: 5-10 candidate matches acceptable (disfilter ke top-3 via confidence)
- Some revisions might remain UNRESOLVED jika konteks insufficient

**Logis jadi Batasan:**
```
"Revision matcher menggunakan semantic similarity untuk menghubungkan partial 
order dengan refill messages. Jika context tidak cukup ATAU ambiguity tinggi 
(10+ candidate matches), system meninggalkan revision FLAGGED (tidak force resolution). 
Human operator melakukan final matching decision. Scope penelitian ini TIDAK mencakup 
automatic resolution dari ambiguous case - confidence threshold di-set untuk 
PRECISION over RECALL (false positive expensive, false negative acceptable for 
human review). Aspiration untuk 'auto-resolve semua ambiguity' adalah future 
research, bukan current scope."
```

---

## BAGIAN 4: SYNERGY ANTARA 4 POIN → RESEARCH COHERENCE

Ketika 4 poin Rafay + 2 kekurangan tambahan digabung, mereka membentuk **coherent research scope**:

```
┌─────────────────────────────────────────────────────────┐
│ RESEARCH VISION (Defined by Scope):                    │
│                                                         │
│ "Develop domain-specific ML + rule-based pipeline      │
│  for SEMI-AUTOMATIC extraction dari unstructured       │
│  logistics orders, focusing on QUALITY over SCALE,     │
│  with human-in-the-loop validation for safety-         │
│  critical decisions"                                    │
├─────────────────────────────────────────────────────────┤
│ WHAT WE BUILD:                                          │
│ - Hybrid ML extraction (NER + classifier + matcher)    │
│ - Rule-based refinement (Rafay-specific patterns)      │
│ - Revision linking (semantic matching)                  │
│ - Manual validation UI                                  │
│ - Proof-of-concept pipeline                            │
├─────────────────────────────────────────────────────────┤
│ WHAT WE DON'T BUILD:                                    │
│ - General-purpose framework                            │
│ - Enterprise data integration                          │
│ - Real-time streaming                                  │
│ - Production infrastructure                            │
│ - 12+ month operational validation                      │
│ - Algorithm innovation                                  │
├─────────────────────────────────────────────────────────┤
│ WHY THESE BOUNDARIES:                                   │
│ - Rafay-specific domain: maximize applicability       │
│ - Hybrid approach: practical reality vs pure ML        │
│ - WA-only scope: minimize integration complexity       │
│ - R&D phase: focus on validation not scale             │
│ - Specific fields: realistic extraction vs wishful     │
│ - Vendor-specific: proof-of-concept, not framework     │
│ - Ambiguity tolerance: precision > recall (safety)    │
└─────────────────────────────────────────────────────────┘
```

**Research Contribution:**
```
✅ Applied ML engineering for domain-specific use case
✅ Proof of concept: hybrid ML + rules approach efficacy
✅ Practical pipeline: reduces manual work 2-3 min → <1 min
✅ Baseline models: for future vendors/domains to reference
✅ Real operational data: from 200-300 orders monthly
✅ Production readiness: flagged what's needed for deployment

❌ Algorithm innovation (not research goal)
❌ General-purpose framework (not research goal)
❌ Enterprise scale (future engineering phase)
```

---

## BAGIAN 5: REKOMENDASI PENYUSUNAN BAB 1.4 BATASAN MASALAH

### Struktur Suggested (5-6 Paragraf):

**Paragraf 1 (Opening + Hybrid Philosophy):**
- Penjelasan hybrid ML+rules approach
- WHY: practical necessity untuk Rafay data characteristics
- Konsekuensi: fokus pada application engineering, bukan algo innovation

**Paragraf 2 (Data Source & Field Scope):**
- HANYA extraction dari WhatsApp (not SPK, DB, pricing)
- HANYA 10-12 fields (not 50+ complete record)
- WHY: minimize scope, focus pada text extraction extraction
- Implikasi: output structured data + NULL fields + downstream enrichment

**Paragraf 3 (R&D Phase & Maturity):**
- Batch processing (not real-time)
- Manual validation required (not automated decision)
- 2-month data, 200-300 orders tested (not 12+ month patterns)
- WHY: research timeline vs production requirement trade-off

**Paragraf 4 (Vendor-Specific & Generalization):**
- Rafay-specific training, rules, domain logic
- Transfer ke vendor lain memerlukan retraining
- NOT general-purpose framework
- Implication: contribution adalah POC, not framework

**Paragraf 5 (Revision Matching & Ambiguity):**
- Semantic matching untuk revision linking
- Limited by available context
- Some cases remain unresolved → human review
- WHY: precision > recall (safety-critical decisions)

**Paragraf 6 (Optional - Bridge to Next Chapter):**
- Ringkasan: scope yang tightly defined
- What comes next: literature review (ML, NER, semantic similarity)
- Setup untuk BAB 2

---

## 📌 KEY MESSAGING UNTUK BATASAN MASALAH:

**DON'T SAY:**
- ❌ "We couldn't do X because of limitations"
- ❌ "Project is incomplete, we skipped Y"
- ❌ "Future work includes Z" (apologetic tone)

**DO SAY:**
- ✅ "This research focuses on X, which is strategic because..."
- ✅ "Y is purposefully out-of-scope to enable..."
- ✅ "Z is identified for future engineering phase that..."
- ✅ "This scope design enables..."

**Tone:** Confident, intentional, defensive (in good way - "defending research choices")

