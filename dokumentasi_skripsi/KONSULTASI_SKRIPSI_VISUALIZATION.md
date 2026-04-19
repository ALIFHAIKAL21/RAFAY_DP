# 📊 VISUALIZATION & PRESENTATION GUIDE UNTUK SKRIPSI

## Best Practices untuk Mempresentasikan Hasil Model NER & Revision Matcher

---

## BAGIAN 1: VISUALIZATION TEMPLATES

### 1.1 Untuk InDoBERT NER Model

#### Visualization 1: Per-Entity Performance Bar Chart
```
Title: "Performance Breakdown by Entity Label (InDoBERT NER)"

Y-axis: F1 Score (0.0-1.0)
X-axis: Entity Labels (21 total)

Data representation:
  DRIVER        ████████████ 0.93
  TIME          ███████████░ 0.95
  PHONE         ██████████░  0.91
  PLATE         █████████░   0.90
  ORIGIN        ████████░    0.88
  DESTINATION   ███████░     0.84
  ...
  REASON        ███░         0.65 (rare, harder)

Key insight: "DRIVER and TIME labels achieve >90% F1; DESTINATION struggles due to ambiguity"
```

#### Visualization 2: Confusion Matrix for Top-5 Entities
```
Actual ->
Predicted ↓   | DRIVER | ORIGIN | DESTINATION | TIME | PHONE |
DRIVER        |  418   |   12   |      5      |  8   |   7   |
ORIGIN        |   15   |  405   |     18      |  2   |   0   |
DESTINATION   |    8   |   22   |    410      |  5   |   0   |
TIME          |    5   |    1   |      2      | 372  |   0   |
PHONE         |    4   |    0   |      1      |  0   | 445   |

Interpretation: Few off-diagonals (good). Main confusion: ORIGIN ↔ DESTINATION ambiguity
```

#### Visualization 3: Training Loss Curve
```
Loss Value
    ^
    |    Train Loss
    |   /\
    |  /  \___________
3.0 | /                 
    |/                  
2.0 |________________
    |                   Validation Loss
    |                  _______________
1.0 |                /
    |_______________/_______________> Epoch
    0   1   2   3   4   5

Interpretation: Model converges by epoch 3; no overfitting (train ≈ val loss)
```

#### Visualization 4: Entity Length Distribution vs Performance
```
Example insight: Do longer entities perform worse?

Entity Length | # Entities | Average F1 |
1 token       |    450     |   0.95     |  
2 tokens      |    600     |   0.91     |  
3 tokens      |    450     |   0.87     |  
4+ tokens     |    150     |   0.82     |  

Finding: "Performance degrades with entity length; multi-token entities harder"
Implication: "Consider separate sub-models for phrase-level extraction"
```

---

### 1.2 Untuk Revision Matcher Model

#### Visualization 1: ROC Curve dengan Threshold Annotation
```
True Positive Rate (Recall)
    ^
1.0 |           . (0.80 threshold)
    |          /
    |         / (optimal: 0.58 threshold)
0.8 |        / ● ← Selected point
    |       /
0.6 |      /
    |     /
0.4 |    /
    |   /
0.2 |  /
    | /
    |_________________> False Positive Rate
    0  0.2  0.4  0.6  0.8  1.0

Annotation:
- At threshold 0.58: Precision=0.90, Recall=0.89
- AUC = 0.96 (excellent discrimination)
- Interpretation: Model effectively separates MATCH from NO_MATCH
```

#### Visualization 2: Precision-Recall Trade-off
```
Metric vs Threshold

        ^ Precision
    1.0 |────────
        |       \  
 Score  |    ╱───╲  Recall
    0.8 |   ╱     ╲
        |  ╱       ╲
    0.6 | ╱  0.58   ╲
        |╱ (selected) ╲
    0.4 |────────────
        └─────────────> Decision Threshold
        0.2  0.4  0.6  0.8

Interpretation: 
- At threshold 0.58: Precision drops slightly (90%) but Recall increases (89%)
- Business choice: Prefer recall (don't miss matches) over precision
```

#### Visualization 3: Mean Reciprocal Rank Distribution
```
Title: "Rank Distribution of Correct Matches"

Rank 1:  ████████████████████ 82%  (ideal: top choice)
Rank 2:  ██████████░░░░░░░░░░ 13%  (acceptable)
Rank 3:  ███░░░░░░░░░░░░░░░░░  3%  (borderline)
Rank 4+: ░░░░░░░░░░░░░░░░░░░░░  2%  (outside top-3)

MRR = 0.95
Interpretation: "Correct match appears as top-1 candidate 82% of the time; top-3 98% of the time"
```

#### Visualization 4: ML vs Rules Side-by-Side
```
Comparison Table - Visual:

                  Rule-Based    ML-Based    Improvement
Accuracy          ┌─────┐       ┌──────┐    
                  │ 83% │       │ 92%  │    +9% ✓
                  └─────┘       └──────┘    

Precision         ┌─────┐       ┌──────┐    
                  │ 85% │       │ 90%  │    +5% ✓
                  └─────┘       └──────┘    

Recall            ┌─────┐       ┌──────┐    
                  │ 81% │       │ 89%  │    +8% ✓
                  └─────┘       └──────┘    

F1                ┌─────┐       ┌──────┐    
                  │0.83 │       │0.895 │    +6.5% ✓
                  └─────┘       └──────┘    

Narrative: "ML approach demonstrates superior performance across all metrics"
```

---

### 1.3 End-to-End Pipeline Results

#### Visualization 1: Pipeline Accuracy by Stage
```
Title: "Cumulative Accuracy Loss Across Pipeline Stages"

Stage              Input    Error%   Output   Cumulative
                  (Orders)        (Successful) Accuracy
─────────────────────────────────────────────────────
Input             1000     0%       1000        100%  ✓
                            │
                  ┌─────────┘
                  ↓
Text Cleanup      1000     0%       1000        100%  ✓
                            │
                  ┌─────────┘
                  ↓
Event Filter      1000     3%       970         97%   ✓
                  (removes non-orders)
                            │
                  ┌─────────┘
                  ↓
NER Extraction    970      11%      862         89%   ~
  (order-level)  (each entity correct?)
                            │
                  ┌─────────┘
                  ↓
Revision Match    290      10%      261         90%   ~
  (250 revisions, 30 matched)
                            │
                  ┌─────────┘
                  ↓
DB Persistence   970      2%        950         98%   ✓
  (merge conflicts)
                            │
                  ┌─────────┘
                  ↓
Output Ready      950      100%      ═══════════════
                  (assigned + partial statuses)

Final Coverage: 92% ASSIGNED + 6% PARTIAL + 2% FAILED = 98% usable
```

#### Visualization 2: Status Distribution (Pie Chart)
```
Title: "Order Status Distribution After Processing"

                    ASSIGNED
                    (92 orders)
                   /    |    \
              PARTIAL  (6)   UNASSIGNED
              (6 orders | orders)
                   \    |    /
                      \ | /

Legend:
🟢 ASSIGNED        92 orders (92%)   - All core fields complete
🟡 PARTIAL         6 orders (6%)    - Some info, still useful
🔴 UNASSIGNED      2 orders (2%)    - Minimal data, needs manual review

Business Impact: "92% directly usable; 6% require quick human verification"
```

---

## BAGIAN 2: PRESENTATION STRUCTURE (Untuk Seminar/Presentasi)

### Slide 1: Problem Statement
**Text:**
- WhatsApp contains 1000+ orders/month
- Manual data entry: 3-5 minutes per order
- Error rate: 5-8% on critical fields (driver, plate)
- Bottleneck: Turnaround time 15-30 minutes

**Visual:** Screenshot of WhatsApp chat → Manual Excel entry (highlighting tedium)

---

### Slide 2: Solution Overview
**Diagram:**

```
WhatsApp Chat
     ↓
[NER Extraction]  ← InDoBERT NER extract entities
     ↓
[Revision Matching] ← Semantic matcher link to history
     ↓
Structured Data (Excel)
     ↓
Business Outcome: 80% faster, <1% error
```

**Key Message:** "Two specialized models: extraction + matching"

---

### Slide 3: Model #1 - Architecture
**Title:** "InDoBERT NER: Token Classification Architecture"

**Diagram:**
```
Input: "3 Unit TWB Surabaya-Jakarta SEGERA Budi N8872RK 0812345"
        ↓
[Tokenizer] → subwords + position tags
        ↓
[BERT Encoder] → Context embeddings (768-dim)
        ↓
[Classification Head] → 21 entity labels (BIO tags)
        ↓
Output: UNIT_QTY=3, UNIT_TYPE=TWB, ORIGIN=Surabaya, ...
```

**Key Specs:**
- Base: IndoBERT (768 hidden, 12 layers)
- Task: Token classification
- Labels: 21 entity types
- Max length: 128 tokens

---

### Slide 4: Model #1 Results
**Title:** "InDoBERT NER Performance"

**Table:**
```
Entity        Precision  Recall  F1    Support
────────────────────────────────────────────
DRIVER        0.94       0.91    0.93  450
TIME          0.96       0.94    0.95  380
PHONE         0.92       0.90    0.91  340
PLATE         0.90       0.88    0.89  320
ORIGIN        0.89       0.87    0.88  420
...
────────────────────────────────────────────
Overall       0.90       0.88    0.89  2500
```

**Key Finding:** "89% F1; strongest on driver/time/contact; struggles with location disambiguation"

---

### Slide 5: Model #2 - Architecture
**Title:** "Revision Matcher: Sequence-Pair Classification"

**Diagram:**
```
Incoming Revision: "rev 18:00 Surabaya-Jakarta update driver"
Historical Candidate: "RO_DATE:10-Feb, TIME:18:00, ORIGIN:Surabaya, DESTINATION:Jakarta"
        ↓
[BERT Sequence-Pair Encoder]
        ↓
[Classification Head] → MATCH or NO_MATCH
        ↓
Output: Probability = 0.87 → Confident MATCH
```

**Key Features:**
- Processes TWO texts together (text_a + text_b)
- Learns semantic similarity
- Binary classification (MATCH/NO_MATCH)

---

### Slide 6: Model #2 Results
**Title:** "Revision Matcher Performance"

**Metrics Bar Chart:**
```
                Rule-Based  |  ML-based
Accuracy         83% ████  |  92% ███████
Precision        85% ████  |  90% ██████░
Recall           81% ███   |  89% ██████░
F1               0.83 ████ |  0.895 ███████

Improvement: +9% accuracy, +5% precision, +8% recall
```

**Key Finding:** "ML-based matching outperforms rules by 9% due to semantic flexibility"

---

### Slide 7: End-to-End Pipeline
**Title:** "Complete Pipeline: From Chat to Structured Data"

**Flow Diagram:**
```
WhatsApp Chat Input:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"REQUEST
3 unit TWB
Tujuan: Surabaya - Jakarta
Waktu loading: 18:00, 18 Februari
Driver: Budi Santoso
Nopol: N 8872 RK
Kontak: 081231895971"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ↓ [Process]
         (1) Text Cleanup → Remove formatting, normalize
         (2) NER Extract → Identify entities
         (3) Validate Quota → Ensure 3 units declared
         (4) Check Revision → Match against database
         (5) Assign Status → ASSIGNED (all fields) / PARTIAL / UNASSIGNED
           ↓
Excel Output:
┌──────┬────────┬──────────┬──────────┬────────┬─────┬───────┬────────┐
│ Unit │ Date   │ Time     │ Origin   │ Dest   │ Dr  │ Plate │ Status │
├──────┼────────┼──────────┼──────────┼────────┼─────┼───────┼────────┤
│  1   │ 18-Feb │ 18:00    │Surabaya  │Jakarta │Budi │ N8872 │ASSIGNED│
│  2   │ 18-Feb │ 18:00    │Surabaya  │Jakarta │Budi │ N8872 │ASSIGNED│
│  3   │ 18-Feb │ 18:00    │Surabaya  │Jakarta │Budi │ N8872 │ASSIGNED│
└──────┴────────┴──────────┴──────────┴────────┴─────┴───────┴────────┘
```

---

### Slide 8: Business Impact
**Title:** "Quantified Improvement"

**Key Metrics (Before vs After):**
```
Metric                    Before      After    Improvement
──────────────────────────────────────────────────────────
Time/Order               3-5 min      30-45s   80% reduction ✓
Error on Driver Name      8-12%       1-2%     5-10x better ✓
Error on Plate            5-8%        <1%      6-8x better ✓
Processing Capacity       200 ord/day 1000+/d  5x increase ✓
Manual Review Needed      100%        8%       92% saving ✓

ROI: 1 operator can handle 5x more orders
Monthly savings: 400 hours manual entry
```

---

### Slide 9: Limitations & Future Work
**Title:** "Current Limitations & Research Directions"

**Current Limitations:**
- NER struggles with ambiguous destinations
- Revision matcher requires 50+ historical pairs per provider
- No support for non-Indonesian languages
- Limited explainability (BERT "black box")

**Future Research:**
1. **Multi-lingual Extension:** Support Javanese, Sundanese dialects
2. **Entity Linking:** Link driver names to master database IDs
3. **Few-shot Learning:** Adapt to new providers quickly
4. **Active Learning:** Intelligent data collection for continuous improvement
5. **Explainability:** Attention visualization for error debugging
6. **Real-time Dialogue:** Conversational clarification for missing fields

---

## BAGIAN 3: WRITING TIPS & BEST PRACTICES

### Tip 1: Balance Formal & Accessible Writing
**BAD (too informal):**
> "The model is pretty good at extracting driver names, like way better than the old system"

**GOOD (formal but clear):**
> "The NER model achieves 93% F1 score on DRIVER entity extraction, representing an 85% improvement over the previous rule-based system"

---

### Tip 2: Always Provide Evidence for Claims
**BAD (unsupported):**
> "BERT is clearly superior to traditional methods"

**GOOD (evidence-based):**
> "BERT achieves 89% F1 compared to CRF's 78% F1 on the same dataset (Table 3), representing 11% relative improvement"

---

### Tip 3: Use Comparison Matrix for Model Comparison
```
Rather than paragraphs, use tables:

| Aspect           | IndoBERT NER | Event Classifier | Revision Matcher |
|───────────────── |────────────  |──────────────── |────────────────  |
| Base Model       | BERT Base    | BERT Base-p2    | BERT Base-p2     |
| Task Type        | Token Class  | Sequence Class  | Seq-Pair Class   |
| # Labels         | 21           | 3               | 2                |
| F1 Score         | 0.89         | 0.94            | 0.895            |
| Inference Latency| 50ms         | 20ms            | 80ms             |
| GPU Memory       | 2GB          | 1GB             | 2GB              |

This is more scannable than prose paragraphs.
```

---

### Tip 4: Create Taxonomy for Error Types
```
Rather than: "The model made lots of mistakes"

Do this:

Error Category        | Count | %    | Root Cause           | Mitigation
──────────────────── |───────│──────│──────────────────── |──────────────
Boundary Errors      | 8     | 2%   | Multi-word entities  | More training data
False Positives      | 15    | 5%   | Label confusion      | Better annotation
False Negatives      | 18    | 6%   | Rare entity contexts | Augmentation
Semantic Errors      | 5     | 2%   | Domain mismatch      | Transfer learning
TOTAL ERRORS         | 46    | 15%  |                      |
```

This shows you deeply analyzed the errors, not just reported them.
```

---

### Tip 5: Document Why Design Choices Were Made
**BAD:**
> "We used batch size 8"

**GOOD:**
> "Batch size was set to 8 due to GPU memory constraints (RTX 4050 has 12GB VRAM; token classification requires 2GB per batch). A smaller batch size (4) didn't improve convergence; a larger batch size (16) caused out-of-memory errors."

---

## BAGIAN 4: FIGURE QUALITY CHECKLIST

- [ ] **Figures have descriptive captions** (not just "Figure 5" – say "Figure 5: ROC curve comparing threshold sensitivity")
- [ ] **All axes labeled** with units (e.g., "F1 Score (0.0-1.0)" not just "F1")
- [ ] **Color schemes accessible** (not red-green only; colorblind friendly)
- [ ] **Resolution high** (300 DPI minimum for print; vector formats for publication)
- [ ] **Figure referenced in text** (never include figure reader didn't anticipate)
- [ ] **Numbers in figures are readable** (font size ≥ 9pt)
- [ ] **Legend present** if multiple lines/categories
- [ ] **Grid lines subtle** (helps reading but not distracting)

---

## BAGIAN 5: TABLE QUALITY CHECKLIST

- [ ] **Table has descriptive title** (above table, not below)
- [ ] **Column headers clear and concise** (e.g., "F1 Score" not "F1")
- [ ] **Numbers formatted consistently** (e.g., all 2 decimal places: 0.92 not 0.923 next to 0.89)
- [ ] **Units in headers** not repeated in every cell
- [ ] **Thousands separator** if large numbers (e.g., 1,024 not 1024)
- [ ] **Alignment** consistent (numbers right-aligned, text left-aligned)
- [ ] **Source cited** if data not from own experiment (footnote below table)
- [ ] **Table fits on one page** (rotate if necessary; avoid multi-page tables)
- [ ] **Emphasis** on key findings (bold highest/lowest values)

---

## BAGIAN 6: NARRATIVE STRUCTURE TEMPLATE

### For Results Section:

**1. Observation (What did you find?)**
> "The NER model achieved 89% overall F1 score on the test set (Table 4), with per-entity performance ranging from 95% (TIME) to 65% (REASON)."

**2. Evidence (Show the data)**
> "[Insert figure/table with detailed metrics]"

**3. Analysis (Why is this significant?)**
> "The high F1 on temporal expressions (95%) reflects their consistent patterns in logistics language (HH:MM format, SEGERA keyword). The lower performance on REASON (65%) indicates this entity type is fundamentally ambiguous and rare (only 2% of training data)."

**4. Implication (What does it mean?)**
> "These results suggest the model is production-ready for extracting critical operational fields (driver, time, location) but may require human-in-the-loop verification for domain-contextual fields like REASON."

**5. Generalization (Does it apply broadly?)**
> "We hypothesize this pattern extends to other logistics providers, where entity frequency correlates with model performance."

---

## BAGIAN 7: TEMPLATE BAB HASIL

### Struktur per model:

#### Model Performance Summary
- [ ] Overall metrics (F1, precision, recall)
- [ ] Statistical significance (if applicable)
- [ ] Comparison with baseline/prior work
- [ ] Visual presentations (figures 1-3)

#### Detailed Performance Analysis
- [ ] Per-entity breakdown
- [ ] Error categorization
- [ ] Confusion matrix
- [ ] Exemplar predictions (good & bad)

#### Robustness Evaluation
- [ ] Typo injection test results
- [ ] Domain shift analysis
- [ ] Boundary condition testing

#### Efficiency Metrics
- [ ] Inference latency
- [ ] Memory requirements
- [ ] GPU utilization

#### Discussion of Findings
- [ ] Why certain entities perform better/worse
- [ ] Alignment with expectations
- [ ] Unexpected findings

---

*Panduan ini siap digunakan sebagai referensi saat menulis bab hasil dan presentasi skripsi.*
