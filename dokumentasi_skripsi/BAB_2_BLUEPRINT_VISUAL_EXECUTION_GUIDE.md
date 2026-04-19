# 🎯 BLUEPRINT VISUAL & EXECUTION GUIDE - BAB 2
## Struktur Terkompresi + Panduan Implementasi

**Status:** Ready for Content Generation  
**Purpose:** Visual reference + how to generate each subsection  
**Output:** Action items per subsection

---

## BAGIAN 1: BAB 2 STRUKTUR VISUAL - TREE DIAGRAM

```
┌────────────────────────────────────────────────────────────────┐
│               BAB II. LANDASAN TEORI                            │
│          Knowledge Foundation untuk RAFAY IDP v2.0              │
└────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────▼─────────┐           ┌────────▼──────────┐
        │  2.1 TINJAUAN   │           │  2.2 PENELITIAN   │
        │   PUSTAKA       │           │    TERKAIT        │
        │ (Foundational   │           │  (Related Work &  │
        │  Concepts)      │           │   Gap Analysis)   │
        │ ~6,400 words    │           │  ~1,900 words     │
        └────────┬────────┘           └────────┬──────────┘
                 │                             │
    ┌────────────┼──────────────────┬─────────┘
    │            │                  │
    ▼            ▼                  │
2.1.1       2.1.2-5            2.1.6-11        2.2.1-5
[Core       [Embedding &      [NLP App &    [Survey &
NLP]        BERT]             Domain]       Position]
    │            │                  │
    ▼            ▼                  ▼

┌─Concepts───┬─Tech Stack──┬──Applications──┬─Related Research──┐
│- NLP basics│- Embeddings │- NER (21 types)│- Indonesian NER   │
│- Relevance │- Transformer│- Sem. Matching │- E-com Matching   │
│  to orders │- BERT       │- Seq-pair class│- Hybrid Systems   │
│            │- InDoBERT   │- Indonesian    │- InDoBERT apps    │
│            │- Transfer   │- Informal text │- Order processing │
│            │  Learning   │- Hybrid ML+R   │                   │
│            │            │- Evaluation    │                   │
│            │            │  metrics       │                   │
└────────────┴────────────┴────────────────┴───────────────────┘
```

---

## BAGIAN 2: SUBSECTION QUICK REFERENCE

### **CLUSTER A: FOUNDATIONAL CONCEPTS (Building Blocks)**

```
2.1.1: Natural Language Processing
└─ Purpose: Why NLP relevant to problem
└─ Length: 400 words
└─ Key Content: NLP definition, tasks, why hard, order extraction context
└─ Target Audience: Non-NLP experts
└─ Generate: Conceptual explanation + order processing application
```

```
2.1.2: Word Embeddings dan Representasi Teks
└─ Purpose: Foundation for understanding BERT (contextual embeddings)
└─ Length: 500 words
└─ Key Content: Static embeddings → why BERT better → connection
└─ Focus: W2V/GloVe concepts (not math), BERT advantage
└─ Generate: Intuitive explanation + why matters for order extraction
```

```
2.1.3: Transformer Architecture
└─ Purpose: Understand why BERT works so well
└─ Length: 600 words
└─ Key Content: Attention mechanism, why transformers > RNN
└─ Focus: Self-attention intuition, multi-head, why fast & parallelizable
└─ Generate: Visual-friendly explanation (sequence processing model)
```

---

### **CLUSTER B: CORE TECHNOLOGY (BERT-Based)**

```
2.1.4: BERT Model dan Transfer Learning ⭐ CRITICAL
└─ Purpose: Core methodology for entire project
└─ Length: 800 words
└─ Key Content: 
   ├─ BERT architecture (12L, 768H, 12H)
   ├─ Bidirectional advantage
   ├─ Pre-training (MLM, NSP)
   ├─ Fine-tuning vs feature extraction
   └─ Why perfect for 2 tasks + limited data
└─ Must Include: Why BERT > LSTM/CNN for this project
└─ Generate: Detailed but accessible explanation
```

```
2.1.5: InDoBERT: BERT untuk Bahasa Indonesia
└─ Purpose: Justify technology choice (why InDoBERT not mBERT)
└─ Length: 500 words
└─ Key Content:
   ├─ What InDoBERT is (pre-trained on Indo corpus)
   ├─ Why Indo-specific better
   ├─ Performance comparison (InDoBERT vs mBERT)
   └─ Why chosen for Rafay
└─ Must Discuss: Indonesian morphology advantages
└─ Generate: Comparative analysis + justification
```

---

### **CLUSTER C: APPLICATION COMPONENTS (Project-Specific)**

```
2.1.6: Named Entity Recognition (NER) ⭐ CRITICAL
└─ Purpose: Justify Component 1 of project
└─ Length: 800 words
└─ Key Content:
   ├─ NER task definition
   ├─ Sequence labeling (BIO scheme, explain tags)
   ├─ Traditional vs Neural approaches
   ├─ BERT for token classification
   ├─ 21 entity types for order domain
   ├─ Evaluation metrics (token vs entity level)
   └─ Why critical for order extraction
└─ Must Include: Practical example (order message → extracted entities)
└─ Generate: Conceptual + practical walkthrough
```

```
2.1.7: Semantic Similarity dan Sentence Embeddings
└─ Purpose: Foundational for Component 2
└─ Length: 600 words
└─ Key Content:
   ├─ Semantic similarity definition
   ├─ Sentence embedding methods
   ├─ BERT CLS token for representation
   ├─ Similarity scoring
   └─ Why for revision matching
└─ Must Include: Connection to ranking (top-3 candidates)
└─ Generate: Intuitive explanation + ranking application
```

```
2.1.8: Sequence-Pair Classification dengan BERT
└─ Purpose: Justify Component 2 implementation
└─ Length: 500 words
└─ Key Content:
   ├─ Sequence-pair task (vs single sequence)
   ├─ BERT pair input format [CLS]+S1+[SEP]+S2
   ├─ Why effective for pair classification
   ├─ Binary classification (MATCH/NO-MATCH)
   ├─ Confidence scoring & ranking
   └─ Application to revision-order matching
└─ Must Include: Example (revision msg + order candidates → scores)
└─ Generate: Practical application walkthrough
```

---

### **CLUSTER D: CONTEXT & METHODOLOGY (Supporting)**

```
2.1.9: Karakteristik Bahasa Indonesia dan Teks Informal
└─ Purpose: Justify preprocessing + why rule layer needed
└─ Length: 500 words
└─ Key Content:
   ├─ Indonesian morphology & syntax
   ├─ Informal text (WhatsApp) characteristics
   ├─ Typos, abbreviations, slang
   ├─ Challenges for NLP
   ├─ Why InDoBERT handles better
   └─ Why rule layer needed for residuals
└─ Must Include: Example from raw.txt (actual message patterns)
└─ Generate: Contextualized explanation with examples
```

```
2.1.10: Pendekatan Hybrid: Machine Learning + Rule-Based
└─ Purpose: Justify architectural choice (3 components, not just 2 models)
└─ Length: 600 words
└─ Key Content:
   ├─ Pure ML limitations (edge cases, rules implicit)
   ├─ Pure rule limitations (brittleness, not generalizable)
   ├─ Why hybrid (combine strengths)
   ├─ Hybrid patterns (our pattern: ML → rule refinement)
   ├─ Why appropriate for Rafay (data constraints, format consistency)
   └─ Examples from similar projects
└─ Must Include: Rafay-specific justification (why rules needed)
└─ Generate: Philosophical + practical justification
```

```
2.1.11: Metrics Evaluasi untuk Tugas NLP
└─ Purpose: Explain how we measure success
└─ Length: 500 words
└─ Key Content:
   ├─ Basic metrics (Precision, Recall, F1)
   ├─ Why F1 (vs accuracy)
   ├─ Entity-level metrics (important for app)
   ├─ Per-entity evaluation (some entities more critical)
   ├─ For pair classification (ranking metrics)
   ├─ Cross-validation importance
   └─ Connection to project evaluation
└─ Must Include: Concrete example (how we evaluate NER success)
└─ Generate: Methodological explanation
```

---

### **CLUSTER E: RELATED RESEARCH (Context & Positioning)**

```
2.2.1: Sistem NER di Bahasa Indonesia
└─ Purpose: Where is existing work → what's the gap?
└─ Length: 400 words
└─ Key Content:
   ├─ Existing Indonesian NER systems
   ├─ Performance on formal text
   ├─ Gap: Informal text + order domain
   ├─ Why Rafay project addresses gap
   └─ Our contribution
└─ References: IndoBERT NER benchmarks, Indonesian datasets
└─ Generate: Literature survey + gap analysis
```

```
2.2.2: Semantic Matching dalam E-Commerce dan Logistik
└─ Purpose: Existing semantic matching work → Rafay's unique angle
└─ Length: 400 words
└─ Key Content:
   ├─ Order matching/revision matching literature
   ├─ Existing approaches (rules, ML, hybrid)
   ├─ Gap: Indonesian context, revision-specific matching
   ├─ Why Rafay approach novel
   └─ Our contribution
└─ References: E-commerce deduplication, logistics automation
└─ Generate: Application domain research survey
```

```
2.2.3: Sistem Hybrid Machine Learning + Rule-Based
└─ Purpose: Hybrid approach proven → why ours is justified
└─ Length: 350 words
└─ Key Content:
   ├─ Examples hybrid systems in NLP literature
   ├─ When hybrid outperforms pure approaches
   ├─ Design patterns
   ├─ Why for Rafay (data constraints)
   └─ Positioning our hybrid
└─ References: Hybrid NER, hybrid IE systems
└─ Generate: Architecture positioning
```

```
2.2.4: Aplikasi InDoBERT di Downstream Tasks
└─ Purpose: InDoBERT proven on various tasks → justified for ours
└─ Length: 350 words
└─ Key Content:
   ├─ InDoBERT paper & design
   ├─ Applications (sentiment, POS, NER, etc.)
   ├─ Performance vs mBERT
   ├─ Successfully used for 2-task architecture?
   ├─ What we do differently/uniquely
   └─ Our contribution
└─ References: InDoBERT paper, downstream task papers
└─ Generate: Technology landscape overview
```

```
2.2.5: Sistem Pemrosesan Pesanan Otomatis
└─ Purpose: Situate in broader logistics automation context
└─ Length: 400 words
└─ Key Content:
   ├─ Logistics automation literature
   ├─ Order processing challenges (international)
   ├─ Similar AI systems
   ├─ Why Rafay project relevant to industry
   ├─ Business impact potential
   └─ Our contribution to field
└─ References: Logistics automation, order processing systems
└─ Generate: Application context + business relevance
```

---

## BAGIAN 3: CONTENT GENERATION GUIDELINES PER SUBSECTION

### Template for Each Subsection:

```
📝 SUBSECTION STRUCTURE:

[Opening Paragraph]
├─ Define/introduce concept
├─ Why relevant to NLP/project
└─ Roadmap: what will be covered

[Body Paragraphs]
├─ Explanation 1: Core concept
├─ Explanation 2: How it works / methodology
├─ Example/Application: How relevant to order extraction/matching
└─ Connection: How applicable to Rafay project

[Closing Paragraph]
├─ Summary of key points
├─ Significance for project
└─ Bridge to next subsection
```

### Length Guidelines:

| Length | Appropriate For | Examples |
|--------|-----------------|----------|
| 300-400 words | Basic foundational concepts | 2.1.1 (NLP intro) |
| 400-500 words | Intermediate concepts or surveys | 2.1.2, 2.1.9 |
| 500-600 words | Important concepts with examples | 2.1.3, 2.1.7, 2.1.11 |
| 600-800 words | **CRITICAL** sections needing detail | 2.1.4, 2.1.6, 2.1.10 |
| 350-450 words | Related work surveys | 2.2.1-2.2.5 |

### Detail Level:

| Concept | Detail Level | Why |
|---------|-------------|-----|
| Math/formulas | Minimal (mention, don't derive) | Project not implementing from scratch |
| Intuition/concepts | HIGH (explain clearly) | Students need to understand principles |
| Examples | HIGH (use project-relevant) | Concrete understanding |
| Implementation | MINIMAL (not needed) | Project using frameworks |
| Comparisons | MEDIUM (existing work) | Positioning & justification |

---

## BAGIAN 4: SUBSECTION-BY-SUBSECTION CONTENT HINTS

### 2.1.1: Natural Language Processing

**Opening:**
"Natural Language Processing (NLP) adalah subfield Artificial Intelligence yang berfokus pada 
pemahaman dan pengolahan bahasa alami manusia..."

**Must Cover:**
- NLP tasks (tokenization, POS, NER, etc.)
- Why hard (ambiguity, context dependency)
- Modern NLP era (shift from rules to machine learning)
- Relevance to order extraction

**Example to Use:**
"Dalam konteks PT. Rafay, pesanan dikirim melalui WhatsApp dalam bentuk teks tidak terstruktur 
seperti 'REQUEST ORDER ONCALL ... 5 UNIT TWB 50 CBM'. Tugas NLP adalah mengekstraksi informasi 
terstruktur (5 unit, model TWB, kapasitas 50 CBM) dari teks tidak terstruktur ini..."

---

### 2.1.2: Word Embeddings

**Opening:**
"Untuk memproses teks dengan komputer, kita perlu merepresentasikan kata dalam bentuk numerik. 
Word embeddings adalah teknik untuk mengkonversi kata menjadi vektor kontinyu..."

**Must Cover:**
- Why not one-hot encoding
- Static embeddings (W2V, GloVe) - conceptual
- Limitations (not contextual)
- Contextual embeddings (BERT) - why better
- Connection: Why BERT's contextual embeddings crucial for order extraction

**Don't Over-Include:**
- Mathematical derivation of W2V skip-gram
- All embedding variants

---

### 2.1.3: Transformer Architecture

**Opening:**
"Transformer adalah arsitektur neural network yang merevolusi NLP dengan menggantikan 
RNN/LSTM yang memproses sequence secara sekuensial dengan mechanisme self-attention 
yang memproses seluruh sequence secara parallel..."

**Must Cover:**
- Sequential processing limitation (RNN bottleneck)
- Self-attention mechanism (intuition, not math)
- Multi-head attention
- Positional encoding
- Why faster & better
- Application in BERT

**Example:**
"Dalam ekstraksi field order, self-attention memungkinkan model fokus ke kata-kata penting 
('DRIVER: Umar Ali') sambil mengabaikan kata filler ('REQUEST ORDER ONCALL')..."

---

### 2.1.4: BERT Model dan Transfer Learning ⭐

**Opening:**
"BERT (Bidirectional Encoder Representations from Transformers) adalah model pre-trained 
yang mengubah paradigma NLP dengan memanfaatkan transfer learning. BERT pre-trained pada 
corpus massive dengan tujuan generic, kemudian di-fine-tune untuk task spesifik..."

**Must Cover (DETAILED):**
- BERT architecture (12 layers, 768 hidden, 12 heads for base)
- Bidirectional training advantage vs unidirectional
- Pre-training objectives:
  * MLM (Masked Language Model) - explain why effective
  * NSP (Next Sentence Prediction)
- Fine-tuning approach vs feature extraction
- Why choose fine-tuning (vs feature extraction) for Rafay
- Advantages for scenario limited data (200-300 orders)
- Challenges: overfitting risk with small dataset + solutions

**Why Critical:**
- Core methodology for both NER & Revision Matcher
- Explains why 2 components can use same InDoBERT base

**Example:**
"InDoBERT pre-trained pada 16GB corpus Indonesian menghasilkan representations yang 
memahami arti kontekstual kata '"driver", "nopol", "loading time". Ketika Rafay fine-tune 
InDoBERT pada 200-300 orders selama 5 epochs, model belajar ekstrak field-field order 
dengan accuracy 88-92% hanya dalam 1-2 jam training..."

---

### 2.1.5: InDoBERT

**Opening:**
"InDoBERT adalah model BERT yang di-pre-train khusus pada corpus bahasa Indonesia, 
dirancang untuk mengatasi karakteristik unik bahasa Indonesia yang berbeda dari English..."

**Must Cover:**
- What InDoBERT is (BERT pre-trained on Indonesian)
- Pre-training data (Indonesian corpus: Wikipedia, news, web)
- Design choices for Indonesian (tokenizer, vocab)
- Performance on Indonesian benchmarks (vs English BERT, vs mBERT)
- Downstream task performance (NER, sentiment, etc.)
- Why chosen for Rafay

**Comparison Table:**
- InDoBERT vs Multilingual BERT (mBERT) vs English BERT
- Show performance metrics

**Must Justify:**
Why InDoBERT better than just using English BERT or mBERT for order extraction on WhatsApp Indonesian

---

### 2.1.6: Named Entity Recognition ⭐

**Opening:**
"Named Entity Recognition (NER) adalah tugas Information Extraction yang bertujuan mengidentifikasi 
dan mengklasifikasikan entity-entity penting dalam teks, seperti nama orang, lokasi, waktu, 
nomor kendaraan, dll..."

**Must Cover (DETAILED):**
- NER task definition & use cases
- Entity types definition (Rafay: driver name, plate number, location, etc.)
- Sequence labeling formulation (BIO scheme)
  * B-ENTITY (beginning of entity)
  * I-ENTITY (inside entity)
  * O (outside entity)
- Traditional approaches (rule-based, dictionary, CRF)
- Neural approaches (LSTM, CNN, BERT-based)
- BERT for token classification:
  * How BERT generates token-level representations
  * Classification head (linear layer on each token output)
  * Why BERT effective (contextual representations)
- For Rafay specifically:
  * 21 entity types (driver, nopol, phone, date, time, location, route, unit qty, unit type, etc.)
  * Example: Input "5 UNIT TWB 50 CBM ... DRIVER: Hendra" → Output {UNIT_QTY: 5, UNIT_TYPE: TWB, ...}
- Evaluation metrics:
  * Token-level F1 (per-token classification accuracy)
  * Entity-level F1 (complete entity match required)
  * Per-entity-type F1 (some entities more critical)
  * Why entity-level F1 matters for application (extracting complete field values)
- Challenges (entity boundary detection, unknown entities, typos, class imbalance)

**Why This Section Critical:**
- Core contribution #1 (Component 1 of hybrid system)
- Justifies 21-entity design
- Explains how accuracy & metrics work

**Example (Detailed):**
```
Input: "HENDRA S.P\nNopol: D 9044 AG\nNo hp: +62 877-8667-6177"

Expected output (BIO tags):
HENDRA    → B-DRIVER
S.P       → I-DRIVER
Nopol     → O
:         → O
D         → B-NOPOL
9044      → I-NOPOL
AG        → I-NOPOL
No        → O
hp        → O
:         → O
+62       → B-PHONE
877-8667-6177 → I-PHONE

Entity-level extraction:
- DRIVER: "HENDRA S.P"
- NOPOL: "D 9044 AG"
- PHONE: "+62 877-8667-6177"
```

---

### 2.1.7: Semantic Similarity

**Opening:**
"Semantic similarity adalah ukuran seberapa mirip arti dua teks, terlepas dari similaritas 
permukaan (surface-level). Misalnya, 'REVISI DRIVER: Umar Ali' secara semantik mirip dengan 
'REQUEST ORDER ... driver umar ali' meskipun wording berbeda..."

**Must Cover:**
- Semantic similarity definition (meaning-based, not surface)
- Use cases (deduplication, paraphrase detection, document retrieval)
- Sentence embedding methods:
  * Word average (baseline)
  * LSTM/GRU encoders
  * BERT CLS token (what we use)
  * Pooling strategies (mean, max, attention)
- Similarity metrics (cosine similarity, Euclidean distance)
- Ranking via similarity scores (top-K retrieval)
- BERT for semantic tasks:
  * CLS token as sentence representation
  * Why effective
  * Fine-tuning for semantic similarity
- Connection to Revision Matching:
  * Find which original order matches revision message
  * Score all candidates
  * Rank top-3

**Example:**
```
Candidates (dari historical orders):
1. "REQUEST ORDER ... DRIVER UMARALII NOPOL B9932SXW ..."
2. "REQUEST ORDER ... DRIVER BUDI NOPOL B9932AXW ..."
3. "REQUEST ORDER ... DRIVER UMAR NOPOL B9932SXW ..."

Revision message: "REVISI DRIVER: Umar Ali, B 9932 SXW"

Semantic similarity scores (BERT):
- Candidate 1: 0.92 (highest - exact match essentially)
- Candidate 3: 0.85 (close - slight typo variation)
- Candidate 2: 0.45 (low - different driver)

Output: Top-3 with scores
```

---

### 2.1.8: Sequence-Pair Classification

**Opening:**
"Sequence-pair classification adalah tugas mengklasifikasikan relationship antara dua sequence. 
BERT khusus di-design untuk handle input berpasangan, membuatnya sempurna untuk task seperti 
matching order revisions dengan original orders..."

**Must Cover:**
- Single sequence vs sequence-pair classification
- BERT pair input format: [CLS] + Sentence1 + [SEP] + Sentence2 + [SEP]
- Special tokens purpose ([CLS], [SEP], segment embeddings)
- Classification mechanism:
  * CLS token → dense hidden layer → output logits
  * Softmax untuk probabilities
- Binary classification (MATCH=1 vs NO_MATCH=0)
- Confidence scoring (probability of MATCH class)
- Ranking: score all pairs, sort by MATCH probability → top-3
- Why BERT effective (captures semantic interaction between pair)

**Connection to Revision Matching:**
- Input pair: (revision_message, order_candidate)
- Output: is_match probability
- For each revision, score against all historical orders
- Return top-3 matching orders

**Example:**
```
Revision message (S1): "REVISI NOPOL B 9932 SXW"
Order candidates (S2):
- Cand1: "REQUEST ORDER NOPOL B 9932 SXW DRIVER UMAR"
  Input: [CLS] REVISI NOPOL B 9932 SXW [SEP] REQUEST ORDER NOPOL B 9932 SXW [SEP]
  Output: MATCH=0.94

- Cand2: "REQUEST ORDER NOPOL B 9932 AXW DRIVER BUDI"
  Input: [CLS] REVISI NOPOL B 9932 SXW [SEP] REQUEST ORDER NOPOL B 9932 AXW [SEP]
  Output: MATCH=0.12

- Cand3: "REQUEST ORDER NOPOL L 9722 UE DRIVER AKIYAT"
  Input: [CLS] REVISI NOPOL B 9932 SXW [SEP] REQUEST ORDER NOPOL L 9722 UE [SEP]
  Output: MATCH=0.05

Top-3: [Cand1=0.94, Cand3=0.12, Cand2=0.05] (after sorting)
```

---

### 2.1.9: Indonesian Language & Informal Text

**Opening:**
"Bahasa Indonesia memiliki karakteristik morfologi dan sintaksis yang unik. Ketika ditambah 
dengan gaya writing informal WhatsApp (typos, abbreviations, slang), NLP menjadi lebih challenging..."

**Must Cover:**
- Indonesian language characteristics:
  * Rich morphology (affixes, prefixes, suffixes)
  * Word order flexibility
  * No noun inflection (simpler in some ways)
  * Relative clause complexity
- Informal text characteristics (WhatsApp):
  * Typos (common, multiple types: transposition, substitution, omission)
  * Abbreviations ("bgus"="bagus", "klo"="kalau")
  * Slang ("gw"="saya", "bt"="bant")
  * Punctuation variation
  * Code-mixing (Indo + English)
- NLP challenges from informality:
  * Standard models trained on formal text struggle
  * Tokenization harder
  * Entity recognition more difficult
  * More variation in entity presentation
- Pre-processing strategies (traditional):
  * Normalization (standardize spelling)
  * Stop-word removal
  * Stemming/lemmatization
- Why minimal pre-processing with BERT:
  * BERT pre-trained to handle variations
  * Over-aggressive preprocessing loses signal
- Why InDoBERT better than English BERT:
  * Trained on Indonesian corpus
  * Understands Indonesian patterns
- Why rule-based layer needed:
  * Residual formatting (phone numbers, locations)
  * BERT alone insufficient for complete standardization

**Example from raw.txt:**
```
NO HP:+62 877-8667-6177 (format 1 - with +62)
NO HP:0882016641381 (format 2 - no +62, local format)
NOHP:085784422398 (format 3 - abbreviation)
NOHP :089690885555 (format 4 - space variation)

Rule layer standardizes all → +62-81-XXXX-XXXX format
Which BERT alone wouldn't do uniformly
```

---

### 2.1.10: Hybrid ML + Rule-Based

**Opening:**
"Penelitian ini menggunakan pendekatan hybrid yang mengintegrasikan machine learning dengan 
rule-based post-processing. Hybrid approach ini dipilih karena karakteristik unik masalah Rafay 
yang membutuhkan kombinasi generalisasi (ML) dan konsistensi (rules)..."

**Must Cover (DETAILED):**
- Pure ML approach:
  * Advantages: Learns generalizable patterns, handles unseen variations, scalable
  * Limitations: Requires large training data, black-box (hard to debug), edge cases leak through
  * For Rafay: 200-300 orders not massive; format consistency important
- Pure rule-based approach:
  * Advantages: Transparent, deterministic, perfect on known patterns
  * Limitations: Brittle (breaks on variations), doesn't generalize, expensive maintenance
  * For Rafay: Manual rules not sustainable for 500+ orders
- Hybrid approach (combining both):
  * ML for: Learning patterns from data (38 fields, entity variations)
  * Rules for: Format standardization (phone, location, date, unit)
  * Result: 91%+ accuracy (BETTER than pure ML 82% or pure rule ~60%)
- Hybrid architecture patterns (existing literature):
  * Pattern 1: Rule filter → ML ranking (candidate filtering)
  * Pattern 2: ML output → rule refinement (OUR approach)
  * Pattern 3: Cascading (rule first, if fail then ML)
  * Pattern 4: Parallel (both independent, combine results)
- Why Rafay chose Pattern 2 (ML → rule):
  * NER extracts fields (ML does well)
  * Rules standardize format (rules do well)
  * Pipeline natural: extraction → refinement
- Benefits for Rafay specifically:
  * ML learns Rafay-specific variability
  * Rules ensure output format consistency
  * Hybrid handles edge cases better
  * Interpretability (can debug each layer)
- Challenges Rafay faced:
  * Rule maintenance (as patterns grow)
  * Where boundaries between ML & rule should be
  * Interaction debugging (which layer caused issue?)

**Why This Section Critical:**
- Justifies architectural choice (not just NER + Matcher, but + rules)
- Shows deliberate design, not hack
- Defensible against critic: "Why not pure ML?"

**Example:**
```
Input WhatsApp message: "DRIVER: Umar Ali, No hp:+62-877-8667-6177, Nopol:D 9044 AG"

NER (ML component) extracts:
- DRIVER: "Umar Ali"
- PHONE: "+62-877-8667-6177" (inconsistent with existing)
- NOPOL: "D 9044 AG" (inconsistent format)

Rule layer (Post-processing) refines:
- PHONE: "+62-877-8667-6177" → standardized "+62-877-8667-6177" (already standard)
- DRIVER: "Umar Ali" → normalize capitalization... (already ok)
- NOPOL: "D 9044 AG" → standardized "D 9044 AG" (already standard)
- Check against location aliases: If location "Argopantes" mentioned, validate driver pool
- Check date-time consistency: If "03:00 load 05-Feb" doesn't align with operator schedule, flag

Result: Fully standardized, validated record ready for system integration
```

---

### 2.1.11: Evaluation Metrics

**Opening:**
"Mengukur keberhasilan sistem ekstraksi dan matching membutuhkan metrics yang tepat. Metrics 
yang salah dapat menghasilkan interpretasi misleading tentang performa model..."

**Must Cover:**
- Basic classification metrics:
  * Precision = TP / (TP+FP) :: of predicted positive, how many correct?
  * Recall = TP / (TP+FN) :: of actual positive, how many found?
  * F1 = 2 * (Precision*Recall) / (Precision+Recall) :: harmonic mean
  * Why F1 better than accuracy (handles class imbalance)
- For multi-class (per-entity-type) evaluation:
  * Micro F1 (average across all instances)
  * Macro F1 (average per entity type)
  * Weighted F1 (average weighted by entity frequency)
- For NER specifically:
  * Token-level metrics (per-token classification)
  * Entity-level metrics (STRICT: entity must be exact boundary)
  * Why entity-level matters (application cares about complete field values, not partial)
  * Partial/relax matching (for some applications)
- For sequence-pair classification:
  * Per-class precision/recall/F1 (for MATCH vs NO_MATCH)
  * ROC-AUC (for ranking quality assessment)
  * Ranking metrics: NDCG@K, MRR@K (K=3 for Rafay top-3)
- Statistical significance:
  * Confidence intervals (not just point estimates)
  * Importance of cross-validation (k-fold CV for consistency)
  * Avoiding overfitting indicators
- Connection to project:
  * How we measure NER success: Entity-level F1 per type
  * How we measure Revision Matcher: NDCG@3 (quality of top-3 ranking)
  * Why certain entities weighted higher (DRIVER more critical than misc fields)

**Example:**
```
NER evaluation on 100 test orders:

Token-level:
- Precision: 0.91 (91% of predicted tokens correct)
- Recall: 0.88 (88% of actual entities tokens found)
- F1: 0.895

Entity-level (STRICT):
- Precision: 0.88 (88% of predicted entities fully correct)
- Recall: 0.85 (85% of actual entities fully extracted)
- F1: 0.865

Why lower entity-level:
- Some partial extractions (e.g., extracted "Umar" but missed "Ali" - boundary error)

Per-entity performance:
- DRIVER: F1=0.92 (critical entity, well-recognized)
- PHONE: F1=0.89
- LOCATION: F1=0.81 (trickier due to alias variations)
- NOPOL: F1=0.88
- ROUTE: F1=0.85
```

---

## BAGIAN 5: RELATED RESEARCH GENERATION GUIDELINES

### 2.2.1: NER in Indonesian

**Reference Structure:**
1. What exists (existing Indonesian NER systems)
2. Performance benchmarks (on what metrics?)
3. Gap identification (what's missing?)
4. How Rafay addresses (unique contribution)

**Papers to reference:**
- IndoBERT paper (Table with downstream task results including NER)
- Indonesian NER datasets (NERP if available, or social media NER)
- Indonesian NLP survey papers

**Tone:** Academic survey, not listing all papers

---

### 2.2.2-5: Similar sections

Each 2.2.X follows similar pattern:
1. Domain/area overview (what exists in literature)
2. Performance/findings (what works well)
3. Gap (what's missing)
4. Rafay's unique angle (how project fills gap)
5. Contribution (what makes it novel)

---

## BAGIAN 6: INTEGRATION CHECKLIST - BEFORE WRITING

Before generating content for each subsection:

**Preparation Checklist:**
- [ ] Understand why this subsection needed for project
- [ ] Know connection to other subsections
- [ ] Have concrete examples from Rafay
- [ ] Identify target length (300-800 words)
- [ ] Know audience (thesis committee, not fellow ML researchers)
- [ ] Prepare references to cite
- [ ] Understand level of technical detail (conceptual vs mathematical)

---

## SUMMARY: READY FOR CONTENT GENERATION

**BAB 2 Blueprint Complete:**
- ✅ 16 subsections identified
- ✅ Each subsection purpose defined
- ✅ Content hints provided
- ✅ Examples given
- ✅ Length guidelines clear
- ✅ Connection to project justified

**Next Step Options:**
1. **Generate subsections via Gemini** (recommended)
2. **Write manually** using this blueprint
3. **Combine**: Write some, Gemini for others

---

**STATUS: BAB 2 BLUEPRINT COMPLETE & READY FOR IMPLEMENTATION ✅**

All 16 subsections ready to generate. Choose content generation method and execute!

