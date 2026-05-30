# 3.1 KERANGKA PEMIKIRAN
## Sistem Ekstraksi Data Berbasis Fine-Tuning IndoBERT untuk PT. Rafay Logistik

---

## Diagram Kerangka Pemikiran Penelitian

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│          KERANGKA PEMIKIRAN METODOLOGI PENELITIAN PT. RAFAY LOGISTIK           │
│        Pengembangan Named Entity Recognition Berbasis Fine-Tuning IndoBERT    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘


                              ┌──────────────────────────┐
                              │  IDENTIFIKASI MASALAH    │
                              ├──────────────────────────┤
                              │ • Ribuan field entry     │
                              │   per bulan (overload)   │
                              │ • Ambiguitas data        │
                              │   susulan (refill/revisi)│
                              │ • Skalabilitas unsustain │
                              │ • Cognitive load tinggi  │
                              └────────────┬─────────────┘
                                          │
                                          ↓
                       ┌──────────────────────────────────────┐
                       │   STUDI LITERATUR &                 │
                       │   TINJAUAN PUSTAKA                  │
                       ├──────────────────────────────────────┤
                       │ • Deep Learning & NLP                │
                       │ • Transformer Architecture           │
                       │ • IndoBERT untuk bahasa Indonesia    │
                       │ • NER (Named Entity Recognition)     │
                       │ • Semantic Similarity & Sequence     │
                       │   Pair Classification                │
                       │ • Metrik Evaluasi (P, R, F1)        │
                       │ • Data Preprocessing & Augmentation  │
                       │ • Penelitian terkait (RESTI, dll)    │
                       └──────────┬───────────────────────────┘
                                  │
                  ┌───────────────┴──────────────────┐
                  │                                  │
                  ↓                                  ↓
    ┌─────────────────────────────┐    ┌──────────────────────────┐
    │  PELATIHAN MODEL AI         │    │ DATA PREPARATION &       │
    │  TAHAP 1: NER EXTRACTION    │    │ PREPROCESSING            │
    ├─────────────────────────────┤    ├──────────────────────────┤
    │ • Model: IndoBERT Base      │    │ • Collection: WhatsApp   │
    │ • Head: Token Classification│    │   JSON (5000+ messages)  │
    │ • Loss: CRF Loss            │    │ • Annotation: Label      │
    │ • Epochs: 3                 │    │   Studio (2000 samples)  │
    │ • Learning Rate: 2e-5       │    │ • Converter: BIO tagging │
    │ • Batch Size: 16            │    │ • Cleaner: Fix errors    │
    │ • Output: 7 entities        │    │ • Augmenter: 3-5x expand │
    │   (ORDER_DATE, UNIT_SPEC,   │    │ • Final: 8000 samples    │
    │    LOCATION, LOAD_TIME,     │    │   (Train/Test: 80/20)    │
    │    ROUTE, DRIVER, PHONE)    │    │                          │
    └────────────┬────────────────┘    └──────────┬───────────────┘
                 │                                  │
                 │ Transfer Learning                │
                 │ (Fine-Tuning)                    │
                 │                                  │
                 └──────────────────┬───────────────┘
                                    │
                  ┌─────────────────┴──────────────────┐
                  │                                    │
                  ↓                                    ↓
    ┌──────────────────────────────┐   ┌──────────────────────────┐
    │ PELATIHAN MODEL AI           │   │ PELATIHAN MODEL AI       │
    │ TAHAP 2A: EVENT CLASSIFIER   │   │ TAHAP 2B: REVISION       │
    │                              │   │ MATCHER                  │
    ├──────────────────────────────┤   ├──────────────────────────┤
    │ • Model: IndoBERT Base       │   │ • Model: IndoBERT Base   │
    │ • Head: Sequence             │   │ • Head: eSequenc-Pair    │
    │   Classification             │   │   Classification         │
    │ • Classes: 4                 │   │ • Classes: 2             │
    │   (NEW_ORDER, REPAIR,        │   │   (MATCH, NO_MATCH)      │
    │    REFILL, NON_ORDER)        │   │ • Input: Pair kalimat    │
    │ • Loss: CrossEntropyLoss     │   │ • Task: Semantic matching│
    │ • Purpose: Message routing   │   │ • Purpose: Data          │
    │ • Threshold: 0.75            │   │   reconciliation         │
    │                              │   │ • Threshold: 0.58        │
    └────────────┬─────────────────┘   └──────────┬───────────────┘
                 │                               │
                 │                               │
                 └──────────────┬────────────────┘
                                │
                                ↓
                  ┌──────────────────────────────┐
                  │  PENGUJIAN & EVALUASI        │
                  ├──────────────────────────────┤
                  │ • Metrics:                   │
                  │   - Precision, Recall, F1   │
                  │   - Accuracy (per model)    │
                  │   - Confusion Matrix        │
                  │ • Test Set: 20% data        │
                  │ • Per-Entity Evaluation     │
                  │   (7 entity types)          │
                  │ • End-to-End Test:          │
                  │   30 orders (Day 1 + Day 2) │
                  │ • Success Criteria:         │
                  │   F1 ≥ 0.85, Matching ≥90% │
                  │ • Error Analysis            │
                  │ • Ablation Studies          │
                  └────────────┬─────────────────┘
                               │
                               ↓
                  ┌──────────────────────────────┐
                  │  INTEGRASI SISTEM WEB        │
                  ├──────────────────────────────┤
                  │ • Framework: Streamlit       │
                  │ • Backend: Python Flask      │
                  │ • Database: SQLite           │
                  │ • Pipeline Inference:       │
                  │   - Batch processing        │
                  │   - Smart text splitting    │
                  │   - Event routing           │
                  │   - Conditional execution   │
                  │ • Post-Processing:          │
                  │   Rule-based standardization│
                  │ • Output: Excel export      │
                  │ • Persistence: Database     │
                  │ • Monitoring: Metrics track │
                  └──────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════

## Penjelasan Alur Kerangka Pemikiran

### Fase 1: IDENTIFIKASI MASALAH
Penelitian dimulai dengan mengidentifikasi tiga masalah operasional utama di PT. Rafay 
Logistik yang terkait dengan pengelolaan data pesanan:

1. **Beban Entri Data Manual**: Dua admin mengelola ribuan field entry per bulan dari 
   pesan WhatsApp tidak terstruktur, mengakibatkan penumpukan pekerjaan dan cognitive 
   load tinggi.

2. **Ambiguitas Data Susulan**: Pesan refill (data lengkap) dan revisi diterima tanpa 
   rujukan eksplisit order induk, menyebabkan pencocokan data manual yang rentan error.

3. **Keterbatasan Skalabilitas**: Dengan rencana ekspansi bisnis, volume pesanan akan 
   melampaui kapasitas manual, menciptakan bottleneck operasional yang unsustainable.

Masalah ini membutuhkan solusi berbasis teknologi yang menggabungkan kemampuan deep 
learning untuk pemahaman bahasa alami dengan business logic rules untuk standarisasi.

---

### Fase 2: STUDI LITERATUR & TINJAUAN PUSTAKA
Setelah identifikasi masalah, dilakukan review komprehensif terhadap:

**Landasan Teori Teknis:**
- Deep Learning dan arsitektur neural networks untuk NLP
- Transformer architecture dengan mekanisme self-attention
- IndoBERT sebagai pre-trained model khusus bahasa Indonesia
- Named Entity Recognition (NER) untuk ekstraksi entitas
- Semantic Similarity dan Sequence-Pair Classification
- Metrik evaluasi standar (Precision, Recall, F1-Score)
- Data preprocessing dan augmentation techniques

**Penelitian Terkait:**
- RESTI: Indonesian news classification menggunakan Word2Vec + K-NN
- Penelitian lain: NER via RNN, semantic matching, dll.
- Comparison dengan metode konvensional (rule-based, statistical)

**Gap Analisis:**
Penelitian terdahulu sebagian besar fokus pada teks formal (news, social media umum) 
dengan single-task models. Project Rafay inovatif karena:
- Domain spesifik: pesan operasional logistik (informal, jargon tinggi)
- Dual-task: NER (token-level) + semantic matching (sentence-level)
- Practical implementation: human-in-the-loop system untuk production

---

### Fase 3: PELATIHAN MODEL AI — TAHAP 1 (NER EXTRACTION)
Berdasarkan literature review, dipilih pendekatan **Fine-Tuning IndoBERT** untuk dua 
alasan utama:

**Transfer Learning Rationale:**
- Limited labeled data (~2000 samples) → fine-tuning optimal vs training scratch
- IndoBERT sudah pre-trained pada 220M Indonesian text tokens
- Efficient: 3 epochs, 2-4 jam training (vs weeks from scratch)

**Model Architecture (NER):**
```
Input: Pesan WhatsApp mentah
       "3 UNIT TWB Lokasi ARGOPANTES Waktu SEGERA"
         ↓
       Tokenization (WordPiece subword tokens)
         ↓
       IndoBERT Encoder (12 layers, self-attention)
       [CLS] 3 UNIT TWB Lokasi ARGOPANTES Waktu SEGERA [SEP]
         ↓
       Token Classification Head (768 → num_classes)
         ↓
       CRF Decoder (ensure valid BIO sequences)
         ↓
       Output: {
         ORDER_DATE: "tidak ada",
         UNIT_SPEC: "3 UNIT TWB",
         LOCATION: "ARGOPANTES",
         LOAD_TIME: "SEGERA",
         ROUTE: "tidak ada",
         DRIVER: "tidak ada",
         PHONE: "tidak ada"
       }
```

**Hyperparameter Configuration:**
- Batch Size: 16 (GPU memory constraint)
- Epochs: 3 (sufficient untuk fine-tuning)
- Learning Rate: 2e-5 (conservative, preserve pre-trained weights)
- Warmup: 10% dari total steps
- Loss Function: CRF loss (ensures valid tag transitions)

---

### Fase 3: DATA PREPARATION & PREPROCESSING (Parallel)
Secara paralel dengan training, data dipersiapkan melalui pipeline:

**Data Collection (Oktober 2025 - Maret 2026):**
- Sumber: WhatsApp operasional PT. Rafay (raw JSON export)
- Volume: 5000+ messages
- Metadata: timestamp, sender, message body

**Data Annotation (Manual):**
- Tool: Label Studio (open-source annotation platform)
- Domain Expert: 2-3 admin PT. Rafay (understand jargon spesifik)
- Task: Span-level entity labeling untuk 7 entitas
- Output: Character-level spans dengan entity type labels
- Effort: ~65 jam annotation untuk 2000 messages

**Data Preparation Pipeline:**
1. **Converter**: Transform Label Studio JSON → BIO format
   - Align character spans dengan token boundaries
   - Handle overlapping/nested entities
   
2. **Cleaner**: Fix annotation errors & inconsistencies
   - Phone number correction (08xxx format validation)
   - Date format normalization
   - Remove stutters & typos dari tokens
   - Re-tag mislabeled entities
   
3. **Augmenter**: Generate synthetic variations
   - Synonym replacement (WordNet-based)
   - Back-translation (ID ↔ EN)
   - Token shuffling (entity-aware)
   - Goal: 3-5x expansion (2K → 8K samples)

**Final Dataset:**
- Training set: 6400 samples (80%)
- Test set: 1600 samples (20%)
- Total: 8000 labeled examples ready for training

---

### Fase 4: PELATIHAN MODEL AI — TAHAP 2A (EVENT CLASSIFIER)
Model kedua dikembangkan untuk **routing decision**: Apa tipe pesan ini?

**Necessity:**
- Tidak semua pesan adalah order baru
- Ada REPAIR (revisi data) dan REFILL (data lengkap susulan)
- Ada NON_ORDER (chat sampah)
- Smart routing → efficient pipeline execution

**Model Architecture:**
```
Input: Single message text
       "Driver SUTRISNO ganti WAHYUDI"
         ↓
       IndoBERT Encoder
       [CLS] Driver SUTRISNO ganti WAHYUDI [SEP]
         ↓
       [CLS] token pooling (768D vector)
         ↓
       Sequence Classification Head (768 → 4 classes)
         ↓
       Softmax probabilities:
       {
         NEW_ORDER: 0.05,
         REPAIR: 0.85,
         REFILL: 0.08,
         NON_ORDER: 0.02
       }
         ↓
       Decision: REPAIR > threshold (0.75) ✓ → Route to Revision Matcher
```

**Purpose & Application:**
- NEW_ORDER (0.85+) → Route ke NER pipeline
- REPAIR/REFILL (0.75+) → Route ke Revision Matcher
- NON_ORDER atau low confidence → Manual review flag

---

### Fase 4: PELATIHAN MODEL AI — TAHAP 2B (REVISION MATCHER)
Model ketiga menggunakan **Sequence-Pair Classification** untuk semantic matching.

**Problem it solves:**
- Pesan revisi: "Driver SUTRISNO ganti WAHYUDI" — siapa yang dimaksud?
- Perlu mencari order parent dari last 3 days
- Compute semantic similarity dengan setiap candidate
- Rank dan select best match

**Model Architecture:**
```
Input: Pair kalimat
       text_1: "Driver SUTRISNO ganti WAHYUDI"
       text_2: "Order #123: 3 UNIT TWB, Driver SUTRISNO, CGK-SUB"
         ↓
       Tokenization (paired format)
       [CLS] text_1 [SEP] text_2 [SEP]
            └ token_type=0 ┘└ token_type=1 ─┘
       
       (Token type IDs inform model: "ini dua teks yang dibandingkan")
         ↓
       IndoBERT Encoder (joint representation)
         ↓
       Sequence-Pair Classification Head (768 → 2 classes)
         ↓
       Output probabilities:
       {
         MATCH: 0.78,
         NO_MATCH: 0.22
       }
```

**Candidate Ranking Pipeline:**
```
Incoming revision: "Driver SUTRISNO ganti WAHYUDI"
Query database: Orders dari last 3 days (50+ candidates)
                └─ Status INCOMPLETE (missing fields)
  ↓
For each candidate order:
  score(revision, candidate) → match_probability
  ↓
Sort by match_probability DESC
  ↓
Filter candidates:
  ✓ match_probability > 0.58
  ✓ gap between top-2 > 0.05 (avoid ambiguity)
  ↓
Output: Ranked list dengan confidence per rank
        [{order_id: 123, score: 0.78, rank: 1},
         {order_id: 456, score: 0.62, rank: 2},
         ...]
```

---

### Fase 5: PENGUJIAN & EVALUASI
Semua tiga model dievaluasi secara terpisah dan terintegrasi.

**Metrik Evaluasi per Model:**

1. **NER Model:**
   - Per-entity metrics: Precision, Recall, F1-Score
   - Confusion matrix (27 classes: B/I tags + O)
   - Expected F1-score: ≥ 0.85 (success threshold)
   - Ranking difficulty: PHONE (easy, 0.94) > LOAD_TIME (hard, 0.82)

2. **Event Classifier:**
   - Accuracy overall
   - Per-class Precision/Recall/F1
   - ROC-AUC untuk setiap class
   - Expected Accuracy: ≥ 0.85

3. **Revision Matcher:**
   - Accuracy: Berapa % rank-1 adalah correct match?
   - MRR (Mean Reciprocal Rank): Average ranking quality
   - Expected: ≥ 90% correct at top-1, 95%+ at top-3

**End-to-End Testing:**
- Test case: 30 orders (15 new orders day 1 + 15 revisions day 2)
- Success criteria: ≥ 97.8% fields correct, ≥ 93% revision matching
- Error analysis: Document failure modes dan causes
- Ablation studies: Impact of augmentation, CRF, thresholds

---

### Fase 6: INTEGRASI SISTEM WEB
Model-model yang sudah dilatih dan dievaluasi diintegrasikan ke dalam sistem 
production-ready.

**Arsitektur Deployment:**

**Frontend (User Interface):**
- Framework: Streamlit (rapid UI development)
- Features:
  - CSV upload (WhatsApp export)
  - Real-time extraction preview
  - Database query interface
  - Model management (version selection, threshold tuning)
  - Excel export functionality

**Backend (Inference Pipeline):**
```
Raw Chat Upload
    ↓
Batch Processor
  ├─ Smart text splitting (header-aware)
  ├─ Multi-unit detection
  └─ Junk filtering
    ↓
Event Classifier
  └─ Route to appropriate pipeline
    ↓
    ├─ IF NEW_ORDER:
    │   └─ NER Inference
    │       ├─ Extract 7 entities
    │       └─ Confidence scoring
    │
    └─ IF REPAIR/REFILL:
        └─ Revision Matcher Inference
            ├─ Query candidate pool
            ├─ Score & rank
            └─ Return best match
    ↓
Post-Processing Layer (Rule-based)
  ├─ Date format standardization
  ├─ Phone number cleanup
  ├─ Location code mapping
  ├─ Driver blacklist check
  └─ Timestamp normalization
    ↓
Database Persistence (SQLite)
  ├─ order_rows table (main records)
  ├─ chat_history table (audit trail)
  ├─ revision_log table (tracking updates)
  └─ model_metadata table (version tracking)
    ↓
Output Export (CSV/Excel)
  └─ Admin-friendly format untuk downstream tasks
```

**Key Features:**
- **Conditional Execution**: Only use models yang needed (efficient)
- **Confidence Scoring**: Each output tagged dengan confidence
- **Fallback Handling**: Low confidence → manual review flag
- **Persistence**: Database storage untuk audit & replay
- **Monitoring**: Track model performance over time

---

## Inovasi Metodologi

Kerangka pemikiran ini menghadirkan beberapa inovasi dalam metodologi penelitian:

### 1. Dual-Model Architecture (vs Single Unified)
- **Alasan**: NER (token-level) berbeda task dari classification (document-level)
- **Benefit**: Better specialization, independent versioning, conditional efficiency
- **Trade-off**: Slight system complexity untuk better production performance

### 2. Event-Driven Routing (vs Pipeline Monolitik)
- **Alasan**: Tidak semua pesan memerlukan semua processing steps
- **Benefit**: GPU-efficient, faster inference for non-order messages
- **Impact**: Scalable untuk high-volume message processing

### 3. Hybrid DL + Rule-Based (vs Pure DL)
- **Alasan**: DL handles linguistic complexity, rules handle business logic
- **Benefit**: Explainability, deterministic standardization, production robustness
- **Balance**: Automation dengan control

### 4. Domain-Specific Data Augmentation
- **Alasan**: Limited labeled data (2K) untuk training model spesifik domain
- **Technique**: Paraphrase, back-translation, entity-aware shuffling
- **Result**: Effective 3-5x data expansion tanpa manual annotation

---

## Kontribusi Metodologi Terhadap Penelitian NLP Terapan

1. **Practical Transfer Learning**: Demonstrasi effective knowledge transfer dari 
   general pre-trained model ke domain logistik spesifik dengan limited data

2. **Sequence-Pair Classification untuk Data Reconciliation**: Innovative use case 
   semantic similarity untuk automatic matching of related messages (revision ↔ order)

3. **End-to-End NLP System Architecture**: Framework lengkap dari data collection, 
   annotation, training, evaluation, hingga production deployment

4. **Evaluation Methodology**: Comprehensive testing strategy yang mencakup per-entity 
   metrics, end-to-end scenarios, dan error analysis

---

**Gambar 3.1**: Diagram Kerangka Pemikiran Penelitian PT. Rafay Logistik 
(Lihat halaman sebelumnya untuk visual flowchart)

---

*Sub-Bab 3.1 selesai. Lanjut ke 3.2 untuk detail Metode AI yang Digunakan.*
