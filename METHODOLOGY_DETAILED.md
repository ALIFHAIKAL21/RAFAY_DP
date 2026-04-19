# DETAILED METHODOLOGY COMPARISON
## RESTI vs RAFAY IDP v2.0

---

## PART 1: RESTI METHODOLOGY (News Classification)

### 1.1 Problem Definition
```
Input:  Indonesian online news articles (text)
        Example: "Pasar modal Indonesia mencatat rekor tertinggi..."
        
Output: Category label (single classification)
        Example: {"category": "Finance", "confidence": 0.92}
        
Categories: Business, Finance, Technology, Sports, Entertainment, Politics, etc. (typically 5-15 categories)
```

### 1.2 Data Preprocessing Pipeline

```
Raw News Text
    ↓
[1] Tokenization
    - Split text into word tokens
    - Handle punctuation
    Example: "Harga emas naik 5%" → ["Harga", "emas", "naik", "5", "%"]
    
    ↓
[2] Case Normalization
    - Convert to lowercase
    Example: "JAKARTA" → "jakarta", "Bank" → "bank"
    
    ↓
[3] Stopword Removal
    - Remove common Indonesian words: "dan", "atau", "yang", "di", "ke"
    Example: "harga emas dan perak" → ["harga", "emas", "perak"]
    
    ↓
[4] Lemmatization
    - Reduce words to root form
    - Indonesian-specific stemming (e.g., affixes: me-, ber-, -kan)
    Example: "dinaikan" → "naik", "memberikan" → "beri"
    
    ↓
Preprocessed Tokens: ["harga", "emas", "naik"]
```

### 1.3 Feature Extraction: Word2Vec

```
CONCEPT: Word2Vec creates dense numerical vectors for words
         based on context in corpus

METHOD 1: Skip-gram Architecture
┌─────────────────────────────────────────┐
│ Training on corpus: "harga emas turun"  │
├─────────────────────────────────────────┤
│ For word "emas" with context window=2:  │
│ - Predict surrounding words: ["harga", "turun"]
│ - Adjust vector so similar words get similar vectors
│ - "emas" ≈ "perak" (both precious metals)
│ - "emas" ≠ "berita" (different concept)
└─────────────────────────────────────────┘

METHOD 2: CBOW (Continuous Bag of Words)
┌─────────────────────────────────────────┐
│ Given context: ["harga", "turun"]       │
│ Predict center word: "emas"             │
│ Builds similar relationships             │
└─────────────────────────────────────────┘

OUTPUT: Each word → 100-300 dimensional vector

Example Vectors (conceptual):
  "emas"    = [0.2, -0.5, 0.8, 0.1, ...]
  "perak"   = [0.2, -0.4, 0.9, 0.1, ...] ← Similar!
  "berita"  = [-0.3, 0.6, -0.2, 0.8, ...]  ← Different!

DOCUMENT REPRESENTATION:
  Doc = Average of all word vectors (or TF-IDF weighted)
  
  "harga emas naik" → 
    ([0.2, -0.5, 0.8...] + [0.5, 0.1, 0.3...] + [0.1, 0.2, 0.5...]) / 3
    = [0.27, -0.07, 0.53...]  ← 300D vector representing whole news article
```

### 1.4 Classification: SVM (Support Vector Machine)

```
SVM CONCEPT:
- Find optimal hyperplane separating different categories
- Maximize margin between categories in high-dimensional space

TRAINING:
1. Take preprocessed news articles (300D Word2Vec vectors)
2. Label each with category (Finance, Technology, Sports, etc.)
3. Learn decision boundaries

KERNELS USED:
- RBF (Radial Basis Function): For non-linear separation
- Handles complex decision boundaries

EXAMPLE:
  Training samples in 2D (reduced from 300D for visualization):
  
    Technology ●●    ← Articles about tech news
         ●●
    ─────────────────  ← Optimal hyperplane
         ●●
    Finance  ●●       ← Articles about finance
    
  New article: "Startup Indonesia dapat funding" 
  Maps to point near Technology cluster → Predicts "Technology"
```

### 1.5 Hyperparameters

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Embedding Dimension | 100-300 | Sweet spot: large enough to capture semantics, small enough to train |
| Context Window | 5-10 | Captures local semantic context |
| Min Word Frequency | 5-10 | Removes rare words (likely noise or typos) |
| SVM C parameter | 0.1-1.0 | Regularization: prevent overfitting |
| SVM Kernel | RBF | Non-linear classification for news categories |
| Train-Test Split | 80%-20% | Standard ML practice |
| Cross-Validation | 5-fold | Robust evaluation |

### 1.6 Training Process

```
[1] Build Word2Vec Model
    - Load all news corpus
    - Train on combined text
    - Save embedding matrix (Vocab_Size × 300)
    - Training time: Hours to days on large corpus
    
[2] Convert Documents to Vectors
    - For each training news article:
      - Get word embeddings
      - Average (or weighted average)
      - Result: 300D vector per document
    
[3] Train SVM Classifier
    - Input: (300D vectors, category labels)
    - Optimizer: SMO (Sequential Minimal Optimization)
    - Find hyperplane parameters
    - Training time: Minutes to hours on 10K+ docs
    
[4] Validation & Tuning
    - 5-fold cross-validation
    - Test different hyperparameters (C, kernel)
    - Select best model
    
[5] Final Evaluation
    - Test on held-out test set (20%)
    - Report Accuracy, Precision, Recall, F1
```

### 1.7 Inference (Prediction on New News)

```
New Article: "Bank Indonesia turunkan suku bunga"

[1] Preprocess
    - Tokenize: ["Bank", "Indonesia", "turunkan", "suku", "bunga"]
    - Lowercase + stemming: ["bank", "indonesia", "turun", "suku", "bunga"]
    - Remove stopwords: ["bank", "turun", "bunga"]

[2] Get Word2Vec Embeddings
    - bank   → [0.1, 0.2, -0.3, ...]  (300D)
    - turun  → [0.2, 0.1, -0.2, ...]
    - bunga  → [0.3, -0.1, 0.1, ...]
    
[3] Document Vector (Average)
    doc_vec = ([0.1, 0.2, -0.3...] + [0.2, 0.1, -0.2...] + [0.3, -0.1, 0.1...]) / 3
            = [0.2, 0.07, -0.13...]  (300D)

[4] SVM Prediction
    - Compute distance to hyperplane
    - Distance > 0 → Finance (confidence: 0.92)
    - Distance < 0 → Not Finance
    
[5] Output
    {"category": "Finance", "confidence": 0.92}
```

### 1.8 Strengths & Limitations

**Strengths:**
- ✓ Simple, interpretable approach
- ✓ Word2Vec captures semantic relationships
- ✓ SVM is robust classifier
- ✓ Low computational cost
- ✓ Works well on clean, formal text

**Limitations:**
- ✗ Word2Vec is static (context-independent)
- ✗ Cannot handle word sense disambiguation
- ✗ Doesn't capture long-range dependencies
- ✗ Struggles with typos/misspellings (OOV words)
- ✗ Document representation (averaging) loses word order
- ✗ No understanding of negation ("not good" ≈ "good")

---

## PART 2: RAFAY METHODOLOGY (Logistics Order Extraction)

### 2.1 Problem Definition

```
Input:  WhatsApp chat messages (informal, unstructured)
        Example: "[10.00, 17/2/26] Surabaya ke CGK 3x TWB
                  Driver: M Syaichoni (082191633212)
                  Nopol: N 8872 RK | SEGERA"
        
Output: Structured multi-field extraction
        {
          "UNIT_QTY": "3",
          "UNIT_TYPE": "TWB",
          "ORIGIN": "SURABAYA",
          "DESTINATION": "CGK",
          "DRIVER": "M Syaichoni",
          "PHONE": "082191633212",
          "PLATE": "N 8872 RK",
          "TIME": "SEGERA",
          "DATE": "17/02/2026",
          "confidence": {...per field...}
        }
```

### 2.2 Data Preprocessing Pipeline

```
Raw WhatsApp Message
    ↓
[1] Timestamp Extraction & Removal
    - Pattern: [HH.MM, DD/MM/YYYY]
    - Extract date/time
    - Remove from main text
    Example: "[10.00, 17/2/26] text" → date="17/02/2026", time="10:00", text="text"
    
    ↓
[2] Emoji & Special Character Handling
    - Remove emoji, emoticons, multiple spaces
    Example: "SURABAYA 😊  →  CGK" → "SURABAYA CGK"
    
    ↓
[3] Case Normalization
    - Lowercase location names (will uppercase later for consistency)
    Example: "JAKARTA" → "jakarta"
    
    ↓
[4] Abbreviation Mapping
    - Recognize: CBM (cubic meter), TWB (truck), WB (car)
    - Recognize: CGK (Jakarta), SUB (Surabaya), JKT (Jakarta)
    - Recognize: SEGERA (urgent/immediate)
    Example: "2 CBM" kept as is (domain-specific)
    
    ↓
[5] Fuzzy Label Normalization
    - Fix typos in field labels
    - Levenshtein distance ≤ 2
    Example: "Loksai" → "Lokasi" (Levenshtein: 2 edits: s→k, i→a)
             "drver" → "driver" (Levenshtein: 1 edit: delete r)
             "Wktu lodaing" → "Waktu loading"

    ↓
Normalized Message (but still unstructured):
"surabaya ke cgk 3 twb
 driver: m syaichoni (082191633212)
 plate: n 8872 rk
 time: segera"
```

### 2.3 Feature Extraction: IndoBERT (BERT for Indonesian)

```
TRANSFORMER ARCHITECTURE:
- 12 stacked layers of self-attention transformers
- 768 hidden units per token
- 12 attention heads
- 110M+ parameters

TOKENIZATION (Subword):
  Input: "SURABAYA"
  
  Step 1: Tokenize to subwords
    "SURABAYA" → ["SUR", "##ABA", "##YA"]
    (## indicates continuation of previous word)
  
  Step 2: Add special tokens
    [CLS] SUR ##ABA ##YA [SEP]
    (CLS = classification token, SEP = separator)
  
  Step 3: Convert to token IDs
    [CLS]=101, SUR=2456, ##ABA=3891, ##YA=5023, [SEP]=102

EMBEDDING LAYER:
  Each token ID → 768D embedding vector
  [CLS] → [0.1, -0.3, 0.5, ..., 0.2]  (768 values)
  SUR   → [0.2, 0.1, -0.2, ..., -0.1]
  ##ABA → [0.3, -0.1, 0.4, ..., 0.0]
  ##YA  → [-0.1, 0.2, 0.1, ..., 0.3]
  [SEP] → [0.4, 0.0, -0.3, ..., 0.1]

POSITIONAL ENCODING:
  Encodes position: token_1, token_2, token_3, ...
  Position 1: [0.0, 1.0, 0.0, ...]
  Position 2: [0.1, 0.9, 0.0, ...]
  Position 3: [0.2, 0.8, 0.0, ...]

STACKED SELF-ATTENTION (12 layers):
  Layer 1:
    Input: [CLS_embed, SUR_embed, ##ABA_embed, ##YA_embed, [SEP]_embed]
    ↓ Self-Attention
    [CLS] attends to: SUR (50%), ##ABA (20%), ##YA (20%), [SEP] (10%)
    SUR attends to: ##ABA (40%), ##YA (35%), [CLS] (15%), [SEP] (10%)
    (Learns which tokens are semantically related)
    ↓ Feed-Forward
    Output: Updated embeddings (still 768D each)
  
  Layer 2-12: Repeat, building deeper semantic understanding

OUTPUT of BERT:
  Each token has contextual embedding (768D)
  [CLS] → [0.05, -0.28, 0.51, ..., 0.18]  ← Contextually aware!
  SUR → [0.19, 0.12, -0.18, ..., -0.08]
  etc.

KEY DIFFERENCE from Word2Vec:
  - Word2Vec: "SURABAYA" always = same vector (static)
  - BERT: "SURABAYA" embedding varies by context:
    * In "ORIGIN: SURABAYA" context → high value for location features
    * In "DRIVER from SURABAYA" context → different representation

CONTEXTUAL UNDERSTANDING:
  BERT learns that in logistics domain:
  - "CBM", "TWB", "WB" are unit types
  - "SEGERA", "PAGI", "SORE" are time expressions
  - "CGK", "SUB", "JKT" are locations
  - Through 12 layers of attention over training data
```

### 2.4 Task 1: Named Entity Recognition (NER) - Token Classification

```
OBJECTIVE: For each token, predict its entity type

ARCHITECTURE:
  BERT Encoder (12 layers, 768D)
    ↓
  Linear Classification Head
    ↓
  Softmax over 21 entity labels

BIO TAGGING SCHEME:
  B-ORIGIN    (Beginning of origin location)
  I-ORIGIN    (Inside/continuation of origin)
  B-DESTINATION (Beginning of destination)
  I-DESTINATION
  B-DRIVER    (Beginning of driver name)
  I-DRIVER
  ... (21 total labels)
  O           (Outside any entity)

TRAINING EXAMPLE:
  Input: "Surabaya ke CGK 3 TWB driver M Syaichoni"
  
  Token:    ["Surabaya", "ke", "CGK", "3", "TWB", "driver", "M", "Syaichoni"]
  True Tag: [B-ORIGIN,  O,   B-DEST, O,  B-UNIT_TYPE, O,   B-DRIVER, I-DRIVER]
  
  BERT processes all 8 tokens in parallel with 12-layer attention
  
  Output: Predicted tags for each token
  Predicted: [B-ORIGIN, O, B-DEST, O, B-UNIT_TYPE, O, B-DRIVER, I-DRIVER]
  
  Loss computed: Cross-entropy between true and predicted
  Backprop through 12 layers to update weights

POST-PROCESSING (Subword Reconstruction):
  Model output at subword level:
    SUR (B-ORIGIN), ##ABA (I-ORIGIN), ##YA (I-ORIGIN)
  
  Reconstruct to word level:
    "SURABAYA" → B-ORIGIN (merge subword tags)

CONFIDENCE:
  Softmax outputs probabilities for each label
  ORIGIN confidence = 0.95 (95% confident)
  DRIVER confidence = 0.87 (87% confident)
```

### 2.5 Task 2: Event Classifier (Intent Detection) - Sequence Classification

```
OBJECTIVE: Classify intent of entire message

ARCHITECTURE:
  Input: Full message
  BERT Encoder (12 layers)
    ↓
  [CLS] token output (represents whole message)
    ↓
  Linear Classification Head (3 classes)
    ↓
  Softmax over 3 labels

3-WAY CLASSIFICATION:
  1. NEW_ORDER  (User submitting new order)
  2. UPDATE     (User revising/updating existing order)
  3. NON_ORDER  (Other messages: cancel, info request, etc.)

TRAINING EXAMPLE:
  Message: "[10.00, 17/2/26] Surabaya ke CGK 3 TWB..."
  True Label: NEW_ORDER (label_id = 0)
  
  BERT [CLS] representation: [0.1, -0.2, 0.3, ..., 0.05]  (768D)
  
  Linear head:
    logit_NEW_ORDER = W_new @ [CLS] + b_new = 2.5
    logit_UPDATE = W_upd @ [CLS] + b_upd = 1.2
    logit_NON_ORDER = W_non @ [CLS] + b_non = -1.8
  
  Softmax:
    P(NEW_ORDER) = exp(2.5) / (exp(2.5) + exp(1.2) + exp(-1.8)) = 0.92
    P(UPDATE) = 0.06
    P(NON_ORDER) = 0.02
  
  Prediction: NEW_ORDER (confidence: 0.92)
  
  Loss: Cross-entropy between [1,0,0] (true) and [0.92, 0.06, 0.02] (pred)
```

### 2.6 Task 3: Revision Matcher (Semantic Matching) - Sequence-Pair Classification

```
OBJECTIVE: Determine if revision matches existing order

ARCHITECTURE:
  Input: (text_a, text_b) pair
    text_a = new message: "Surabaya ke CGK ubah driver jadi Budi"
    text_b = existing order from DB: "RO_DATE: 17/02/2026, ORIGIN: Surabaya, ..."
  
  Concatenate: text_a [SEP] text_b
  
  BERT Encoder (12 layers)
    ↓
  [CLS] token output
    ↓
  Linear Classification Head (binary)
    ↓
  Softmax over 2 labels

BINARY CLASSIFICATION:
  0. NO_MATCH (revision doesn't match this order)
  1. MATCH    (revision matches this order)

TRAINING EXAMPLE:
  text_a: "Perubahan driver, jadi Budi"
  text_b: "ORDER#5 RO_DATE: 17/02/2026 DRIVER: M Syaichoni ORIGIN: Surabaya"
  True Label: MATCH (label = 1)
  
  Concatenated input:
    [CLS] Perubahan driver jadi Budi [SEP] ORDER#5 RO_DATE: 17/02/2026 ... [SEP]
  
  BERT processes with attention across [SEP]:
    - "Budi" (new driver) attends to "M Syaichoni" (old driver)
    - "Perubahan" (change) attends to "ORDER#5"
    - Builds semantic matching features
  
  [CLS] representation captures: "This revision is about changing driver for ORDER#5"
  
  Linear head:
    logit_NO_MATCH = 0.8
    logit_MATCH = 2.1
  
  Softmax:
    P(MATCH) = exp(2.1) / (exp(0.8) + exp(2.1)) = 0.78
    P(NO_MATCH) = 0.22
  
  Prediction: MATCH (confidence: 0.78)
```

### 2.7 Training Pipeline

```
[1] DATA PREPARATION
    - Collect WhatsApp messages with manual annotations
    - Task 1 (NER): Annotate entities (ORIGIN, DESTINATION, DRIVER, etc.)
    - Task 2 (Event): Label as NEW/UPDATE/NON_ORDER
    - Task 3 (Revision): Create pairs (revision_msg, existing_order) + label
    
[2] TRAIN NER MODEL
    - Load IndoBERT checkpoint (pre-trained on Indonesian)
    - Add token classification head
    - Loss: Cross-entropy per token
    - Optimize: AdamW (learning rate 2e-5, batch size 8, epochs 5)
    - Metrics tracked: Per-entity F1, boundary F1 (seqeval)
    - Save best model (highest F1 on validation)
    
[3] TRAIN EVENT CLASSIFIER
    - Load IndoBERT checkpoint
    - Add sequence classification head (3 classes)
    - Loss: Cross-entropy for sequence
    - Optimize: AdamW (learning rate 2e-5, batch size 8, epochs 4)
    - Metrics tracked: Macro F1, per-class precision/recall
    - Save best model
    
[4] TRAIN REVISION MATCHER
    - Load IndoBERT checkpoint
    - Add sequence-pair classification head (binary)
    - Loss: Cross-entropy for pair
    - Optimize: AdamW (learning rate 2e-5, batch size 8, epochs 4)
    - Metrics tracked: F1 for MATCH class
    - Save best model
    
[5] INTEGRATION & TESTING
    - Load all 3 models
    - Test on held-out test set
    - Evaluate pipeline: Message → Classification → NER → Matching
    - Report end-to-end accuracy
```

### 2.8 Inference Pipeline (Production)

```
NEW MESSAGE: "[10.00, 17/2/26] Surabaya ke CGK 3 TWB. Driver M Syaichoni..."

STEP 1: EVENT CLASSIFICATION
  │
  ├─ Model: Event Classifier
  ├─ Input: Full message
  ├─ Output: P(NEW_ORDER)=0.92, P(UPDATE)=0.06, P(NON_ORDER)=0.02
  │
  └─ Decision: 
      IF P(NEW_ORDER) > 0.75 → Continue to extraction
      ELSE IF P(NON_ORDER) > threshold → Discard message
      ELSE IF P(UPDATE) > threshold → Go to revision matching
      
STEP 2: ENTITY EXTRACTION
  │
  ├─ Model: NER Model (Token Classification)
  ├─ Input: Message (tokenized → subword tokens)
  │         [CLS] Surabaya ke CGK 3 TWB driver M Syaichoni [SEP]
  │
  ├─ Process: 12-layer BERT + token classification head
  │         Each token → probability over 21 labels
  │
  ├─ Output:
  │   Token    | Predicted Label | Confidence
  │   ---------|-----------------|----------
  │   Surabaya | B-ORIGIN        | 0.98
  │   ke       | O               | 0.99
  │   CGK      | B-DESTINATION   | 0.96
  │   3        | B-UNIT_QTY      | 0.94
  │   TWB      | B-UNIT_TYPE     | 0.92
  │   driver   | O               | 0.97
  │   M        | B-DRIVER        | 0.89
  │   Syaichoni| I-DRIVER        | 0.91
  │
  └─ Postprocess: Reconstruct entities + merge subwords
      ORIGIN = "SURABAYA" (conf: 0.98)
      DESTINATION = "CGK" (conf: 0.96)
      UNIT_QTY = "3" (conf: 0.94)
      UNIT_TYPE = "TWB" (conf: 0.92)
      DRIVER = "M Syaichoni" (conf: 0.90)
      ...
      
STEP 3: BUSINESS LOGIC ENFORCEMENT
  │
  ├─ Check quotas:
  │   Declared: 3 units → Must generate 3 rows
  │   Generated: 1 (M Syaichoni) → 2 PARTIAL rows
  │
  ├─ Fill order status:
  │   Row 1: M Syaichoni + Plate → ASSIGNED
  │   Row 2, 3: No driver/plate → PARTIAL
  │
  └─ Determine match type: NEW_ORDER (create new)
  
STEP 4 (If UPDATE): REVISION MATCHING
  │
  ├─ Query existing orders from DB:
  │   ORDER#5 (17/02/2026, Surabaya→CGK, existing driver)
  │   ORDER#8 (18/02/2026, Surabaya→SUB, different route)
  │   ...
  │
  ├─ For each candidate:
  │   Model: Revision Matcher
  │   Input: (new_msg, candidate_order)
  │   Output: P(MATCH), P(NO_MATCH)
  │
  ├─ Scoring:
  │   ORDER#5: P(MATCH)=0.88 > THRESHOLD(0.58) → CANDIDATE
  │   ORDER#8: P(MATCH)=0.32 < THRESHOLD → REJECT
  │
  └─ Update: Apply revision to ORDER#5
  
STEP 5: DATABASE PERSISTENCE
  │
  ├─ Save to PostgreSQL:
  │   raw_chat table: Store original message
  │   order_dataset table: Store extracted structured data
  │   Relationships: Link to ORDER#5 if revision
  │
  └─ Return response:
      {
        "order_id": 5,
        "type": "UPDATE",
        "extracted": {
          "DRIVER": "M Syaichoni",
          ...
        },
        "confidence": 0.90,
        "status": "ASSIGNED"
      }
```

### 2.9 Comparison: Static vs Contextual

```
WORD2VEC (RESTI):
  "CGK" word vector = [0.2, -0.3, 0.4, 0.1, ...]  ← ALWAYS same

  Context 1: "Keberangkatan dari CGK"
             Vector: [0.2, -0.3, 0.4, 0.1, ...]

  Context 2: "Tujuan: CGK"
             Vector: [0.2, -0.3, 0.4, 0.1, ...]  ← SAME vector!

  Problem: Model cannot distinguish usage context

BERT (RAFAY):
  Layer 1 attention:
    Context 1 "Keberangkatan dari CGK"
    CGK attends to: "Keberangkatan" (origin context)
    CGK hidden state: [0.19, -0.32, 0.38, 0.12, ...]

  Layer 12 output:
    Context 1: [0.25, -0.28, 0.42, 0.05, ...]

  ──────────────────────────────────────────

  Layer 1 attention:
    Context 2 "Tujuan: CGK"
    CGK attends to: "Tujuan" (destination context)
    CGK hidden state: [0.21, -0.29, 0.36, 0.15, ...]

  Layer 12 output:
    Context 2: [0.28, -0.26, 0.39, 0.08, ...]  ← DIFFERENT!

  Benefit: Model learns context-dependent representations
           "origin CGK" vs "destination CGK" have different meanings
```

---

## PART 3: KEY DIFFERENCES SUMMARY

| Aspect | RESTI | RAFAY |
|--------|-------|-------|
| **Problem** | Document classification | Information extraction pipeline |
| **Input Characteristics** | Formal, clean | Informal, noisy |
| **Embedding** | Word2Vec (static, 300D) | BERT (contextual, 768D per token) |
| **Classification Task** | Single (1 model) | 3 models (NER + Event + Matcher) |
| **Output** | 1 label | 10+ structured fields |
| **Constraints** | None | Multiple business rules |
| **State Management** | Stateless | Stateful (DB tracking) |
| **Handling Typos** | Preprocessing only | Fuzzy matching + BERT robustness |
| **Evaluation Metrics** | Global F1 | Per-entity F1 + constraint satisfaction |
| **Deployment** | Batch processing | Real-time streaming + UI + Database |
| **Model Parameters** | ~1M (SVM) | ~400M (3 × BERT models) |
| **Training Time** | Hours | Days (on GPU) |
| **Inference Time** | ms | 100-200ms per message |

---

**Version:** 1.0  
**Created:** April 2026
