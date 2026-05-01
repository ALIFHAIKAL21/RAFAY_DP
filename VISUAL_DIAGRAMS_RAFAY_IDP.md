# VISUAL DIAGRAMS & FLOWCHARTS
## Sistem Ekstraksi Data Logistik PT. Rafay

---

## 1. SISTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│            PT. RAFAY LOGISTIK - DATA EXTRACTION SYSTEM              │
│                   (Dual-Model Hybrid Approach)                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────┐
│   EXTERNAL INPUT SOURCES      │
├──────────────────────────────┤
│ • WhatsApp API               │ ── Raw message JSON
│ • Manual CSV upload          │ ── Structured chat export
│ • Direct text input (Streamlit) ── Ad-hoc testing
└──────┬───────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────┐
│                  STREAMLIT WEB APPLICATION                        │
│  (User Interface for Admin, Batch Processing Control)             │
├──────────────────────────────────────────────────────────────────┤
│ • File upload → CSV parsing                                      │
│ • Real-time preview of extracted data                            │
│ • Database query interface                                       │
│ • Model management (version selection, threshold tuning)         │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌────────────────────────────────────────────────────────────────────┐
│                 BATCH PROCESSOR LAYER                               │
│          (Smart Text Splitting + Junk Filtering)                   │
├────────────────────────────────────────────────────────────────────┤
│ Input:  Large unstructured text (possibly multiple orders)         │
│ Logic:  - Header-based split ("Request...", "On Call...")         │
│         - Multi-unit detection (multiple "X UNIT" per message)    │
│         - Junk filtering (non-order messages)                     │
│ Output: List of isolated order chunks (strings)                   │
│ File:   src/inference/batch_processor.py                          │
└──────┬───────────────────────────────────────────────────────────┘
       │
       ↓
┌────────────────────────────────────────────────────────────────────┐
│            EVENT CLASSIFICATION LAYER                               │
│       (Routing Decision: NEW_ORDER vs REPAIR/REFILL)               │
├────────────────────────────────────────────────────────────────────┤
│ Model:    IndoBERT + SequenceClassification head                   │
│ Input:    Single order chunk (string)                              │
│ Classes:  [NEW_ORDER, REPAIR, REFILL, NON_ORDER]                  │
│ Threshold: 0.75 confidence                                        │
│ Output:   {label: str, confidence: float}                         │
│ File:     src/inference/event_classifier.py                       │
│ Config:   RAFAY_EVENT_THRESHOLD (env var)                         │
└──────┬────────────────────────────────┬──────────────────────────┘
       │                                │
   NEW_ORDER                       REPAIR/REFILL
       │                                │
       ↓                                ↓
┌─────────────────────────┐   ┌──────────────────────────────┐
│  PATH A: NER PIPELINE   │   │ PATH B: REVISION MATCHING    │
├─────────────────────────┤   ├──────────────────────────────┤
│ Task: Token-level       │   │ Task: Sentence-level         │
│       classification    │   │       pair classification    │
│                         │   │                              │
│ Input: Order text       │   │ Input: (revision_msg,        │
│                         │   │         candidate_order)     │
│ Output: Entities dict   │   │                              │
│ {ORDER_DATE: ...,       │   │ Output: Match score          │
│  UNIT_SPEC: ...,        │   │ {match_prob, rank}          │
│  LOCATION: ...,         │   │                              │
│  LOAD_TIME: ...,        │   │ Model: IndoBERT +            │
│  ROUTE: ...,            │   │        Pair Classification   │
│  DRIVER: ...,           │   │                              │
│  PHONE: ...}            │   │ Threshold: 0.58 confidence  │
│                         │   │ Min Gap: 0.05               │
│ File: pipeline.py       │   │ File: revision_matcher.py   │
│ Model: indobert_NER     │   │ Model: indobert_revision_   │
│        /final_model     │   │        matcher              │
└────────┬────────────────┘   └────────────┬────────────────┘
         │                                 │
         │                                 ↓
         │                     ┌──────────────────────────────┐
         │                     │ CANDIDATE RANKING            │
         │                     ├──────────────────────────────┤
         │                     │ Step 1: Query previous       │
         │                     │         3 days of orders    │
         │                     │                              │
         │                     │ Step 2: For each candidate:  │
         │                     │ score(revision, candidate)   │
         │                     │                              │
         │                     │ Step 3: Sort by score DESC   │
         │                     │                              │
         │                     │ Step 4: Filter by threshold  │
         │                     │         & min_gap            │
         │                     │                              │
         │                     │ Output: Ranked candidates    │
         │                     │ [{order_id, score, rank}]    │
         │                     └────────────┬─────────────────┘
         │                                  │
         │                                  ↓
         │                     ┌──────────────────────────────┐
         │                     │ CONDITIONAL MERGE LOGIC      │
         │                     ├──────────────────────────────┤
         │                     │ IF top_candidate exists:     │
         │                     │   - Extract fields from      │
         │                     │     incoming revision        │
         │                     │   - Update matching order    │
         │                     │   - Mark as revised          │
         │                     │ ELSE:                        │
         │                     │   - Manual review required   │
         │                     │   - Flag as ambiguous        │
         │                     └────────────┬─────────────────┘
         │                                  │
         └──────────────────┬───────────────┘
                            ↓
              ┌─────────────────────────────────────┐
              │  UNIFIED OUTPUT: Merged Data Dict   │
              │  {order_id, date, unit, location,   │
              │   time, route, driver, phone, ...}  │
              └────────────┬────────────────────────┘
                           ↓
         ╔══════════════════════════════════════════╗
         ║  POST-PROCESSING LAYER                   ║
         ║  (Rule-Based Standardization)            ║
         ║  - Format validation (dates, phones)     ║
         ║  - Timestamp normalization               ║
         ║  - Location code mapping                 ║
         ║  - Driver blacklist check                ║
         ║  - Missing field detection               ║
         ║  Output: Clean, validated record         ║
         ╚═════════════════╤════════════════════════╝
                           ↓
         ┌─────────────────────────────────────────┐
         │  DATABASE PERSISTENCE LAYER             │
         │  (SQLite via db/persistence.py)         │
         ├─────────────────────────────────────────┤
         │ Tables:                                 │
         │ • order_rows: Main order records        │
         │ • chat_history: Raw message logs        │
         │ • revision_log: Tracking updates        │
         │ • model_metadata: Version info          │
         └────────────┬────────────────────────────┘
                      ↓
         ┌─────────────────────────────────────────┐
         │  EXPORT & REPORTING LAYER               │
         ├─────────────────────────────────────────┤
         │ • accumulated_output.csv (admin view)   │
         │ • Daily report generation               │
         │ • Quality metrics dashboard             │
         │ • Model performance tracking            │
         └─────────────────────────────────────────┘
```

---

## 2. DATA FLOW: NEW ORDER vs REVISION

```
┌────────────────────────────────────────────────────────────────┐
│  DAY 1: NEW ORDER PROCESSING                                   │
├────────────────────────────────────────────────────────────────┤

Input Message:
┌────────────────────────────────────────────┐
│ [08.01, 10/3/2026] Akbar Rafay:            │
│ Request Unit On Call Tgl 12 MARET 2026    │
│                                            │
│ RAFAY                                      │
│ 3 UNIT TWB 50 CBM                          │
│ Lokasi : ARGOPANTES                        │
│ Waktu loading : SEGERA                     │
│ Rute/tujuan : CGK - SUB                    │
│ driver  : SUTRISNO                         │
│ Nopol  : BM 8364 AU                        │
│ No hp  : 085353886066                      │
└────────────────────────────────────────────┘
                ↓
        Event Classification
        (indolem/indobert)
                ↓
        ✓ NEW_ORDER (confidence: 0.92)
                ↓
        NER Pipeline (Token Classification)
                ↓
        Extracted Entities:
        ┌────────────────────────────────────────┐
        │ ORDER_DATE: "12 MARET 2026"            │
        │ UNIT_SPEC: "3 UNIT TWB 50 CBM"         │
        │ LOCATION: "ARGOPANTES"                 │
        │ LOAD_TIME: "SEGERA"                    │
        │ ROUTE: "CGK - SUB"                     │
        │ DRIVER: "SUTRISNO"                     │
        │ PHONE: "085353886066"                  │
        └────────────────────────────────────────┘
                ↓
        Post-Processing
        (Standardization Rules)
                ↓
        Database Insert:
        ┌────────────────────────────────────────┐
        │ Order ID: <auto-generated>             │
        │ Date: 2026-03-12                       │
        │ Unit: TWB 50 CBM (qty: 3)              │
        │ Location: ARGOPANTES                   │
        │ Time: SEGERA (priority)                │
        │ Route: CGK→SUB                         │
        │ Driver: SUTRISNO                       │
        │ Phone: 085353886066                    │
        │ Status: COMPLETE ✓                     │
        │ Created: 2026-03-10 08:01              │
        └────────────────────────────────────────┘
                ↓
        ✓ ORDER SAVED TO DATABASE (1 record)


┌────────────────────────────────────────────────────────────────┐
│  DAY 2: REFILL/REPAIR PROCESSING                               │
├────────────────────────────────────────────────────────────────┤

Input Message:
┌────────────────────────────────────────────┐
│ [10.30, 11/3/2026] Akbar Rafay:            │
│                                            │
│ Nomor kontak SUTRISNO 085353886066         │
│ (untuk order tgl 12 maret)                 │
└────────────────────────────────────────────┘
                ↓
        Event Classification
        (indolem/indobert)
                ↓
        ✓ REFILL (confidence: 0.81)
                ↓
        Revision Matcher
        (Sequence-Pair Classification)
                ↓
        Query Database:
        Find orders from last 3 days
        with PHONE field incomplete
        → Candidate Pool: [Order#123, Order#456, ...]
                ↓
        Score each candidate:
        score(refill_msg, candidate_order)
                ↓
        Ranking Results:
        ┌────────────────────────────────────────┐
        │ Rank 1: Order#123  (match_score: 0.79) │
        │         "3 UNIT TWB...SUTRISNO..."      │
        │         ✓ PASS (score > 0.58)          │
        │                                        │
        │ Rank 2: Order#456  (match_score: 0.62) │
        │         "2 UNIT CDDL...KARYADI..."      │
        │         ✓ PASS (score > 0.58)          │
        │                                        │
        │ Rank 3: Order#789  (match_score: 0.41) │
        │         "3 UNIT CDDL...JATMIYANTA..."   │
        │         ✗ FAIL (score < 0.58)          │
        │                                        │
        │ GAP between Rank 1 & 2: 0.17 > 0.05 ✓  │
        └────────────────────────────────────────┘
                ↓
        CONFIDENCE: Rank 1 is confident match
                ↓
        Merge Logic:
        IF (top_score > 0.58 AND gap > 0.05):
          Extract PHONE from refill_msg
          Update Order#123:
            - PHONE: 085353886066
            - Updated: 2026-03-11 10:30
            - Status: COMPLETE ✓
        ELSE:
          Flag for manual review
                ↓
        Database Update:
        ┌────────────────────────────────────────┐
        │ Order ID: 123                          │
        │ Date: 2026-03-12                       │
        │ Unit: TWB 50 CBM (qty: 3)              │
        │ Location: ARGOPANTES                   │
        │ Time: SEGERA                           │
        │ Route: CGK→SUB                         │
        │ Driver: SUTRISNO                       │
        │ Phone: 085353886066  ← UPDATED         │
        │ Status: COMPLETE ✓                     │
        │ Last Update: 2026-03-11 10:30          │
        └────────────────────────────────────────┘
                ↓
        ✓ ORDER UPDATED (1 record modified)
```

---

## 3. NER MODEL: Token-Level Classification

```
┌──────────────────────────────────────────────────────────────┐
│                    TEXT TOKENIZATION                          │
│  "3 UNIT TWB 50 CBM Lokasi ARGOPANTES Waktu loading SEGERA" │
└──────────────────────────────────────────────────────────────┘
                          ↓
            (WordPiece Subword Tokenization)
                          ↓
┌──────────────────────────────────────────────────────────────┐
│ Tokens:  [CLS]  3    UNIT  TWB  50  CBM  Lo  ##kasi  ...    │
│ Token#:   0     1    2     3    4   5    6    7     ...     │
│ (Embedding space: 768 dimensional vectors per token)        │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│              INDOBERT ENCODER (12 layers)                     │
│  Layer 1: Self-Attention (context awareness)                 │
│           Multi-Head Attention (8 heads, each 96D)           │
│                                                              │
│  Layer 2-12: Transformer blocks (feed-forward networks)      │
│                                                              │
│  Output: Contextual embeddings                              │
│  (each token representation incorporates surrounding tokens) │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│     TOKEN CLASSIFICATION HEAD + CRF LAYER                     │
│                                                              │
│  Dense(768 → 27)  [27 possible classes: B/I 13 entities + O] │
│         ↓                                                    │
│  Logits: (seq_len, 27)                                       │
│         ↓                                                    │
│  CRF Decoding:                                               │
│  (Constrain: valid BIO sequences only)                       │
│         ↓                                                    │
│  Token#1: B-UNIT_SPEC (score: 0.92)                          │
│  Token#2: I-UNIT_SPEC (score: 0.88)                          │
│  Token#3: I-UNIT_SPEC (score: 0.85)                          │
│  Token#4: O             (score: 0.91)                        │
│  ...                                                         │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│              ENTITY RECONSTRUCTION                            │
│                                                              │
│  Merge subword tokens back to words:                         │
│  Token: [CLS]  3    UNIT  TWB  50  CBM  Lo  ##kasi           │
│  Label:  -     B-U  I-U   I-U  O   O    B-L I-L             │
│  Word:    -     3    UNIT  TWB  50  CBM  Lokasi             │
│  Label:   -     B-UNIT_SPEC    O   O    B-LOCATION         │
│                                                              │
│  Extracted Entities:                                        │
│  • UNIT_SPEC: "3 UNIT TWB" [score: 0.88]                    │
│  • LOCATION: "Lokasi" [score: 0.90]                         │
│                                                              │
│  (Confidence = average of constituent token scores)         │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│                 OUTPUT DICTIONARY                             │
│                                                              │
│  {                                                           │
│    "ORDER_DATE": {                                           │
│      "value": "12 MARET 2026",                              │
│      "confidence": 0.91,                                     │
│      "start_pos": 0,                                         │
│      "end_pos": 15                                           │
│    },                                                        │
│    "UNIT_SPEC": {                                            │
│      "value": "3 UNIT TWB 50 CBM",                           │
│      "confidence": 0.88                                      │
│    },                                                        │
│    "LOCATION": {                                             │
│      "value": "ARGOPANTES",                                  │
│      "confidence": 0.92                                      │
│    },                                                        │
│    ...                                                       │
│  }                                                           │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. SEMANTIC SIMILARITY: Sequence-Pair Classification

```
INCOMING REVISION MESSAGE:
┌────────────────────────────────────────────┐
│ "Driver SUTRISNO ganti jadi WAHYUDI"       │
│ (untuk order tgl 12 maret ke CGK-SUB)"     │
└────────────────────────────────────────────┘

CANDIDATE ORDERS (from last 3 days):
┌────────────────────────────────────────────┐
│ Order #123:                                │
│ "3 UNIT TWB ke CGK-SUB, Driver SUTRISNO,   │
│  tgl 12 maret"                             │
│                                            │
│ Order #456:                                │
│ "2 UNIT CDDL ke CGK-PKU, Driver SISWANTO,  │
│  tgl 13 maret"                             │
│                                            │
│ Order #789:                                │
│ "3 UNIT CDDL ke JATENG, Driver KARYADI,    │
│  tgl 13 maret"                             │
└────────────────────────────────────────────┘

                    ↓

PAIR ENCODING (for each candidate):

Pair 1: (revision, Order#123)
┌────────────────────────────────────────────────────────────┐
│ Text 1: "Driver SUTRISNO ganti jadi WAHYUDI"              │
│ Text 2: "3 UNIT TWB ke CGK-SUB, Driver SUTRISNO, tgl 12"  │
│         ↓                                                  │
│ [CLS] Driver SUTRISNO ganti ... [SEP] 3 UNIT TWB ... [SEP]│
│  └─ type_id=0 ─┘                   └─ type_id=1 ──────────┘ │
│  (Token type IDs distinguish text1 from text2)            │
└────────────────────────────────────────────────────────────┘
                    ↓
        Contextual Embedding (768D vector)
                    ↓
        Classification Head (768 → 2)
                    ↓
        Softmax Output:
        • MATCH: 0.78
        • NO_MATCH: 0.22
        ✓ PASS (score > 0.58)

Pair 2: (revision, Order#456)
        ... [similar process] ...
        Output:
        • MATCH: 0.62
        • NO_MATCH: 0.38
        ✓ PASS (score > 0.58)

Pair 3: (revision, Order#789)
        ... [similar process] ...
        Output:
        • MATCH: 0.41
        • NO_MATCH: 0.59
        ✗ FAIL (score < 0.58)

                    ↓

RANKING RESULTS:
┌────────────────────────────────────────────────┐
│ Rank 1: Order#123 (match_prob: 0.78) ← BEST   │
│         Gap to Rank 2: 0.78 - 0.62 = 0.16    │
│         Status: ✓ Confident (gap > 0.05)     │
│                                                │
│ Rank 2: Order#456 (match_prob: 0.62)          │
│         Still > threshold, alternative option │
│                                                │
│ Rank 3: Order#789 (match_prob: 0.41)          │
│         Filtered out (< threshold)             │
└────────────────────────────────────────────────┘
                    ↓
          DECISION: Merge into Order#123
```

---

## 5. POST-PROCESSING RULES

```
┌────────────────────────────────────────────────────────────────┐
│              EXTRACTED DATA FROM NER/MATCHING                   │
├────────────────────────────────────────────────────────────────┤
│ ORDER_DATE: "12 MARET 2026" / "13/03/2026" / "13-03-26"       │
│ UNIT_SPEC: "3 UNIT TWB 50 CBM"                               │
│ LOCATION: "ARGOPANTES"                                        │
│ LOAD_TIME: "SEGERA" / "07:00" / "18:00" / "06:00/13-03-26"   │
│ ROUTE: "CGK - SUB" / "CGK - JATENG TENTATIVE"                │
│ DRIVER: "SUTRISNO" / "M SYAICHONI" / "FERI IRAWAN"           │
│ PHONE: "085353886066" / "+6285353886066" / "0853538860660"  │
└────────────────────────────────────────────────────────────────┘
                             ↓
    ╔════════════════════════════════════════╗
    ║  STANDARDIZATION RULES                 ║
    ╚════════════════════════════════════════╝
                             ↓
    ┌─────────────────────────────────────────────┐
    │ 1. DATE NORMALIZATION                       │
    │                                             │
    │ Rule: Parse date → ISO 8601 format         │
    │                                             │
    │ "12 MARET 2026" → "2026-03-12"             │
    │ "13/03/2026"    → "2026-03-13"             │
    │ "13-03-26"      → "2026-03-13"             │
    │                                             │
    │ Validation:                                 │
    │ • Check month range [1-12] ✓              │
    │ • Check day range [1-31] ✓                │
    │ • Flag if future date > today + 30 days   │
    └─────────────────────────────────────────────┘
                             ↓
    ┌─────────────────────────────────────────────┐
    │ 2. PHONE NUMBER CLEANUP                     │
    │                                             │
    │ Rule: Extract digits → validate length     │
    │                                             │
    │ "085353886066"        → "085353886066" ✓   │
    │ "+6285353886066"      → "085353886066" ✓   │
    │ "0853538860660"       → "085353886066" ✓   │
    │   (truncate to 12 digits)                  │
    │ "08535388"            → INCOMPLETE ⚠       │
    │                                             │
    │ Blacklist Check:                            │
    │ • Don't allow admin phone numbers          │
    │ • Don't allow empty/zero phones            │
    └─────────────────────────────────────────────┘
                             ↓
    ┌─────────────────────────────────────────────┐
    │ 3. LOCATION CODE MAPPING                    │
    │                                             │
    │ Rule: Standardize location abbreviations    │
    │                                             │
    │ Input: "ARGOPANTES"                        │
    │ Mapping DB: ARGOPANTES → ARGOPANTES        │
    │ Output: "ARGOPANTES" ✓                     │
    │                                             │
    │ Input: "CGK"                               │
    │ Mapping: CGK → Jakarta (Soekarno-Hatta)    │
    │ Output: "CGK_JAKARTA" ✓                    │
    │                                             │
    │ Input: "SUB"                               │
    │ Mapping: SUB → Surabaya (Juanda)           │
    │ Output: "SUB_SURABAYA" ✓                   │
    └─────────────────────────────────────────────┘
                             ↓
    ┌─────────────────────────────────────────────┐
    │ 4. DRIVER NAME VALIDATION                   │
    │                                             │
    │ Rule: Uppercase, blacklist check            │
    │                                             │
    │ "SUTRISNO"        → "SUTRISNO" ✓           │
    │ "sutrisno"        → "SUTRISNO" ✓           │
    │ "RAFAY"           → FLAGGED ✗ (blacklist) │
    │ "AKBAR"           → FLAGGED ✗ (blacklist) │
    │ "M SYAICHONI"     → "M SYAICHONI" ✓        │
    │                                             │
    │ Blacklist words:                            │
    │ ["RAFAY", "AKBAR", "ADMIN", "DRIVER",      │
    │  "ONCALL", "REQUEST", "LOGISTIK", ...]     │
    └─────────────────────────────────────────────┘
                             ↓
    ┌─────────────────────────────────────────────┐
    │ 5. TIME FORMAT NORMALIZATION                │
    │                                             │
    │ Rule: Parse → 24-hour format               │
    │                                             │
    │ "SEGERA"              → "00:00" (priority) │
    │ "07:00"               → "07:00" ✓          │
    │ "18:00"               → "18:00" ✓          │
    │ "07:00 13/03/2026"    → "07:00" ✓          │
    │ "06:00/13-03-26"      → "06:00" ✓          │
    │ "21:00"               → "21:00" ✓          │
    └─────────────────────────────────────────────┘
                             ↓

┌────────────────────────────────────────────────────────────────┐
│              CLEANED & STANDARDIZED DATA                        │
├────────────────────────────────────────────────────────────────┤
│ ORDER_DATE: "2026-03-12"                  ✓ ISO format        │
│ UNIT_SPEC: "3 UNIT TWB 50 CBM"            ✓ Preserved         │
│ LOCATION: "ARGOPANTES"                    ✓ Standardized      │
│ LOAD_TIME: "07:00"                        ✓ 24H format        │
│ ROUTE: "CGK → SUB"                        ✓ Standardized      │
│ DRIVER: "SUTRISNO"                        ✓ Uppercase, valid  │
│ PHONE: "085353886066"                     ✓ 12 digits         │
│ COMPLETE: TRUE                             ✓ All fields filled │
│ CONFIDENCE_SCORE: 0.88                    ✓ Average F1 score  │
└────────────────────────────────────────────────────────────────┘
                             ↓
                Ready for Database Insert
```

---

## 6. DATABASE SCHEMA & PERSISTENCE

```
┌──────────────────────────────────────────────────────────────┐
│                   SQLITE DATABASE                             │
│                  (rafay_database.db)                          │
└──────────────────────────────────────────────────────────────┘

TABLE 1: order_rows
┌────────────────────────────────────────────────────────────┐
│ COLUMN                 │ TYPE        │ DESCRIPTION           │
├────────────────────────────────────────────────────────────┤
│ id                     │ INTEGER PK  │ Auto-increment        │
│ date                   │ DATE        │ Order date (ISO 8601) │
│ unit                   │ VARCHAR     │ Unit spec (3 TWB50)   │
│ location               │ VARCHAR     │ Loading location      │
│ time                   │ TIME        │ Loading time (24H)    │
│ route                  │ VARCHAR     │ Route (CGK→SUB)       │
│ driver                 │ VARCHAR     │ Driver name           │
│ phone                  │ VARCHAR     │ Contact phone         │
│ status                 │ VARCHAR     │ COMPLETE/INCOMPLETE   │
│ confidence_score       │ FLOAT       │ Avg NER confidence    │
│ is_complete            │ BOOLEAN     │ All fields filled?    │
│ created_at             │ DATETIME    │ Record creation time  │
│ updated_at             │ DATETIME    │ Last modification     │
│ revision_count         │ INTEGER     │ # of updates applied  │
│ notes                  │ TEXT        │ Admin annotations     │
└────────────────────────────────────────────────────────────┘

TABLE 2: chat_history
┌────────────────────────────────────────────────────────────┐
│ COLUMN                 │ TYPE        │ DESCRIPTION           │
├────────────────────────────────────────────────────────────┤
│ id                     │ INTEGER PK  │ Auto-increment        │
│ order_id               │ INTEGER FK  │ Reference to order    │
│ timestamp              │ DATETIME    │ Message timestamp     │
│ sender                 │ VARCHAR     │ Who sent message      │
│ raw_text               │ TEXT        │ Original message      │
│ event_type             │ VARCHAR     │ NEW_ORDER/REPAIR/REFILL
│ event_confidence       │ FLOAT       │ Classification score  │
│ processing_status      │ VARCHAR     │ SUCCESS/PARTIAL/FAIL  │
│ processed_at           │ DATETIME    │ Processing time       │
│ extracted_data         │ JSON        │ NER/Revision output   │
│ error_message          │ TEXT        │ If failed, why?       │
└────────────────────────────────────────────────────────────┘

TABLE 3: model_metadata
┌────────────────────────────────────────────────────────────┐
│ COLUMN                 │ TYPE        │ DESCRIPTION           │
├────────────────────────────────────────────────────────────┤
│ id                     │ INTEGER PK  │ Auto-increment        │
│ model_name             │ VARCHAR     │ indobert_NER, etc     │
│ model_version          │ VARCHAR     │ Semantic version      │
│ model_path             │ VARCHAR     │ Local/cloud path      │
│ training_date          │ DATE        │ When trained          │
│ training_dataset_size  │ INTEGER     │ # samples used        │
│ validation_f1_score    │ FLOAT       │ F1-score on test set  │
│ active                 │ BOOLEAN     │ Currently used?       │
│ activated_at           │ DATETIME    │ When put to production│
│ hyperparams            │ JSON        │ Training config       │
└────────────────────────────────────────────────────────────┘

RELATIONSHIPS:
┌─────────────────┐
│   order_rows    │ 1 ─────── * chat_history
│   (id: PK)      │         (order_id: FK)
└─────────────────┘
```

---

## 7. TRAINING & EVALUATION PIPELINE

```
┌──────────────────────────────────────────────────────────────┐
│            LABELED DATASET PREPARATION                        │
│         (Label Studio → JSON → Processed)                     │
└──────────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   ┌─────────┐    ┌──────────┐    ┌────────────┐
   │ NER Dataset │ Event Dataset  │ Revision   │
   │            │  (Classification)│ Matcher    │
   │ 8000 samples│  5000 samples   │ Dataset    │
   │ (annotated) │  (4 classes)    │ (pairs)    │
   └──────────┬──┘   └──────┬────┘   └────────┬─┘
              │             │                │
              ↓             ↓                ↓
        ╔──────────╗  ╔──────────╗  ╔──────────────╗
        ║Train/Test║  ║Train/Test║  ║Train/Test    ║
        ║Split     ║  ║Split     ║  ║Split 80/20   ║
        ║80/20     ║  ║80/20     ║  ║              ║
        ╚────┬─────╝  ╚────┬─────╝  ╚────┬─────────╝
             │             │             │
             ↓             ↓             ↓
      ┌──────────────────────────────────────────┐
      │      FINE-TUNING LOOP (3 epochs)         │
      ├──────────────────────────────────────────┤
      │ For each epoch:                          │
      │  1. Forward pass (IndoBERT → logits)     │
      │  2. Loss computation (CRF / CrossEnt)    │
      │  3. Backward pass (gradients)            │
      │  4. Optimizer step (AdamW)               │
      │  5. Eval on validation set               │
      │  6. Save best checkpoint (by F1-score)   │
      │                                          │
      │ Hyperparameters:                         │
      │  • Learning rate: 2e-5 (careful tuning)  │
      │  • Batch size: 16 (GPU memory limit)     │
      │  • Warmup: 0.1 * total_steps             │
      │  • Weight decay: 0.01 (regularization)   │
      └──────────────────────────────────────────┘
             │
             ↓
      ┌──────────────────────────────────────────┐
      │        EVALUATION ON TEST SET             │
      ├──────────────────────────────────────────┤
      │ Metrics Computed:                        │
      │                                          │
      │ NER Model:                               │
      │  • Precision per entity type             │
      │  • Recall per entity type                │
      │  • F1-score (macro & weighted)           │
      │  • Accuracy (token-level)                │
      │  • Expected F1: ~0.88+                   │
      │                                          │
      │ Event Classifier:                        │
      │  • Accuracy                              │
      │  • Precision / Recall per class          │
      │  • F1-score (weighted)                   │
      │  • ROC-AUC (per class)                   │
      │  • Expected Accuracy: ~0.86+             │
      │                                          │
      │ Revision Matcher:                        │
      │  • Accuracy (MATCH / NO_MATCH)           │
      │  • Precision / Recall (MATCH class)      │
      │  • MRR (Mean Reciprocal Rank)            │
      │  • Expected Accuracy: ~0.84+             │
      └──────────────────────────────────────────┘
             │
             ↓
      ┌──────────────────────────────────────────┐
      │   FINAL MODELS & MODEL VERSIONING        │
      ├──────────────────────────────────────────┤
      │ Saved Artifacts:                         │
      │  • models/indobert_NER/final_model/      │
      │    ├─ config.json                        │
      │    ├─ pytorch_model.bin (weights)        │
      │    ├─ tokenizer.json                     │
      │    └─ metrics.json (validation scores)   │
      │                                          │
      │  • models/indobert_event_classifier/...  │
      │  • models/indobert_revision_matcher/...  │
      │                                          │
      │ Version Tracking:                        │
      │  • Stored in model_metadata table        │
      │  • Can roll back if new version worse    │
      │  • A/B testing capability                │
      └──────────────────────────────────────────┘
```

---

**Version**: 1.0  
**Last Updated**: April 2026
