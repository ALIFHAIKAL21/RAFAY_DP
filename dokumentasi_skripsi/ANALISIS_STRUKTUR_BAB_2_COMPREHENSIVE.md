# 📚 ANALISIS STRUKTUR BAB 2 - LANDASAN TEORI
## untuk RAFAY IDP v2.0 - Hybrid Machine Learning

**Status:** Deep Analysis + Comprehensive Structure Design  
**Project Context:** Hybrid NER + Revision Matcher berbasis InDoBERT  
**Approach:** Bottom-up dari project components → Identify required theory  
**Output:** BAB 2 structure blueprint (NOT generic, spesifik untuk project)

---

## BAGIAN 1: PROJECT COMPONENTS MAPPING → REQUIRED THEORY

### Technical Stack RAFAY:

```
RAFAY IDP v2.0
├─ COMPONENT 1: NER (Named Entity Recognition)
│  ├─ Base Model: indolem/indobert-base-uncased
│  ├─ Task: Token Classification (21 entity types, BIO scheme)
│  ├─ Architecture: BERT + linear classification layer
│  ├─ Learning Approach: Transfer Learning (fine-tuning)
│  └─ Required Theory: NLP, Word Embedding, BERT, Transfer Learning, NER
│
├─ COMPONENT 2: Revision Matcher
│  ├─ Base Model: indobenchmark/indobert-base-p2
│  ├─ Task: Sequence-pair classification (semantic similarity)
│  ├─ Architecture: BERT + pooling + classification layer
│  ├─ Learning Approach: Transfer Learning (fine-tuning)
│  └─ Required Theory: Semantic Similarity, Sentence Embeddings, Classification
│
├─ COMPONENT 3: Rule-Based Layer (Post-processing)
│  ├─ Function: Format standardization, validation
│  ├─ Logic: Conditional rules + pattern matching
│  ├─ Learning Approach: Manual-crafted from observation
│  └─ Required Theory: Pattern Recognition, Heuristic Methods
│
├─ FOUNDATION: InDoBERT (Indonesian BERT)
│  ├─ Base: Transformer BERT
│  ├─ Specialized: Indonesian language context
│  ├─ Architecture: 12-layer, 768-hidden, 12-heads
│  └─ Required Theory: Transformers, BERT, Pre-training, Language Models
│
└─ DATA CONTEXT: WhatsApp Unstructured Indonesian Text
   ├─ Characteristics: Informal language, typos, abbreviations
   ├─ Source: Single channel (WhatsApp)
   ├─ Problem: Variability, incomplete information
   └─ Required Theory: Natural Language Understanding, Text Processing
```

### Theory Requirements Identified:

**TIER 1: Foundation (Essential)**
- ✅ Natural Language Processing (NLP) - Fundamentals
- ✅ Word Embeddings & Representations
- ✅ Transformer Architecture
- ✅ BERT Model & Pre-training Approach
- ✅ Transfer Learning Methodology
- ✅ Named Entity Recognition (NER) - Task & Methods

**TIER 2: Specific Components (Critical)**
- ✅ InDoBERT - Indonesian-Specific BERT
- ✅ Semantic Similarity & Sentence Embeddings
- ✅ Sequence Classification & Pair Classification
- ✅ Fine-tuning & Transfer Learning Strategy
- ✅ Evaluation Metrics for NLP Tasks

**TIER 3: Application Context (Important)**
- ✅ Indonesian Language Challenges (Morphology, Syntax)
- ✅ Order Processing Domain (Logistics Context)
- ✅ Hybrid Approaches (ML + Rule-based)
- ✅ Text Preprocessing for Unstructured Data

**TIER 4: Related Research (Reference)**
- ✅ NER Systems in Indonesian
- ✅ Semantic Matching in Logistics/E-commerce
- ✅ Hybrid ML Approaches
- ✅ Similar Order Processing Systems

---

## BAGIAN 2: WHAT TO INCLUDE vs EXCLUDE

### ✅ INCLUDE (Directly relevant to project):

1. **NLP Fundamentals** - Why? Project is core NLP task
   - Tokenization, POS tagging, NER concepts
   - Why NOT over-detail: Project uses pre-built models, not implementing tokenizer from scratch

2. **Word Embeddings** - Why? Foundation for understanding BERT
   - Word2Vec, GloVe, FastText concepts
   - Why necessary: Explain why BERT embeddings better than traditional embeddings
   - Why NOT deep: Project not creating custom embeddings

3. **Transformer Architecture** - Why? BERT is transformer-based
   - Self-attention mechanism (conceptual)
   - Multi-head attention
   - Feedforward layers
   - Why NOT detailed: Project uses pre-trained BERT, not building transformers
   - How much: Enough to understand why BERT works for 2 tasks simultaneously

4. **BERT Model** - Why? Foundation of entire project
   - BERT architecture (high-level)
   - Pre-training objectives (MLM, NSP)
   - Why it transfers well
   - Bidirectional context advantage
   - Why detailed: Core to understanding both NER + Revision Matcher performance

5. **Transfer Learning** - Why? Project methodology
   - Fine-tuning vs feature extraction (explain choice: fine-tuning)
   - Why transfer learning for limited data (200-300 orders)
   - Advantages for domain adaptation
   - Common pitfalls (overfitting with small data)

6. **InDoBERT** - Why? Specific foundation model
   - Design choices for Indonesian
   - Pre-training data & methodology
   - Language characteristics it capture
   - Performance on Indonesian NLP tasks
   - Why detailed: Justifies choice over multilingual BERT or English BERT

7. **Named Entity Recognition (NER)** - Why? Component 1
   - NER task definition & taxonomy
   - Sequence labeling (BIO scheme)
   - Metrics (precision, recall, F1 per entity type)
   - NER approaches (rule-based, ML, hybrid)
   - Why 21 entity types suitable for orders
   - Deep: This is core component

8. **Semantic Similarity & Sentence Embeddings** - Why? Component 2
   - Semantic similarity concepts
   - Sentence representation methods
   - Sequence-pair classification approach
   - Why suitable for revision matching
   - Ranking/scoring mechanisms (top-3 output)

9. **Sequence Classification** - Why? Component 2 specific
   - Binary/multi-class classification on sequences
   - Approaches (CLS token, pooling, attention)
   - Why BERT can handle sequence-pair directly
   - Confidence scoring

10. **Indonesian Language Characteristics** - Why? Context-specific
    - Morphological complexity
    - Word order variations
    - Informal writing (WhatsApp style)
    - Typos & abbreviations common
    - Why important: Justifies preprocessing rules + why rule layer needed

11. **Hybrid Approaches (ML + Rule-Based)** - Why? Project architecture
    - When hybrid needed
    - Advantages of combining ML + rules
    - Common patterns in ML+rule systems
    - Example from similar projects
    - Why detailed: Justify design choice of 2 components + rule layer

12. **Text Preprocessing** - Why? Practical necessity
    - Handling informal text
    - Phone number, location normalization
    - Typo handling approaches
    - Why important: Real operational data messy

13. **Evaluation Metrics for NLP** - Why? Methodology
    - Precision, Recall, F1-score
    - Entity-level vs token-level metrics (for NER)
    - Confusion matrix interpretation
    - Why important: How we measure success

### ❌ EXCLUDE (Not directly relevant):

- ❌ Machine Translation - Different task
- ❌ Sentiment Analysis - Different task
- ❌ Question Answering - Different task
- ❌ Text Summarization - Different task
- ❌ Language Generation - Different task
- ❌ Image Processing - Different domain
- ❌ Custom Transformer Building - Project uses pre-built
- ❌ Deep hyperparameter tuning theory - Beyond scope
- ❌ Distributed/Federated Learning - Project single-machine
- ❌ Advanced optimization (Adam, SGD tricks) - Handled by framework
- ❌ Adversarial examples - Not in scope
- ❌ Other languages deeply - Project Indonesian-focused

---

## BAGIAN 3: RELATED RESEARCH TO INCLUDE

### Research Category 1: NER Systems (Indonesian & Similar)

**Papers to reference:**
- NER on Indonesian social media
- NER on informal text / WhatsApp-like data
- Indonesian NER benchmarks
- BERT for Indonesian NER
- InDoBERT performance on NER tasks

**Why important:** Show existing approaches, gap analysis (why 2-model?)

### Research Category 2: Semantic Matching & Similarity

**Papers to reference:**
- Semantic similarity in e-commerce/order systems
- Sequence-pair classification with BERT
- Candidate ranking/retrieval in logistics
- Hybrid ML approaches in order matching
- Top-K recommendation in search

**Why important:** Justify revision matcher approach

### Research Category 3: Hybrid ML + Rule-Based

**Papers to reference:**
- Hybrid ML-rule systems in NLP
- When rules outperform pure ML
- Rule learning vs manual specification
- Examples: order processing, logistics, data entry

**Why important:** Justify design architecture (NER + Matcher + rules)

### Research Category 4: Indonesian NLP & InDoBERT

**Papers to reference:**
- IndoBERT paper & documentation
- Comparison: IndoBERT vs mBERT vs English BERT
- Indonesian language challenges
- Pre-training on Indonesian data
- Downstream task performance

**Why important:** Justify technology choice

### Research Category 5: Similar Applications (Logistics/Order Processing)

**Papers to reference:**
- Order processing automation
- Data extraction from unstructured messages
- Revision/amendment matching
- Multi-modal order processing
- Similar logistics AI systems

**Why important:** Show practical context, justify relevance

---

## BAGIAN 4: COMPREHENSIVE BAB 2 STRUCTURE FOR RAFAY

### Proposed Structure:

```
BAB II. LANDASAN TEORI

2.1. Tinjauan Pustaka (Literature Review)
├─ 2.1.1. Natural Language Processing (Foundational)
│  └─ Definition, tasks, NLP pipeline basics
│
├─ 2.1.2. Word Embeddings dan Representasi Teks
│  ├─ Word2Vec (concept)
│  ├─ GloVe (concept)
│  └─ Why embeddings matter for BERT
│
├─ 2.1.3. Transformer Architecture
│  ├─ Self-attention mechanism
│  ├─ Multi-head attention
│  └─ Why transformers revolutionized NLP
│
├─ 2.1.4. BERT Model dan Transfer Learning
│  ├─ BERT architecture overview
│  ├─ Pre-training objectives (MLM, NSP)
│  ├─ Fine-tuning approach
│  ├─ Why BERT for sequence tasks
│  └─ Advantages of transfer learning for limited data
│
├─ 2.1.5. InDoBERT: BERT untuk Bahasa Indonesia
│  ├─ Design & pre-training methodology
│  ├─ Indonesian language characteristics
│  ├─ Performance on Indonesian benchmarks
│  ├─ Comparison dengan multilingual BERT
│  └─ Why InDoBERT chosen for Rafay project
│
├─ 2.1.6. Named Entity Recognition (NER)
│  ├─ NER task definition & use cases
│  ├─ Sequence labeling & BIO scheme
│  ├─ NER approaches (rule-based, ML, neural)
│  ├─ BERT for token classification
│  ├─ Entity types for order processing domain
│  ├─ Performance metrics (entity-level, token-level)
│  └─ Why NER critical for order extraction
│
├─ 2.1.7. Semantic Similarity dan Sentence Embeddings
│  ├─ Semantic similarity definition & use cases
│  ├─ Sentence embedding methods
│  ├─ BERT for sentence representation (CLS token, pooling)
│  ├─ Similarity metrics (cosine, Euclidean)
│  └─ Why semantic similarity for revision matching
│
├─ 2.1.8. Sequence-Pair Classification dengan BERT
│  ├─ Sequence classification task
│  ├─ Sequence-pair input format
│  ├─ BERT mechanism for pair classification
│  ├─ Applications in semantic matching
│  └─ Output: confidence scoring & ranking
│
├─ 2.1.9. Karakteristik Bahasa Indonesia dan Teks Informal
│  ├─ Indonesian morphology & syntax
│  ├─ Informal writing (WhatsApp, SMS)
│  ├─ Typos, abbreviations, slang
│  ├─ Challenges untuk NLP Indonesian
│  └─ Pre-processing strategies
│
├─ 2.1.10. Pendekatan Hybrid: Machine Learning + Rule-Based
│  ├─ When hybrid approach needed
│  ├─ ML advantages & limitations
│  ├─ Rule-based advantages & limitations
│  ├─ Combining ML + rules (architecture patterns)
│  ├─ Examples dari similar systems
│  └─ Why hybrid for Rafay (2 ML components + rule layer)
│
└─ 2.1.11. Metrics Evaluasi untuk Tugas NLP
   ├─ Precision, Recall, F1-Score
   ├─ Per-class evaluation (untuk multi-entity NER)
   ├─ Macro vs Micro averaging
   ├─ Confusion matrix interpretation
   └─ Performance analysis strategies

2.2. Penelitian Terkait (Related Work)
├─ 2.2.1. Sistem NER di Bahasa Indonesia
│  ├─ Existing Indonesian NER systems
│  ├─ Performance benchmarks
│  ├─ Gap: Informal text, order domain specific
│  └─ How Rafay project addresses gaps
│
├─ 2.2.2. Semantic Matching dalam E-Commerce dan Logistik
│  ├─ Order matching/revision matching in literature
│  ├─ Candidate ranking approaches
│  ├─ ML-based semantic matching
│  ├─ Gap: Limited work on revision matching di Indonesian context
│  └─ How Rafay project contributes
│
├─ 2.2.3. Sistem Hybrid Machine Learning + Rule-Based
│  ├─ Examples dari similar projects
│  ├─ Design patterns & best practices
│  ├─ When hybrid outperforms pure ML
│  ├─ Implementation challenges
│  └─ How Rafay hybrid approach positioned
│
├─ 2.2.4. Aplikasi InDoBERT di Downstream Tasks
│  ├─ Published work on InDoBERT
│  ├─ NER performance dengan InDoBERT
│  ├─ Semantic tasks dengan InDoBERT
│  ├─ Transfer learning results
│  └─ Gap: Limited work on 2-task simultaneous architecture
│
└─ 2.2.5. Sistem Pemrosesan Pesanan Otomatis
   ├─ Logistics data extraction systems
   ├─ Automated order processing literature
   ├─ Similar projects (international context)
   ├─ Challenges dalam order processing automation
   └─ How Rafay addresses operational reality

2.3. Gap Analysis & Positioning (Optional but recommended)
├─ Existing solutions' limitations
├─ Why Rafay project unique
└─ Contribution to Indonesian logistics NLP
```

---

## BAGIAN 5: DETAILED EXPLANATION PER SUBSECTION

### 2.1.1. Natural Language Processing
**Length:** ~300-400 words  
**Should include:**
- NLP definition & scope
- Traditional NLP tasks (tokenization, POS, parsing)
- Modern NLP (deep learning era)
- Why NLP challenging (ambiguity, context dependency)
- Relevance to order processing

**Should NOT:**
- Deep linguistics theory
- All possible NLP tasks (focus on relevant ones)

### 2.1.2. Word Embeddings
**Length:** ~400-500 words  
**Should include:**
- Why embeddings needed (vs one-hot encoding)
- Word2Vec (skip-gram, CBOW) - concept level
- GloVe - concept level
- Limitations of static embeddings
- Why contextual embeddings (like BERT) better
- Connection to project: Why BERT embeddings needed for order extraction

**Should NOT:**
- Mathematical derivations
- Implement embeddings from scratch

### 2.1.3. Transformer Architecture
**Length:** ~500-600 words  
**Should include:**
- Traditional RNN/LSTM limitations (sequential processing)
- Self-attention concept (high-level, visual explanation helpful)
- Multi-head attention intuition
- Positional encoding
- Why transformers faster & better for long sequences
- Connection to BERT (transformer-based)

**Should NOT:**
- Full mathematical derivation of attention
- Implementation details
- Comparison of all variants (RoBERTa, ELECTRA, etc) - focus on why BERT chosen

### 2.1.4. BERT Model dan Transfer Learning
**Length:** ~600-800 words (CRITICAL section)  
**Should include:**
- BERT architecture (12 layers, 768 hidden, 12 heads for base)
- Bidirectional training (why better than unidirectional)
- Pre-training objectives:
  * Masked Language Model (MLM) - explain why this works
  * Next Sentence Prediction (NSP) - relevance
- Fine-tuning approach vs feature extraction (explain choice)
- Advantages for limited data scenarios
- Challenges: overfitting with small dataset (relevant to 200-300 orders)
- How BERT layers capture linguistic knowledge
- Connection to project: Why BERT fits both NER + semantic matching

**Should NOT:**
- All BERT variants (RoBERTa, ALBERT, etc) - focus on why base BERT chosen
- Pre-training details (already in corpus, not project scope)

### 2.1.5. InDoBERT
**Length:** ~400-500 words  
**Should include:**
- What is InDoBERT (BERT pre-trained on Indonesian text)
- Pre-training data (Indonesian corpus)
- Design choices for Indonesian (character-level tokenizer, corpus selection)
- Architecture (same as BERT base)
- Performance comparison:
  * vs multilingual BERT (mBERT) - why InDoBERT better
  * vs English BERT transferred - why language-specific better
- Downstream task performance on Indonesian benchmarks
- Why chosen for Rafay project (Indonesian order data, better performance)
- Available resources & community support

**Should NOT:**
- Detailed pre-training procedure (not relevant)
- Comparison with ALL Indonesian NLP models (focus on relevant ones)

### 2.1.6. Named Entity Recognition (NER)
**Length:** ~700-800 words (CRITICAL - Component 1)  
**Should include:**
- NER definition & use cases
- Why NER important for information extraction
- Entity types definition & taxonomy
- Sequence labeling formulation
- BIO tagging scheme (explain B, I, O tags)
- Traditional NER approaches (rule-based, dictionary, CRF)
- Neural NER approaches (LSTM, CNN, BERT-based)
- BERT for token classification:
  * How BERT generates token representations
  * Classification head (linear layer on each token)
  * Why BERT effective for NER
- Entity types for order processing (21 types from Rafay)
- Evaluation metrics:
  * Token-level F1
  * Entity-level F1 (strict, partial, relax)
  * Why entity-level matters for applications
- Challenges in NER (entity boundary detection, unknown entities, class imbalance)
- Why important for Rafay (extract 21 fields from unstructured messages)

**Should NOT:**
- Implement CRF from scratch
- All NER models in literature (focus on relevant ones)

### 2.1.7. Semantic Similarity & Sentence Embeddings
**Length:** ~500-600 words  
**Should include:**
- Semantic similarity definition (no surface-form similarity, meaning-based)
- Use cases (duplicate detection, paraphrase, document retrieval)
- Sentence embedding methods:
  * Averaging word embeddings (simple baseline)
  * LSTM/GRU encoders
  * BERT CLS token
  * Pooling strategies (mean, max, attention)
- Similarity metrics (cosine similarity, Euclidean distance)
- Ranking via similarity scores
- BERT for semantic tasks:
  * Why CLS token effective for sentence representation
  * Pooling strategies
  * Fine-tuning for semantic tasks
- Connection to revision matching (find similar orders)
- Challenges (semantic ambiguity, length differences, domain-specific meaning)
- Why important for Rafay (match revision messages with original orders)

**Should NOT:**
- Detailed mathematical formulas
- All sentence embedding methods (focus on BERT-relevant ones)

### 2.1.8. Sequence-Pair Classification
**Length:** ~400-500 words  
**Should include:**
- Sequence classification vs sequence-pair classification
- Use cases (paraphrase, semantic textual similarity, question-answer relevance)
- How BERT handles sequence pairs:
  * [CLS] + Sent1 + [SEP] + Sent2 + [SEP] format
  * Special tokens ([CLS], [SEP]) purpose
  * Segment embeddings (differentiate sent1 from sent2)
- Classification mechanism (CLS token → dense layer → output)
- Binary classification (match vs no-match) for revision matching
- Confidence scoring & ranking (top-3 candidates)
- Why BERT effective for sequence-pair tasks
- Connection to project (revision message vs order candidates)
- Challenges (class imbalance, false positives, ambiguous pairs)

**Should NOT:**
- Alternative architectures (Siamese networks, etc) - focus on BERT approach

### 2.1.9. Karakteristik Bahasa Indonesia & Teks Informal
**Length:** ~400-500 words  
**Should include:**
- Indonesian language characteristics:
  * Morphological richness (affixation)
  * Word order flexibility (SVO but flexible)
  * Absence of noun inflection (no gender, case)
  * Syntactic complexity (relative clauses)
- Informal writing characteristics (WhatsApp, SMS):
  * Typos (common, various types)
  * Abbreviations ("bgus" for "bagus")
  * Slang ("klo" for "kalau")
  * Punctuation variation
  * Code-mixing (Indonesian + English)
- Impact on NLP:
  * RNN/CNN struggling with morphological richness
  * Tokenization challenges
  * Entity boundary detection harder
  * Spelling variation challenges
- Pre-processing strategies:
  * Normalization (standardize spellings)
  * Tokenization (handle affixes)
  * Stopword removal
  * Why minimal preprocessing for BERT (learns from pre-training)
- Why InDoBERT better than generic for Indonesian (captures linguistic patterns)
- Why rule layer needed (handle residual informal patterns)

**Should NOT:**
- Detailed linguistic theory (focus on NLP-relevant aspects)
- All Indonesian dialects/regional variations

### 2.1.10. Pendekatan Hybrid: ML + Rule-Based
**Length:** ~500-600 words  
**Should include:**
- Pure ML approach:
  * Advantages: Generalizable, learns from data, scalable
  * Limitations: Needs lots of data, black-box, edge cases, rule conflicts implicit
- Pure rule-based approach:
  * Advantages: Transparent, handles known patterns perfectly, deterministic
  * Limitations: Brittle, doesn't generalize, expensive maintenance, captures rules manually
- Why hybrid:
  * Combine generalization (ML) + interpretability & known patterns (rules)
  * Handle edge cases (rules) + learn from data (ML)
  * Pragmatic given resource constraints
- Hybrid architecture patterns:
  * ML output → rule refinement (our approach)
  * Rule candidate filter → ML ranking
  * Cascading (rule first, ML if rule fails)
  * Parallel (ML + rule, combine results)
- Benefits for Rafay:
  * ML learns field extraction patterns
  * Rules standardize format (phone numbers, locations)
  * Combination achieves 91%+ accuracy
- Challenges:
  * Rule maintenance
  * Rule-ML interaction debugging
  * Where boundaries between ML & rule should be
- Examples from literature (similar logistics systems)
- Why justified for Rafay (operational reality, limited data, format consistency important)

**Should NOT:**
- All hybrid system types (focus on relevant pattern)
- Detailed rule engine implementation

### 2.1.11. Metrics Evaluasi untuk NLP
**Length:** ~400-500 words  
**Should include:**
- Classification metrics (Precision, Recall, F1-Score):
  * Definitions & formulas
  * Why F1 better than accuracy (class imbalance)
  * Micro vs Macro averaging
  * Weighted averaging
- For NER specifically:
  * Token-level metrics (per-token classification)
  * Entity-level metrics (complete entity match)
  * Why entity-level matters (for app usability)
  * Strict vs partial vs relaxed matching
  * Per-entity-type evaluation (some entities more important)
- Confusion matrix:
  * True Positive, False Positive, False Negative, True Negative
  * How to interpret (Type I vs Type II errors)
  * Why matters for different applications
- For sequence-pair classification:
  * Precision/Recall/F1 per class
  * ROC-AUC for ranking quality
  * Ranking metrics (NDCG, MRR for top-K recommendations)
- Statistical significance:
  * Confidence intervals on metrics
  * Why cross-validation important
  * Avoiding overfitting
- Connection to project evaluation (how we measure NER success, Revision Matcher ranking quality)

**Should NOT:**
- Complex metrics (unless specifically needed)
- Exhaustive list of all possible metrics

---

## BAGIAN 6: RELATED RESEARCH (2.2) GUIDANCE

### 2.2.1. Sistem NER di Bahasa Indonesia
**Location to find:**
- IndoBERT paper (shows NER performance on Indonesian)
- Indonesian NER benchmarks (NERP dataset; Indonesian corpus)
- Social media NER papers (Twitter, informal text)
- BLAH (Bank of Language Access and Hybridity) - Indonesian corpus

**Key takeaway for Rafay:**
- Existing NER models perform well on formal text
- Gap: Informal text (WhatsApp), domain-specific (order processing)
- Our contribution: NER fine-tuned specifically for Rafay's informal order messages

### 2.2.2. Semantic Matching dalam E-Commerce & Logistik
**Reference papers:**
- E-commerce product matching/deduplication
- Order reconciliation systems
- Document similarity in legal/logistics domain
- Similar systems: DHL, Amazon logistics (conceptual reference)

**Key takeaway:**
- Semantic matching is established problem in e-commerce
- Gap: Limited work on revision matching in Indonesian context
- Our contribution: Sequence-pair BERT for matching revision messages with original orders

### 2.2.3. Sistem Hybrid ML + Rule-Based
**Examples:**
- Hybrid NER (ML extraction + rule-based validation)
- Information extraction systems
- Data quality systems (combining automatic filling + manual rules)

**Key takeaway:**
- Hybrid approach proven effective when data limited & rules clear
- Our contribution: Designed hybrid specifically for Rafay constraints

### 2.2.4. Aplikasi InDoBERT di Downstream Tasks
**What exists:**
- Original InDoBERT paper
- Various downstream tasks using InDoBERT (sentiment, POS, etc.)
- Comparison studies (InDoBERT vs mBERT)

**Gap:**
- Limited work on simultaneous 2-task architecture with InDoBERT
- Our contribution: InDoBERT for dual NER + semantic matching

### 2.2.5. Sistem Pemrosesan Pesanan Otomatis
**Research context:**
- Logistics automation literature
- Order processing workflows
- Similar projects (international context)
- Operational challenges in automation

**Key takeaway:**
- Situate project in broader automation context
- Show why order extraction critical for efficiency
- Business relevance

---

## BAGIAN 7: WORD COUNT ESTIMATION PER SUBSECTION

| Section | Subsections | Estimated Words | Notes |
|---------|-----------|------------------|-------|
| 2.1.1 | NLP foundational | 400 | Less detail, basic concepts |
| 2.1.2 | Word embeddings | 500 | Conceptual, not implementation |
| 2.1.3 | Transformer | 600 | Critical architecture, detailed |
| 2.1.4 | BERT & Transfer | 800 | **CRITICAL**, detailed explanation |
| 2.1.5 | InDoBERT | 500 | Specific to project |
| 2.1.6 | NER | 800 | **CRITICAL (Component 1)**, detailed |
| 2.1.7 | Semantic similarity | 600 | Important for Revision Matcher |
| 2.1.8 | Seq-pair classification | 500 | Specific to Component 2 |
| 2.1.9 | Indonesian/informal text | 500 | Context-specific |
| 2.1.10 | Hybrid ML+rule | 600 | Justifies architecture |
| 2.1.11 | Evaluation metrics | 500 | Methodology |
| **2.1 TOTAL** | **11 subsections** | **~6,400** | Comprehensive foundation |
| 2.2.1 | NER in Indonesian | 400 | Related work |
| 2.2.2 | Semantic matching | 400 | Gap analysis |
| 2.2.3 | Hybrid systems | 350 | Positioning |
| 2.2.4 | InDoBERT apps | 350 | Tech landscape |
| 2.2.5 | Order processing | 400 | Application context |
| **2.2 TOTAL** | **5 subsections** | **~1,900** | Survey existing work |
| **GRAND TOTAL** | **16 subsections** | **~8,300** | Full BAB 2 |

**Note:** Typical thesis BAB 2 = 8,000-12,000 words. Our structure = ~8,300 words COMPREHENSIVE but NOT overload.

---

## BAGIAN 8: STRUCTURE NOT TO INCLUDE (Why Excluded)

### ❌ Over-Inclusion Examples:

**Machine Translation Fundamentals**
- Why exclude: Project not translation task
- Focus: NER & semantic matching, not generation

**Distributed Systems / Federated Learning**
- Why exclude: Project single-machine, not distributed
- Scope: Practical MVP development

**Adversarial Examples / Robustness**
- Why exclude: Not in project scope, over-advanced
- Focus: Practical performance, not adversarial hardening

**All BERT Variants (RoBERTa, ELECTRA, DeBERTa, etc)**
- Why exclude: Over-detail for project scope
- Include: Why InDoBERT chosen instead

**Information Retrieval Theory**
- Why exclude: While Revision Matcher similar to IR candidate ranking, deep IR theory not needed
- Include: Only ranking/top-K concepts relevant to Revision Matcher

**Neural Machine Translation Architecture**
- Why exclude: Different task (generation vs extraction/matching)
- Include: NER & seq-pair classification only

### ✅ Appropriately Scoped:

**NER Section Length:** 800 words (not 200, not 2000)
- Long enough to explain BIO scheme, metrics, why BERT applicable
- Short enough to avoid implementation details

**Semantic Matching:** 600 words (not 100, not 1500)
- Covers concept, BERT mechanism, connection to revision matching
- Doesn't go into full IR literature

**Hybrid Section:** 600 words (not 100, not 1500)
- Explains philosophy, patterns, relevance to Rafay
- Doesn't exhaustively cover all hybrid architectures in literature

---

## BAGIAN 9: HOW STRUCTURE REFLECTS PROJECT REALITY

### Project Architecture → BAB 2 Structure Mapping:

```
PROJECT COMPONENTS                          BAB 2 COVERAGE
├─ NER (Component 1)        →   2.1.6 NER + 2.1.4 BERT token classification
├─ Revision Matcher (Comp 2) →   2.1.7-2.1.8 Semantic similarity + seq-pair
├─ Rule Layer (Comp 3)       →   2.1.10 Hybrid approaches
├─ InDoBERT (Foundation)     →   2.1.5 InDoBERT specifically
├─ WhatsApp data (Context)   →   2.1.9 Indonesian/informal text
├─ 21 entities (Domain)      →   2.1.6 NER entity types for orders
├─ Transfer learning (Method) →   2.1.4 BERT + Transfer Learning
├─ Evaluation approach       →   2.1.11 NLP evaluation metrics
└─ Related work              →   2.2.1-2.2.5 Positioned vs existing

HASIL: BAB 2 is NOT generic literature review
       but SPECIFICALLY justified for RAFAY project
```

### Why This Structure PERFECT for RAFAY (not generic):

✅ **Focused on NER + Semantic Matching** (2 core components)  
✅ **InDoBERT-specific** (not generic multilingual BERT discussion)  
✅ **Hybrid approaches justified** (not pure ML)  
✅ **Indonesian context** (not English-only examples)  
✅ **Transfer learning emphasis** (200-300 orders context)  
✅ **Entity-type specific** (order domain, 21 entities)  
✅ **Evaluation metrics for application** (not theoretical metrics only)  

---

## BAGIAN 10: QUALITY CHECKLIST FOR BAB 2 STRUCTURE

**Structure Comprehensiveness:**
- [ ] ✅ Covers all technical components (NER, Matcher, Rules)
- [ ] ✅ Covers all theoretical foundations (BERT, embedding, transformers)
- [ ] ✅ Covers domain context (Indonesian, informal text)
- [ ] ✅ Covers methodology (transfer learning, evaluation)
- [ ] ✅ Covers related work (5 areas of research)

**Not Over-Inclusion:**
- [ ] ✅ Excludes unrelated tasks (translation, summarization)
- [ ] ✅ Excludes over-advanced topics (adversarial, distributed learning)
- [ ] ✅ Excludes implementation details (code, hyperparameter theory)
- [ ] ✅ Excludes exhaustive literature (selective, focused)

**Accuracy to Project:**
- [ ] ✅ Structure reflects actual components used
- [ ] ✅ Technology choices justified (InDoBERT vs alternatives)
- [ ] ✅ Architecture decisions supported (hybrid approach)
- [ ] ✅ Business constraints incorporated (200-300 orders, WhatsApp data)

**Academic Rigor:**
- [ ] ✅ Grounded in established literature
- [ ] ✅ Concepts clearly explained at appropriate depth
- [ ] ✅ Connections between sections logical
- [ ] ✅ Related work positioned properly

**Feasibility:**
- [ ] ✅ Can be written by graduate student (not requiring PhD-level expertise)
- [ ] ✅ Reasonable word count (~8,300 words)
- [ ] ✅ References readily available
- [ ] ✅ Fits standard thesis timeline

---

## SUMMARY: BAB 2 STRUCTURE BLUEPRINT

**Type:** Landasan Teori (Literature Review + Theoretical Foundation)

**Organization:** 2.1 Tinjauan Pustaka (11 subsections, ~6,400 words) + 2.2 Penelitian Terkait (5 areas, ~1,900 words)

**Total Word Count:** ~8,300 words (comprehensive, not bloated)

**Key Characteristics:**
- ✅ Specific to RAFAY project (not generic)
- ✅ Balanced depth (neither shallow nor excessive)
- ✅ Accurate to technical reality
- ✅ Defensible academic foundation
- ✅ Manageable scope

**Next Step:** Ready untuk transform BAB 2 structure ini menjadi detailed outline + Gemini prompts untuk generate setiap subsection.

---

**STATUS: BAB 2 STRUCTURE ANALYSIS COMPLETE ✅**

Structure ini READY untuk advisor discussion atau untuk mulai generate content per subsection.

