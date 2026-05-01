# 3.3 MODEL PENGEMBANGAN SISTEM
## Analisis Model Pengembangan Berdasarkan Kerangka Pemikiran PT. Rafay

---

## 1. Analisis Karakteristik Kerangka Pemikiran

Berdasarkan kerangka pemikiran sub-bab 3.1, sistem PT. Rafay memiliki karakteristik:

```
Fase 1: IDENTIFIKASI MASALAH
    ↓ (Sekuensial)
Fase 2: STUDI LITERATUR
    ↓ (Sekuensial)
Fase 3A: TRAINING MODEL TAHAP 1 (NER)
    ↓ (Paralel dengan 3B)
Fase 3B: DATA PREPARATION
    ↓ (Konvergen ke fase 4)
Fase 4A: TRAINING MODEL TAHAP 2A (Event Classifier)
    ↓ (Paralel dengan 4B)
Fase 4B: TRAINING MODEL TAHAP 2B (Revision Matcher)
    ↓ (Konvergen ke fase 5)
Fase 5: PENGUJIAN & EVALUASI (Iteratif jika perlu refinement)
    ↓ (Conditional: PASS atau refinement loop)
Fase 6: INTEGRASI SISTEM WEB (Deployment)
```

**Karakteristik Utama:**
- ✓ Fase-fase yang **terstruktur dan jelas** (6 fase besar)
- ✓ Ada **proses paralel** (training vs data preparation)
- ✓ Ada **iterasi lokal** (validation → refinement → re-training)
- ✓ Ada **quality gates** di setiap fase (success criteria)
- ✓ Fokus pada **testing & evaluation komprehensif**
- ✓ Integrasi teknologi (hybrid DL + rules)
- ✓ Deployment & monitoring

---

## 2. Evaluasi Model Pengembangan Sistem Kandidat

### Model 1: WATERFALL (Sequential/Linear)

```
Requirements → Design → Implementation → Testing → Deployment → Maintenance
```

**Kesesuaian dengan Kerangka Rafay:**
- ✓ Struktur yang jelas dan terukur
- ✗ Tidak cocok untuk iterasi (feedback dari testing memerlukan refinement)
- ✗ Rigid untuk research (tidak ada flexibility untuk adjustments)
- ✗ Data preparation & training tidak bisa fully parallel

**Skor Kesesuaian: 40/100** — Terlalu rigid untuk development dengan iterasi.

---

### Model 2: ITERATIVE/INCREMENTAL MODEL

```
Analysis → Design & Development → Testing → Evaluation
        ↑_________________________________|
        └─ If refinement needed, loop back
```

**Kesesuaian dengan Kerangka Rafay:**
- ✓ Support untuk multiple iterations
- ✓ Dapat menangani parallel tasks (data prep vs training)
- ✓ Quality gates di setiap fase (validation checkpoints)
- ✓ Cocok untuk research yang memerlukan refinement
- ✓ Incremental deployment (model by model: NER → Event → Matcher)
- ✗ Kadang kurang terstruktur untuk dokumentasi formal

**Skor Kesesuaian: 75/100** — Sangat cocok, terutama incremental model building.

---

### Model 3: AGILE/SCRUM

```
Product Backlog → Sprint Planning → Development (2-4 weeks)
→ Daily Standup → Sprint Review → Retrospective
        ↑_________________________________|
        └─ Next Sprint with refinements
```

**Kesesuaian dengan Kerangka Rafay:**
- ✓ Iteratif dan flexible
- ✓ Focus pada working software
- ✓ Continuous integration & testing
- ✗ Overkill untuk research project (research ≠ product development)
- ✗ Kurang formal untuk dokumentasi academic
- ✗ Tidak cocok timeline project akademis (limited sprints)

**Skor Kesesuaian: 55/100** — Good for teams, tapi heavyweight untuk thesis research.

---

### Model 4: SPIRAL MODEL (Risk-Driven)

```
Planning → Risk Analysis → Engineering → Evaluation
    ↑___________________________________|
    └─ Next cycle dengan lessons learned
```

**Kesesuaian dengan Kerangka Rafay:**
- ✓ Explicit risk management (model convergence, data quality, threshold tuning)
- ✓ Iterative refinement berdasarkan risk assessment
- ✓ Support untuk parallel activities
- ✓ Quality-focused dengan extensive evaluation
- ✓ Cocok untuk complex systems dengan uncertainties
- ✗ Dokumentasi kompleks
- ✗ Mungkin overkill untuk scope yang terbatas

**Skor Kesesuaian: 80/100** — Excellent fit untuk research dengan risk considerations.

---

### Model 5: MLOps/ML DEVELOPMENT LIFECYCLE

```
Problem Definition → Data Collection → Data Preparation
    → Model Development → Model Training & Validation
    → Model Evaluation → Model Deployment → Monitoring
        ↑___________________________________|
        └─ Continuous improvement loop
```

**Kesesuaian dengan Kerangka Rafay:**
- ✓ **SPESIFIK untuk ML systems** (NER, classifiers, matching)
- ✓ Explicit handling dari data pipeline & model versioning
- ✓ Continuous validation & evaluation loops
- ✓ Monitoring & retraining strategy
- ✓ Production-ready perspective
- ✓ Natural fit untuk dual-model architecture
- ✓ Support parallel data & model streams

**Skor Kesesuaian: 95/100** — **HIGHLY RECOMMENDED** untuk ML-focused research.

---

### Model 6: HYBRID MODEL (Structured Iterative + MLOps)

Kombinasi dari:
- **Structure dari Waterfall** (clear phases, documentation)
- **Iteration dari Iterative Model** (refinement loops)
- **ML focus dari MLOps** (data + model pipelines)

```
Problem Definition
    ↓
Data Collection & Annotation (with quality control)
    ↓
Data Preparation Pipeline (Converter → Cleaner → Augmenter)
    ├─ Parallel ─────────────────────┐
    ↓                                 ↓
Model Development (NER)          Model Development (Event + Matcher)
    ↓                                 ↓
Training Cycle 1 ────────────── Training Cycle 1
    ├─ Validation                 ├─ Validation
    └─ Refinement (if needed)     └─ Refinement (if needed)
    ↓                                 ↓
Training Cycle 2 (Incremental) ← Training Cycle 2
    ↓                                 ↓
Integration & Testing
    ├─ End-to-End Testing
    ├─ Error Analysis
    └─ Refinement (if needed) ──┐
                                 ↓
                        Deployment & Monitoring
```

**Kesesuaian dengan Kerangka Rafay:**
- ✓ **Structured** (clear phases untuk academic documentation)
- ✓ **Iterative** (refinement loops untuk quality)
- ✓ **ML-focused** (explicit data + model pipelines)
- ✓ **Parallel capable** (data vs model development)
- ✓ **Quality-gated** (validation checkpoints)
- ✓ **Production-ready** (deployment & monitoring)

**Skor Kesesuaian: 98/100** — **BEST FIT** untuk kerangka pemikiran ini.

---

## 3. REKOMENDASI MODEL PENGEMBANGAN SISTEM

### ✅ PILIHAN UTAMA: HYBRID MODEL (Structured Iterative MLOps)

Untuk project PT. Rafay, model pengembangan yang **PALING COCOK SECARA AKADEMIS** adalah:

**"Structured Iterative Machine Learning Development Model"**

Kombinasi dari:

#### A. Struktur Fase (dari Waterfall + Iterative)
```
1. Problem Definition & Requirements Analysis
2. Data Collection & Preparation (pipeline-based)
3. Model Development (incremental, multi-stage)
4. Training & Validation (iterative refinement)
5. Evaluation & Testing (comprehensive)
6. Integration & Deployment
7. Monitoring & Maintenance
```

#### B. Iterasi Lokal (dari Iterative Model)
- **Data Refinement Loop**: Cleaner → Augmenter → Re-validation
- **Model Training Loop**: Training → Validation → Metric evaluation → Threshold tuning → Re-training
- **Integration Testing Loop**: End-to-end test → Error analysis → Fix → Re-test

#### C. ML Perspective (dari MLOps)
- **Data Pipeline Management**: Collection → Annotation → Preparation → Augmentation
- **Model Versioning**: Track hyperparameters, datasets used, performance metrics
- **Deployment Strategy**: Staged rollout (validation → test → production)
- **Monitoring & Feedback**: Performance tracking, error logging, retraining triggers

---

## 4. JUSTIFIKASI PEMILIHAN MODEL

### Mengapa Hybrid Model (Structured Iterative MLOps)?

#### Alasan 1: Alignment dengan Kerangka Pemikiran
Kerangka pemikiran 3.1 menunjukkan:
- Fase-fase yang **jelas & terstruktur** (6 fase besar)
- **Parallel activities** (data prep vs training)
- **Iterasi lokal** (training cycles dengan validation)
- **Quality gates** (success criteria per fase)

Hybrid model langsung mendukung semua karakteristik ini.

#### Alasan 2: Academic Rigor
Untuk tesis/skripsi, struktur yang clear sangat penting:
- **Documentation**: Mudah menjelaskan methodology yang terstruktur
- **Reproducibility**: Clear phases memungkinkan reproduction
- **Evaluation**: Explicit quality gates & metrics di setiap tahap
- **Contribution**: Jelas apa yang novel dari approach ini

#### Alasan 3: ML-Specific Requirements
Project PT. Rafay memiliki karakteristik ML yang spesifik:
- **Multiple Models**: NER, Event Classifier, Revision Matcher (need independent tracking)
- **Data Pipeline**: Collection → Annotation → Preparation → Augmentation (explicit management)
- **Training Iterations**: Need flexibility untuk hyperparameter tuning & refinement
- **Evaluation Complexity**: Multi-level metrics (per-entity, per-model, end-to-end)

#### Alasan 4: Production Readiness
Hybrid model incorporates production considerations:
- **Deployment Strategy**: Staged integration (model by model)
- **Monitoring**: Track performance over time
- **Feedback Loops**: Data drift detection, performance degradation alerts
- **Maintainability**: Clear versioning & rollback capability

---

## 5. DETAILED WORKFLOW HYBRID MODEL UNTUK RAFAY

### Phase 1: PROBLEM DEFINITION & REQUIREMENTS
```
Input: Business problem (overload data entry, ambiguity in revisions)
Activities:
  • Stakeholder analysis (admin, manager)
  • Process mapping (current workflow)
  • Requirements gathering (success criteria)
Output: Problem statement, functional requirements, non-functional requirements
```

### Phase 2: DATA COLLECTION & PREPARATION (Pipeline-Based)
```
Data Collection:
  • Source: WhatsApp operational messages (Oct 2025 - Mar 2026)
  • Volume: 5000+ messages
  • Storage: data/chat/raw/messages.json

Data Annotation:
  • Tool: Label Studio
  • Annotators: 2-3 domain experts
  • Output: export_label_studio.json (character spans + entity types)

Data Preparation Pipeline:
  CONVERTER
    ├─ Parse Label Studio JSON
    ├─ Align labels dengan tokens
    ├─ Generate BIO format
    └─ Output: TRAIN_DATA_UNCLEAN
      ↓
  CLEANER
    ├─ Fix phone numbers
    ├─ Normalize dates
    ├─ Remove stutters
    ├─ Re-tag mislabeled entities
    └─ Output: TRAIN_DATA_CLEAN
      ↓
  AUGMENTER
    ├─ Synonym replacement
    ├─ Back-translation
    ├─ Token shuffling (entity-aware)
    └─ Output: AUGMENTED_DATASET (8K samples)
      ↓
  SPLIT
    ├─ Training set: 6400 (80%)
    ├─ Test set: 1600 (20%)
    └─ Ready for training

Quality Checkpoints:
  ✓ Annotation agreement (inter-rater reliability)
  ✓ Token-label alignment validation
  ✓ Augmented data sanity check (labels preserved)
```

### Phase 3: MODEL DEVELOPMENT (Incremental)
```
MODEL 1: NER EXTRACTION (Token Classification)
  Architecture:
    IndoBERT Encoder + Token Classification Head + CRF Decoder
  
  Configuration:
    • Base model: indolem/indobert-base-uncased
    • Head type: Token Classification (768 → num_classes)
    • Loss: CRF loss (valid BIO sequence constraint)
    • Entities: 7 types (ORDER_DATE, UNIT_SPEC, LOCATION, LOAD_TIME, ROUTE, DRIVER, PHONE)

MODEL 2A: EVENT CLASSIFIER (Sequence Classification)
  Architecture:
    IndoBERT Encoder + Sequence Classification Head
  
  Configuration:
    • Base model: indolem/indobert-base-uncased
    • Head type: Sequence Classification (768 → 4)
    • Classes: NEW_ORDER, REPAIR, REFILL, NON_ORDER
    • Loss: CrossEntropyLoss
    
MODEL 2B: REVISION MATCHER (Sequence-Pair Classification)
  Architecture:
    IndoBERT Encoder + Sequence-Pair Classification Head
  
  Configuration:
    • Base model: indolem/indobert-base-uncased
    • Head type: Sequence-Pair Classification (768 → 2)
    • Classes: MATCH, NO_MATCH
    • Loss: CrossEntropyLoss
```

### Phase 4: TRAINING & VALIDATION (Iterative Refinement)
```
TRAINING CYCLE (untuk setiap model):

Cycle 1: Initial Training
  Step 1: Setup training environment
    • Device: GPU (CUDA if available)
    • Hyperparameters: batch_size=16, epochs=3, lr=2e-5
    • Callbacks: checkpointing, early stopping
  
  Step 2: Training
    • Load pre-trained IndoBERT weights
    • Forward pass dengan training data
    • Compute loss (CRF atau CrossEnt)
    • Backward pass & optimizer step (AdamW)
    • Log metrics per batch/epoch
  
  Step 3: Validation (after each epoch)
    • Evaluate on validation set
    • Compute metrics (Precision, Recall, F1, Accuracy)
    • Save best checkpoint (by F1-score)
    • Plot learning curves
  
  Output: Best checkpoint saved
  
Cycle 2: Evaluation & Analysis
  Step 1: Test set evaluation
    • Compute per-entity metrics (for NER)
    • Per-class metrics (for classifiers)
    • Confusion matrix analysis
    • Error analysis & pattern detection
  
  Step 2: Decision point:
    IF metrics >= target_criteria (F1 ≥ 0.85):
      ✓ PASS → Move to phase 5 (Integration Testing)
    ELSE:
      ✗ REFINEMENT NEEDED → Cycle 3
  
  Output: Metrics report, error log

Cycle 3: Refinement (if needed)
  Options (choose based on error analysis):
    • Option A: Adjust hyperparameters (lr, epochs, warmup)
    • Option B: Augment more data (focus pada difficult entities)
    • Option C: Architecture adjustment (add layers, change loss)
    • Option D: Data cleaning (re-annotate mislabeled examples)
  
  Re-run Cycle 1-2 with adjustments
  
  Output: Improved checkpoint with better metrics

Model Versioning:
  Each iteration tagged with:
    • Model version (v1.0, v1.1, etc.)
    • Dataset used (train_data_clean_v1, augmented_v2)
    • Hyperparameters (batch_size, lr, epochs)
    • Metrics (F1, accuracy, per-entity scores)
    • Training date & timestamp
    • Notes (what changed from previous version)
  
  Tracked in: model_metadata table (SQLite)
```

### Phase 5: INTEGRATION & END-TO-END TESTING
```
Integration Step 1: Component Testing
  ✓ NER Model: Can it extract entities from test messages?
  ✓ Event Classifier: Can it correctly route messages?
  ✓ Revision Matcher: Can it find correct parent orders?
  
Integration Step 2: Pipeline Testing
  Test complete workflow:
    Raw message 
      → Batch processor 
      → Event classifier 
      → [NER or Revision matcher] 
      → Post-processing 
      → Output
  
  Verify conditional routing:
    • NEW_ORDER → NER pipeline
    • REPAIR/REFILL → Revision Matcher pipeline
    • NON_ORDER → Manual review flag
  
Integration Step 3: End-to-End Test Case
  Test data: 30 complete orders
    • Day 1: 15 new order messages
    • Day 2: 15 refill/revision messages
  
  Success criteria:
    • Extraction accuracy: ≥ 97.8% fields correct
    • Revision matching: ≥ 93% correct parent order
    • Processing time: <5 minutes for 30 orders
    • No critical errors (graceful fallback for edge cases)
  
  Output: Test report with pass/fail per order

Integration Step 4: Error Analysis & Refinement Decision
  IF all tests PASS:
    ✓ Proceed to Phase 6 (Deployment)
  ELSE:
    ✗ Identify root causes
    ✗ Determine refinement needed (data? model? rules?)
    ✗ Go back to Phase 4 (Refinement cycle)
    ✗ Re-test
```

### Phase 6: DEPLOYMENT & INTEGRATION INTO WEB SYSTEM
```
Deployment Step 1: Model Export & Versioning
  • Save models with metadata
  • Location: models/indobert_NER/final_model/
  •          models/indobert_event_classifier/final_model/
  •          models/indobert_revision_matcher/final_model/
  
Deployment Step 2: Application Integration
  • Load models in app.py
  • Setup inference endpoints
  • Configure thresholds (0.75 for event, 0.58 for matcher)
  • Initialize database schema
  
Deployment Step 3: User Interface
  • Streamlit dashboard for admin
  • Upload CSV → Process → Download results
  • Real-time metrics & status updates
  
Deployment Step 4: Database Setup
  • Create tables: order_rows, chat_history, revision_log, model_metadata
  • Setup persistence layer (db/persistence.py)
  • Initialize sample data
  
Deployment Step 5: Testing & Validation
  • UAT (User Acceptance Testing) with admin
  • Load testing (100+ messages)
  • Edge case testing
  • Performance validation
  
Output: Production-ready system
```

### Phase 7: MONITORING & CONTINUOUS IMPROVEMENT
```
Monitoring Activities:
  • Track inference time per message
  • Log confidence scores & predictions
  • Monitor data distribution changes
  • Alert on performance degradation
  • Collect misclassified examples for retraining
  
Feedback Loop:
  • Monthly model performance review
  • Collect admin feedback on false positives
  • Identify drift in message patterns
  • Plan next model iteration if needed
  
Continuous Improvement:
  • Active learning: prioritize hard examples for annotation
  • Regular retraining: incorporate new data monthly
  • A/B testing: test new hyperparameters/architectures
  • Version management: maintain backward compatibility
```

---

## 6. DOKUMENTASI METODOLOGI DALAM SKRIPSI

### Untuk BAB III sub-bab 3.3, jelaskan:

**3.3.1 Pemilihan Model Pengembangan**
- Jelaskan mengapa Hybrid Model (Structured Iterative MLOps) dipilih
- Bandingkan dengan alternatif (Waterfall, Agile, pure MLOps)
- Gambarkan alignment dengan kerangka pemikiran 3.1

**3.3.2 Fase-Fase Pengembangan**
- Jelaskan 6-7 fase besar
- Untuk setiap fase: input, activities, output, quality criteria

**3.3.3 Iterasi & Refinement Strategy**
- Jelaskan lokal iteration loops (training, validation, refinement)
- Decision criteria untuk refinement (F1 < 0.85 → refinement needed)
- Backup strategies (augment data, adjust hyperparameters, architecture change)

**3.3.4 Model Versioning & Tracking**
- Jelaskan bagaimana model versions ditrack
- Metadata yang disimpan (hyperparameters, metrics, datasets, date)
- Rationale untuk version control (reproducibility, rollback capability)

**3.3.5 Quality Assurance**
- Quality gates di setiap fase
- Testing strategy (unit test models, integration test pipeline, end-to-end test)
- Success criteria & acceptance thresholds

---

## 7. VISUAL COMPARISON: MODEL PENGEMBANGAN KANDIDAT

```
┌─────────────────────────────────────────────────────────────────────┐
│              PERBANDINGAN MODEL PENGEMBANGAN SISTEM                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ WATERFALL (Sequential)                                             │
│ ────────────────────────────────────────────────────────────────   │
│ Req → Design → Impl → Testing → Deploy → Maintain                 │
│ ✓ Clear structure          ✗ No iteration               Score: 40  │
│ ✗ Rigid, inflexible        ✗ Late error discovery                  │
│                                                                     │
│ AGILE/SCRUM (Iterative Sprints)                                    │
│ ────────────────────────────────────────────────────────────────   │
│ Backlog → Sprint → Dev → Review → Retrospective ┐                 │
│         ↑__________________________________Loop ─┘                 │
│ ✓ Flexible & adaptive      ✗ Overkill for research      Score: 55  │
│ ✓ Iterative refinement     ✗ Heavy process overhead                │
│                                                                     │
│ SPIRAL MODEL (Risk-Driven)                                         │
│ ────────────────────────────────────────────────────────────────   │
│ Plan → Risk Analysis → Eng → Eval ┐                               │
│ ↑________________________Loop ─────┘                                │
│ ✓ Explicit risk management         Score: 80                       │
│ ✓ Quality-focused                  ✗ Complex documentation         │
│ ✓ Iterative refinement                                             │
│                                                                     │
│ ITERATIVE/INCREMENTAL MODEL (Phase-Based)                          │
│ ────────────────────────────────────────────────────────────────   │
│ Analysis → Dev → Testing → Eval ┐                                 │
│ ↑_________________Loop ─────────┘                                  │
│ ✓ Clear phases with checkpoints    Score: 75                       │
│ ✓ Incremental delivery             ✓ Academic-friendly             │
│ ✓ Quality gates                    ✗ Generic (not ML-specific)    │
│                                                                     │
│ MLOps/ML LIFECYCLE MODEL (Data-Model Centric)                      │
│ ────────────────────────────────────────────────────────────────   │
│ Problem → Data → Prep → Dev → Train → Eval → Deploy ┐             │
│ ↑_________________________________Loop ──────────────┘             │
│ ✓ ML-specific workflows            Score: 95                       │
│ ✓ Explicit data pipeline           ✓ Handles multi-model systems   │
│ ✓ Monitoring & retraining          ✓ Production-ready              │
│                                                                     │
│ ★ HYBRID MODEL (Structured Iterative MLOps) ★                     │
│ ────────────────────────────────────────────────────────────────   │
│ Problem → Data → Prep ─┐                                          │
│                        ├─ Model Dev → Train → Eval ┐             │
│                        │                            ├─ Integration│
│  ───────────────────────────────────────────────────┘             │
│ ✓ Clear structure (academic documentation)                        │
│ ✓ Iterative refinement (quality focus)          Score: 98         │
│ ✓ ML-specific (data + model pipelines)          ★★★ RECOMMENDED   │
│ ✓ Parallel capability (data vs model)           ✓ Perfect fit!    │
│ ✓ Production-ready (deployment & monitoring)                      │
│ ✓ Quality-gated (explicit success criteria)                       │
│                                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## KESIMPULAN: MODEL PENGEMBANGAN SISTEM YANG DIREKOMENDASIKAN

**Untuk project PT. Rafay, model pengembangan sistem yang PALING COCOK secara akademis adalah:**

## ★ HYBRID MODEL (Structured Iterative Machine Learning Development Model)

**Karakteristik Utama:**
1. **Structured phases** (6-7 fase jelas untuk academic documentation)
2. **Iterative refinement loops** (training validation cycles)
3. **ML-specific perspective** (explicit data + model pipelines)
4. **Parallel capabilities** (data preparation vs model development)
5. **Quality-gated** (explicit success criteria per phase)
6. **Production-ready** (deployment & monitoring considerations)

**Alasan Pemilihan:**
- Alignment sempurna dengan kerangka pemikiran 3.1
- Support untuk karakteristik unik project (multi-model, data pipeline, iterasi)
- Academic rigor dengan praktical ML considerations
- Clear documentation path untuk tesis/skripsi
- Reproducibility & quality assurance built-in

**Implementasi dalam Skripsi:**
- BAB III sub-bab 3.3: Jelaskan Hybrid Model dengan detail fase dan iterasi
- Gambar diagram fase + iterasi loops (visual clarity)
- Jelaskan quality gates & success criteria per fase
- Justifikasi pemilihan vs alternatif models

---

**Dokumen 3.3 ini siap untuk ditulis ke BAB III skripsi Anda dengan structure yang akademis dan praktis!**
