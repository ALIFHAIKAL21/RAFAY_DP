# 📋 BLUEPRINT LENGKAP BATASAN MASALAH (BAB 1.4)
## Scope Definition untuk Hybrid ML Rafay IDP v2.0

**Status:** Blueprint Komprehensif  
**Konteks:** 4-point user context + business process + project limitation + research scope  
**Output:** Batasan masalah 6-8 poin logis + Gemini prompt master  
**Target:** BAB 1.4 Batasan Masalah (4-6 paragraf akademis)

---

## BAGIAN 1: ANALISIS 4-POINT CONTEXT USER

### Point #1: Hybrid Approach (ML + Rule-Based)
**Implikasi untuk Batasan Masalah:**
- ✅ **Scope INCLUDED:** ML model (NER + Revision Matcher), rule-based refinement layer
- ❌ **Scope EXCLUDED:** Pure rule-based system, pure ML system, general-purpose BERT tuning
- **Batasan:** Project adalah HYBRID approach, bukan pure ML advancement—komponen rule-based untuk standardisasi format adalah BAGIAN INTEGRAL dari solution, bukan sekadar post-fix

**Kekurangan Terkait:**
- Rule-based component belum seamlessly integrated dengan ML (masih separate pipeline)
- Logic rules tidak data-driven, masih manual best-guess (e.g., format standardization, phone validation rules)
- Tidak ada feedback loop dari production errors ke rule-updating mechanism
- **Batasan Logis:** Penelitian fokus pada ML component effectiveness, rule-based hanya sebagai supporting layer, bukan optimization focus

---

### Point #2: ML Capabilities Spesifik untuk Rafay
**Implikasi untuk Batasan Masalah:**
- ✅ **Scope INCLUDED:** Framework designed untuk WhatsApp unstructured data dari Rafay
- ✅ **Scope INCLUDED:** 21 entity types dari order structure Rafay (driver, nopol, phone, route, etc)
- ❌ **Scope EXCLUDED:** Multi-operator generalization, cross-industry adaptation, different order structure
- **Batasan:** Model bukan untuk general-purpose logistics, spesifik untuk Rafay order characteristics

**Kekurangan Terkait:**
- Training data hanya Rafay (200-300 orders/month) → bias operator spesifik
- Entity label set (21 types) ONLY valid untuk Rafay order format
- Driver names, routes, locations patterns spesifik Rafay
- Language style dalam WhatsApp berbeda tiap driver
- **Batasan Logis:** Model tidak generalizable ke operator lain atau struktur order berbeda; hasil validasi hanya applicable untuk Rafay's operational context

---

### Point #3: Project Belum Operational-Ready
**Implikasi untuk Batasan Masalah:**
- ✅ **Scope INCLUDED:** Prototype/MVP phase (model + pipeline architecture)
- ❌ **Scope EXCLUDED:** Production deployment, scalability optimization, real-time integration
- ❌ **Scope EXCLUDED:** Business workflow integration, user interface, system reliability testing
- ❌ **Scope EXCLUDED:** Integration dengan SPK system, driver management system, inventory system
- **Batasan:** Penelitian TIDAK mencakup operational deployment readiness

**Kekurangan Terkait:**
- Belum error handling comprehensive untuk edge cases di production
- Testing terbatas pada historical data, belum live streaming validation
- Model accuracy tested on batch data, belum on real-time operational stress
- Belum clear metric untuk "success" di operational setting
- Pipeline belum optimized untuk speed requirements (<1 min per order)
- **Batasan Logis:** Accuracy metrics berbasis historical test set, implementation feasibility untuk production bukan scope (recommend by separate operational integration research)

---

### Point #4: Data dari WhatsApp Only, Field-Specific
**Implikasi untuk Batasan Masalah:**
- ✅ **Scope INCLUDED:** WhatsApp unstructured text extraction (21 fields)
- ❌ **Scope EXCLUDED:** Data dari SPK, payment system, assignment system, delivery tracking
- ❌ **Scope EXCLUDED:** Cross-system data reconciliation, data from multiple sources
- ❌ **Scope EXCLUDED:** Fields yang require real-time external validation (e.g., driver availability, unit allocation)
- **Batasan:** Ekstraksi terbatas pada WhatsApp text, data source lain diassumsikan provided separately

**Kekurangan Terkait:**
- Tidak ada validation terhadap consistency dengan SPK system (jika ada)
- Jika field redundant across system, ambiguity tidak di-resolve (hanya WA considered)
- Missing fields dari WA → sistem gap, tidak di-handle oleh research
- Asumsi: Admin sudah de-duplicate/reconcile data dari system lain sebelum masuk ke pipeline
- **Batasan Logis:** Scope penelitian adalah ekstraksi dari single unstructured source (WA), multi-source data fusion adalah separate problem (recommend by data integration research)

---

## BAGIAN 2: KEKURANGAN/LIMITASI DARI RAW DATA CHARACTERISTICS

Dari analisis raw.txt, identifikasi limitasi yang menjadi batasan logis:

### Limitasi 1: Data Incompleteness Pattern
**Pattern dari raw.txt:**
```
Waktu loading : 18:00
Rute/tujuan : CGK - SUB
driver  :           ← EMPTY/PARTIAL
Nopol  :            ← EMPTY/PARTIAL
No hp  :            ← EMPTY/PARTIAL
```

**Implikasi:**
- Revisi/refill sering informasi incomplete di initial request
- Admin akan send multiple messages, sometimes days apart
- Matching incomplete order dengan revisi message adalah CORE problem
- Namun TIDAK semua incomplete fields bisa di-resolve dari revision messages
- **Batasan:** Jika field tidak ada di WA message (e.g., admin belum provide driver info), sistem tidak bisa extract—assume admin responsibility untuk provide info sebelum loading time

### Limitasi 2: Typo & Format Variation Severity
**Pattern dari raw.txt:**
```
No hp  :+62 877-8667-6177    ← Format 1
No hp  :+62 889-0702-0037    ← Format 2
NOHP      :0882016641381     ← Format 3 (no +62)
NO HP : 089690885555         ← Format 4 (no prefix)
```

**Implikasi:**
- Format standardization critical tapi tidak 100% reliable
- Rule-based phone normalization akan have edge cases
- Phone validation bisa reject valid number (e.g., local format vs international)
- **Batasan:** Standardisasi format terbatas pada pattern dari training data; edge case format variation akan raise flagged untuk manual review

### Limitasi 3: Revision/Refill Ambiguity Ceiling
**Pattern dari raw.txt:**
```
[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL 13 FEBRUARI 2026: [5-unit request]
[05.31, 7/3/2026] Akbar Rafay: REQUEST ORDER ONCALL ULANG 13 FEBRUARI 2026: [3-unit revisi]
```

**Challenge:**
- Timestamp semua messages lebih awal (05:31), request untuk 13 Feb dikirim 7 Mar
- Multiple orders same destination, same day, different time
- Revision message minimal context ("REVISI DRIVER: UMAR ALI, B 9932 SXW")
- Top-3 matching bisa return false positives jika 3+ candidate similar

**Implikasi:**
- Semantic matching belum bisa 100% resolve ambiguity
- Jika 3+ kandidat equally likely → admin manual pick required
- **Batasan:** Revision Matcher output adalah TOP-3 RECOMMENDATIONS, final selection tetap admin responsibility; accurate matching ceiling dibatasi oleh information richness di revision message

### Limitasi 4: Multi-Unit Handling Incomplete
**Pattern dari raw.txt:**
```
5 UNIT TWB 50 CBM
Waktu loading : SEGERA
...
Waktu loading : 18:00
driver  : HERMAN
Nopol  : B 9718 TJ
...
Waktu loading : 18:00
driver  : FAJRI
Nopol  : ...            ← Sometimes incomplete for later units
```

**Challenge:**
- Multi-unit order dengan staggered loading times & drivers
- Sometimes only first unit fully specified
- Later units inherit some fields atau left incomplete
- Revisi bisa modify only specific unit, not whole order

**Implikasi:**
- Field extraction per unit kompleks (need to parse hierarchical structure)
- Handling not all combinations covered in training data
- **Batasan:** Project fokus pada extraction accuracy untuk first/fully-specified unit; handling complex multi-unit scenarios dengan incomplete fields di-flag untuk manual completion

---

## BAGIAN 3: TECHNOLOGY & APPROACH LIMITATIONS

### Limitation 1: InDoBERT Base Model Constraint
- Model base: `indolem/indobert-base-uncased` (NER) dan `indobenchmark/indobert-base-p2` (Revision Matcher)
- Tidak custom-trained dari scratch, menggunakan transfer learning
- Token length limit: 128 (NER), 256 (Revision Matcher) → long messages bisa truncated
- Bidirectional context membantu tapi belum perfect untuk entity ambiguity
- **Batasan:** Model architecture design pilihan existing pre-trained model; advanced architecture (RoBERTa, DeBERTa) tidak di-explore

### Limitation 2: Training Data Scale
- Training data: ~200-300 orders/month, asumsi 6-12 bulan data = 1200-3600 orders
- Small dataset → high variance di performance metrics, potential overfitting
- Underrepresented patterns (e.g., rare routes, unusual driver names) akan low recall
- **Batasan:** Model performance hanya valid pada data distribution similar to training set; generalization ke future data dengan different patterns tidak guaranteed

### Limitation 3: Evaluation Metric Simplification
- Accuracy metric untuk NER: precision, recall, F1 score per entity type
- TIDAK ada business-level metric (e.g., order processing success rate, admin time saved)
- Evaluation only on historical batch data, tidak on production stream
- **Batasan:** Performance metric academic-focused, business impact measurement di-defer ke operational phase

### Limitation 4: Rule-Based Logic Brittleness
- Rule-based standardization terlalu rigid untuk edge cases
- Mapping driver names, location aliases MANUAL maintained—tidak scalable
- Tidak ada declarative rule framework, hard-coded logic di code
- **Batasan:** Rule logic tidak generalizable outside Rafay; scaling ke operator lain require manual rule re-engineering

---

## BAGIAN 4: OPERATIONAL INTEGRATION GAPS

### Gap 1: External System Integration
- **Excluded:** Integration dengan SPK system (order ID clash resolution)
- **Excluded:** Integration dengan driver management system (real-time availability)
- **Excluded:** Integration dengan vehicle allocation system (unit availability)
- **Excluded:** Integration dengan payment/billing system
- **Batasan:** Project fokus pada EXTRACTION & MATCHING dari WhatsApp; external data reconciliation assumed di-handle oleh integration layer (separate study)

### Gap 2: Real-Time Validation
- Model trained & tested on batch historical data
- Real-time decision making (e.g., accept order vs reject) tidak covered
- SLA compliance (order processing <1 min) tidak rigorously tested
- **Batasan:** Project deliverable adalah model + pipeline; operational deployment & performance validation di environment live adalah separate integration research

### Gap 3: Feedback Loop & Continuous Learning
- Model aksuracy evaluated one-time (post-training)
- Tidak ada mechanism untuk model re-training dengan production data
- Error analysis & correction feedback tidak feed back ke model
- **Batasan:** Model adalah STATIC post-training; continuous improvement assumption scope di-defer ke MLOps phase

---

## BAGIAN 5: RESEARCH SCOPE DELIMITATION (BATASAN MASALAH FINAL)

### **BATASAN MASALAH #1: Data Source Specificity**
Project membatasi ekstraksi data HANYA dari pesan WhatsApp tidak terstruktur yang diterima oleh Rafay Operations. Data dari sumber lain (SPK system, driver assignment, vehicle allocation) diasumsikan tersedia melalui channel terpisah dan TIDAK merupakan bagian dari ekstraksi penelitian. Integration data multi-source adalah scope terpisah yang di-recommend untuk penelitian lanjutan.

### **BATASAN MASALAH #2: Entity Set Specificity**
Named Entity Recognition dioptimalkan untuk EXACTLY 21 entity types dari order structure Rafay (terdiri dari: Date, Time, Location, Route, Vehicle Type, Unit Quantity, Driver Name, Vehicle Plate, Phone Number, dan varian field lainnya). Model TIDAK divalidasi untuk struktur order berbeda atau entitas jenis lain; transfer learning ke operator logistics lain require re-training & re-validation terpisah.

### **BATASAN MASALAH #3: Operational Readiness Exclusion**
Penelitian fokus pada model accuracy & pipeline architecture validation melalui historical test data. Aspek TIDAK termasuk dalam scope:
- Real-time operational deployment & monitoring
- Performance validation under production load
- Business workflow integration & user interface design
- System reliability, error recovery, & graceful degradation
- Scalability untuk volume order di atas 300/bulan
Operational integration readiness adalah scope untuk implementation research terpisah.

### **BATASAN MASALAH #4: Revision Matching Advisory Scope**
Revision Matcher component menyediakan TOP-3 RECOMMENDATIONS untuk kandidat order yang mungkin. Keputusan final matching adalah RESPONSIBILITY admin (tidak otomatis). Project tidak mengcover:
- Decision support algorithm untuk auto-selection dari 3 candidate terbaik
- Ambiguity resolution ketika top-3 confidence scores sama
- Revision history tracking & multi-step revision reconciliation
Final selection logic & business rule enforcement adalah scope untuk business logic layer research terpisah.

### **BATASAN MASALAH #5: Incomplete Data Completion Limitation**
Project fokus pada EKSTRAKSI informasi yang TERSEDIA dari pesan WhatsApp. Jika suatu field tidak terdapat di pesan initial request atau revision message:
- Project TIDAK include missing data imputation atau inference dari external source
- Admin TETAP responsible untuk provide informasi missing sebelum order processing
- Pipeline output akan flag incomplete records untuk manual admin verification
Missing data handling adalah scope untuk data acquisition & business workflow design research.

### **BATASAN MASALAH #6: Transfer Learning Architecture**
Project menggunakan architecture pre-trained EXISTING (InDoBERT base) dengan fine-tuning pada Rafay data, BUKAN designing custom architecture. Advanced architecture exploration (RoBERTa, DeBERTa, multi-head attention variants) TIDAK termasuk scope research; focus adalah maximizing efficacy dari standard architecture untuk domain spesifik Rafay. Architecture innovation adalah scope untuk future deep learning advancement study.

### **BATASAN MASALAH #7: Rule-Based Component Pragmatism**
Rule-based post-processing layer adalah PRAGMATIC necessity untuk handling Rafay's operational characteristics (format variation, typo patterns, location aliases), BUKAN research contribution. Rule logic TIDAK di-generate automatically; rules adalah MANUAL-crafted berdasarkan historical pattern observation. Declarative rule framework & automatic rule learning adalah scope untuk advanced knowledge engineering research.

### **BATASAN MASALAH #8: Evaluation Metric Academic Focus**
Performance evaluation menggunakan standard NLP metrics (precision, recall, F1-score) pada historical test set. Business-level impact metrics (order processing time, admin effort reduction, error rate improvement) NOT included dalam research evaluation; assumption adalah incremental improvements di extraction accuracy translate ke operational benefit. Business impact measurement & ROI analysis adalah scope untuk business case research terpisah.

---

## BAGIAN 6: CORRELATION DENGAN BUSINESS PROCESS RAFAY

### Batasan #1 ↔ WhatsApp Centrality
PT. Rafay saat ini menggunakan WhatsApp sebagai SINGLE ORDER CHANNEL dari klien. Mengekstrak dari WhatsApp adalah realistic—jika future di-pivot ke web portal atau API, scope batasan ini tetap valid (project bisa di-adapt ke new source dengan re-training).

### Batasan #2 ↔ Order Structure Consistency
Rafay's order format CONSISTENT di WhatsApp (structure repeatable: unit qty, location, time, route, driver, plate, phone). Memilih 21 entity adalah result dari business analysis—jika klien add new field type, model perlu retraining (not incremental adaptation).

### Batasan #3 ↔ Current Operational Constraints
Rafay currently punya 2 admin + 10-15 drivers untuk 200-300 orders/month. Project adalah OPTIMIZATION untuk current team, NOT replacement. Admin tetap di loop untuk verification/approval—"operational readiness" bukan priority at this stage (optimization untuk 500+ orders adalah future phase).

### Batasan #4 ↔ Revision Message Ambiguity Reality
Real pattern dari WhatsApp: revision messages minimal, sometimes hanya "REVISI DRIVER: Umar Ali, B 9932 SXW". TOP-3 recommendations realistic—admin tetap pick correct one (bukan full automation, tapi REDUCE dari 5-10 manual options to 3 predicted high-probability options).

### Batasan #5 ↔ Data Input Workflow
Current workflow: Order dari klien → incomplete di input → follow-up ke klien jika missing info → finalisasi. Project DOESN'T change ini—assume admin ensure all required field before order processing. Missing data flagging adalah SUPPORT untuk existing workflow (tidak fundamental change).

### Batasan #6 ↔ Technology Maturity
Rafay tidak ada in-house ML team. Using existing pre-trained model (InDoBERT) pragmatic—research scope adalah fine-tuning & application, NOT building foundation model (which require massive compute/data infrastructure Rafay doesn't have).

### Batasan #7 ↔ Operational Common-Sense Rules
Rafay admins already know "phone format standardization", "location alias consistency", "vehicle plate format". Rule-based layer adalah CODIFICATION dari existing manual logic, NOT new science.

### Batasan #8 ↔ Business Decision Making
PT. Rafay will decide ROI based on: time saved per admin (5 min → <1 min = 80% efficiency), error rate reduction (5-8% → ~1% = accuracy improvement). Project provides technical metrics; business decision is management responsibility.

---

## BAGIAN 7: RESEARCH SCOPE BOUNDARY VISUALIZATION

```
┌─────────────────────────────────────────────────────────┐
│                     BATASAN MASALAH                      │
│              Research Scope Define Clearly               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ✅ IN SCOPE:                      ❌ OUT OF SCOPE:       │
│  ├─ WhatsApp extraction            ├─ SPK integration    │
│  ├─ 21-entity NER                  ├─ Driver allocation  │
│  ├─ 2-model hybrid approach        ├─ Real-time OPS      │
│  ├─ Rule-based refinement          ├─ Production deploy  │
│  ├─ Historical batch testing       ├─ User interface     │
│  ├─ Accuracy metric (F1, prec)     ├─ Scalability >500   │
│  ├─ Top-3 revision matching        ├─ Auto-matching      │
│  └─ Model fine-tuning              └─ Continuous learn   │
│                                                           │
│  Fokus di apa yang SUDAH ada atau dapat dicontrol       │
│  Defer kompleksitas integrasi ke future phase            │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## BAGIAN 8: SUMMARY LOGIC DARI 4-POINT USER + BATASAN

| User Point | Implikasi Batasan | Batasan Logis yang Dihasilkan |
|-----------|------------------|-------------------------------|
| #1: Hybrid ML+Rule | Tidak pure ML advancement | #1 Data Source + #7 Rule logic |
| #2: Rafay-Specific | Tidak general-purpose | #2 Entity Set + #6 Transfer Learning |
| #3: Not Operational | Prototype phase only | #3 Operational Readiness + #4 Advisory |
| #4: WA data only | Single source extraction | #1 Data Source + #5 Incomplete Data |
| **Kekurangan** | **Ambiguity/scale/edge** | **#4 Matching Advisory + #5 Completion** |

---

## BAGIAN 9: BATASAN MASALAH FINAL COUNT

**Total: 8 Batasan Masalah Logis & Defensible**

1. ✅ Data Source Specificity (WhatsApp only)
2. ✅ Entity Set Specificity (21 types Rafay)
3. ✅ Operational Readiness Exclusion (Prototype phase)
4. ✅ Revision Matching Advisory Scope (Top-3 recommendation)
5. ✅ Incomplete Data Completion Limitation (Admin responsibility)
6. ✅ Transfer Learning Architecture (Pre-trained model only)
7. ✅ Rule-Based Component Pragmatism (Manual-crafted rules)
8. ✅ Evaluation Metric Academic Focus (Precision recall F1)

---

## BAGIAN 10: NEXT STEP - PROMPT MASTER UNTUK GEMINI

[LIHAT FILE BERIKUTNYA: PROMPT_GEMINI_BATASAN_MASALAH_FINAL_BLUEPRINT.md]

Prompt master akan mengkonversi 8 batasan di atas menjadi 4-6 paragraf akademis natural untuk BAB 1.4.

---

**STATUS:** Blueprint Lengkap Ready for Prompt Generation ✅
