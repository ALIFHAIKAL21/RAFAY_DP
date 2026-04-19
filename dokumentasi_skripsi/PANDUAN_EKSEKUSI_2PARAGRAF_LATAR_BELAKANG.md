# ⚡ PANDUAN EKSEKUSI: GENERATE 2 PARAGRAF AKHIR LATAR BELAKANG MASALAH

**Goal:** Tambahkan 2 paragraf akhir ke BAB 1.2 Latar Belakang Masalah untuk nyambung dengan BAB 1.3 Identifikasi Masalah  
**Timeline:** ~20-30 menit total  
**Output:** 2 paragraf akademis (~1200-1800 kata) yang detail model + hybrid approach

---

## 📋 TIM DELIVERABLES (SUDAH READY):

### 1️⃣ **PROMPT_GEMINI_LATAR_BELAKANG_2PARAGRAF_AKHIR.md** 
- Ready-to-copy Gemini prompt
- Struktur ultra-detail
- Input latar belakang Anda (3 paragraf existing)
- Detailed requirements untuk 2 paragraf akhir

### 2️⃣ **REFERENSI_TEKNIS_MODEL_DETAIL.md**
- Cheat sheet semua model details
- Specifications lengkap (architecture, training, output)
- Untuk Anda baca SEBELUM generate (optional tapi recommended)

---

## 🚀 EXECUTION FLOW (Step-by-Step):

### **Phase 1: Persiapan (5 menit)**

**Step 1:** Buka & baca reference document
```
File: REFERENSI_TEKNIS_MODEL_DETAIL.md
Read: MODEL #1 (NER) + MODEL #2 (Revision Matcher) sections
Time: ~3-5 menit untuk understand architecture
Purpose: Familiar dengan semua details sebelum Gemini generate
```

**Step 2:** Understand struktur latar belakang existing Anda
```
Current status: 3 paragraf sudah ada
Paragraf 1: Industry context + Rafay intro
Paragraf 2: Problem #1 (Data Entry Workload)
Paragraf 3: Problem #2 (Semantic Ambiguity)

Goal: Add 2 paragraf:
Paragraf 4: Why Hybrid approach? (Bridge dari masalah ke solusi)
Paragraf 5: Technical model details (Spesifikasi lengkap)
```

---

### **Phase 2: Generate (5-10 menit)**

**Step 3:** Copy Gemini prompt
```
File: PROMPT_GEMINI_LATAR_BELAKANG_2PARAGRAF_AKHIR.md
Section: "## 🎯 PROMPT MASTER (COPY-PASTE KE GEMINI):"
From: "TASK: Generate 2 PARAGRAF AKHIR LATAR BELAKANG..."
To: "[Academic tone throughout]"
Copy: Seluruh section tersebut
```

**Step 4:** Paste ke Gemini & generate
```
1. Buka: gemini.google.com
2. Buat: Chat baru
3. Paste: Entire prompt
4. Submit: Tunggu output (~2-3 menit)
5. Copy: Output Gemini ke text editor
```

**Step 5:** Quick quality check
```
Checklist:
✓ 2 paragraf (tidak bullet points)?
✓ Semua 4 masalah tercakup (hybrid, NER detail, Revision Matcher detail, rules)?
✓ Model names exact (indolem/..., indobenchmark/...)?
✓ 21 entity labels mentioned?
✓ Technical metrics present (batch size, epochs, learning rate)?
✓ Tone confident, tidak apologetic?

Jika ada yang kurang → re-prompt dengan clarification
```

---

### **Phase 3: Integration (5-10 menit)**

**Step 6:** Append ke latar belakang existing
```
Current file: thesis BAB 1.2 atau (LATAR_BELAKANG_MASALAH_RINGKAS.md)
Append: Gemini output sebagai Paragraf 4-5 (setelah existing 3 paragraf)
Result: BAB 1.2 yang complete dengan 5 paragraf cohesive
```

**Step 7:** Flow verification
```
Check: Apakah nyambung smooth?
- Paragraf 3 → Paragraf 4: Ada transisi dari masalah ke solusi?
- Paragraf 4 → Paragraf 5: Ada transisi dari why hybrid ke technical?
- Paragraf 5 → Ende: Ada closing statement navigasi ke BAB 2?

Jika tidak smooth → manual edit connectors
```

**Step 8:** Final review
```
Read through all 5 paragraf:
- Logical flow? ✓
- Technical accuracy? ✓
- Academic tone? ✓
- Length reasonable (~2000-3000 words total)? ✓
- Bridge menuju BAB 2? ✓

Approved! → Ready untuk advisor
```

---

## 📝 CURRENT LATAR BELAKANG ANDA (UNTUK REFERENCE):

**Paragraf 1:**
```
Seiring pesatnya perkembangan industri logistik, efisiensi pengelolaan informasi 
menjadi kunci utama... [context setting + Rafay intro]
```

**Paragraf 2:**
```
Masalah utama operasional berakar pada karakteristik pesanan multi-unit...
[Problem #1: Data Entry Workload Escalation]
```

**Paragraf 3:**
```
Kondisi operasional perusahaan kian kompleks akibat karakteristik aliran data...
[Problem #2: Semantic Ambiguity & Partial Data]
```

**[INSERT Gemini OUTPUT HERE as Paragraf 4-5]**

---

## 🎯 EXPECTED OUTPUT DARI GEMINI (Preview):

### **Paragraf 4 (Why Hybrid):** ~600-900 kata
- Opening: Situasi masalah ganda
- Why rule-based insufficient (15+ label variations, typo, implicit references)
- Why pure ML insufficient (~82% accuracy ceiling)
- Why hybrid necessary (optimal integration)
- Benefits positioning
- Transition ke technical details

### **Paragraf 5 (Technical Details):** ~600-900 kata
- Architecture overview (2 models + rules)
- **NER Model:**
  - indolem/indobert-base-uncased
  - 21 entity labels (BIO scheme)
  - Max 128 tokens
  - Training: batch 8, 5 epochs, 2e-5 lr
  - Output: 10-12 structured fields
- **Revision Matcher:**
  - indobenchmark/indobert-base-p2
  - Binary classification (MATCH/NO_MATCH)
  - Max 256 tokens (concatenated pair)
  - Training: batch 8, 4 epochs, 2e-5 lr
  - Output: Top-3 ranked candidates with scores
- Rule-based refinement layer
- Integration flow diagram (textual)
- Bridge ke BAB 2 (literature review coming next)

---

## ⚠️ POTENTIAL ISSUES & SOLUTIONS:

### Issue #1: Output TERLALU TEKNIS
**Symptom:** Terlalu banyak jargon, tidak accessible
**Solution:** Re-prompt: "Jelaskan architecture lebih accessible, explain BERT & BIO scheme untuk non-ML reader"

### Issue #2: Output TERLALU GENERAL
**Symptom:** Tidak mention spesifik model names, numbers
**Solution:** Re-prompt: "Sebutkan exact model names (indolem/indobert-base-uncased, indobenchmark/indobert-base-p2), configuration values (128 tokens, 21 labels, batch size 8)"

### Issue #3: Output TERLALU PANJANG
**Symptom:** 3-4 paragraf instead of 2
**Solution:** Re-prompt: "Exactly 2 paragraf only, bukan 3+. Combine points jika perlu."

### Issue #4: TONE TERASA APOLOGETIC
**Symptom:** "We couldn't... we were limited..."
**Solution:** Manual edit: Replace dengan "This research focuses on..."

### Issue #5: TIDAK TRANSITION KE BAB 2
**Symptom:** Ending abrupt, tidak bridge ke literature review
**Solution:** Add manual closing sentence: "Pemahaman mendalam tentang [teknik-teknik teknis ini] memerlukan kajian literatur terkini mengenai..."

---

## 📊 SUCCESS CRITERIA (Ketika selesai):

✅ **Content Complete:**
- [ ] 2 paragraf (exactly)
- [ ] ~1200-1800 kata total
- [ ] All 4 aspects covered (why hybrid, NER detail, RevisionMatcher detail, rules)

✅ **Technical Accurate:**
- [ ] Model names exact
- [ ] Architecture specs correct (768 hidden, 12 heads, 12 layers)
- [ ] Training config correct (batch 8, epochs 5/4, lr 2e-5)
- [ ] Entity labels count (21 total)
- [ ] Sequence lengths (128 vs 256)

✅ **Narrative Quality:**
- [ ] Smooth transition from Problem → Solution → Details
- [ ] Academic tone throughout
- [ ] Bridge ke BAB 2 clear
- [ ] Confident, not apologetic

✅ **Integration Ready:**
- [ ] Selaras dengan 3 paragraf existing
- [ ] Cohesive 5-paragraph flow
- [ ] Ready untuk submit ke advisor

---

## 🔄 RECOMMENDED REVISION CYCLE:

1. **First Generation:** Generate with prompt
   - Expected: 70-80% quality
   - Common issues: Minor tone tweaks, some detail gaps

2. **Review & Identify Gaps:** Check against criteria above
   - Time: 5 minutes
   - Identify what needs improvement

3. **Targeted Re-prompt:** If issues found
   - Re-prompt specific clarifications
   - Example: "Tambahkan detail architecture figure (hidden size, heads, layers)"
   - Time: 3 minutes

4. **Manual Refinement:** Final polish
   - Smooth connectors if needed
   - Fix any jargon inconsistencies
   - Verify flow
   - Time: 5-10 minutes

5. **Final Integration:** Append to thesis
   - Integrate with existing 3 paragraf
   - Read full 5-paragraph flow
   - Approve
   - Time: 5 minutes

**Total Cycle Time:** 15-25 menit untuk 90%+ quality output

---

## 💡 PRO TIPS:

### Tip #1: Preview Model Details First
```
Sebelum generate di Gemini, baca REFERENSI_TEKNIS_MODEL_DETAIL.md
Ini membantu Anda: 
1. Understand what should be in output
2. Catch errors in output lebih cepat
3. Re-prompt dengan targeted feedback
Time investment: 5 min, Time saved: 10+ min during refinement
```

### Tip #2: Save All Versions
```
Jangan overwrite → Keep multiple versions:
- v1_gemini_original.md (raw output)
- v1_gemini_refined.md (after first re-prompt)
- v1_final.md (fully integrated ke thesis)
Helps: Easy rollback if needed, track refinement history
```

### Tip #3: Validate Against Original Problems
```
After generate, re-read 3 paragraf existing
Verify Gemini output:
✓ Specifically addresses Problem #1 (workload) solution?
✓ Specifically addresses Problem #2 (ambiguity) solution?
✓ Explains WHY each model is needed for each problem?
Helps: Ensure coherence end-to-end
```

### Tip #4: Architecture Diagram (Optional Future)
```
After finishing latar belakang, consider adding:
- Text-based pipeline diagram (in thesis)
- FlowChart: Input → NER → Rules → Output
- Model architecture visual (BERT structure with dimensions)
Not in scope now, but useful for presentation
```

---

## 📚 FINAL CHECKLIST SEBELUM SUBMIT KE ADVISOR:

### BAB 1.2 Latar Belakang Masalah COMPLETE:

**Struktur (5 Paragraf):**
- [ ] Paragraf 1: Industry context + Rafay intro
- [ ] Paragraf 2: Problem #1 (Data Workload)
- [ ] Paragraf 3: Problem #2 (Ambiguity)
- [ ] Paragraf 4: Why Hybrid approach + NER benefits (Your Gemini output)
- [ ] Paragraf 5: Technical model specs (Your Gemini output)

**Content Quality:**
- [ ] Logical flow dari start to end?
- [ ] All problems explained + justified?
- [ ] Solution approach clear?
- [ ] Technical details complete?
- [ ] Academic tone consistent?
- [ ] Length appropriate (~2500-3000 words)?
- [ ] No garbled text atau typos?

**Integration with Other BAB 1 Sections:**
- [ ] Links dengan BAB 1.1 (Pengenalan)?
- [ ] Sets up BAB 1.3 (Identifikasi Masalah)?
- [ ] Sets up BAB 1.4 (Batasan Masalah)?
- [ ] Natural transition mendatang ke BAB 2?

**Ready to Submit?**
- [ ] Advisor-ready quality
- [ ] Approved by yourself first
- [ ] Saved multiple backup copies

---

## 🎬 ACTION ITEMS (Next Steps):

**Immediately (Today):**
1. [ ] Read REFERENSI_TEKNIS_MODEL_DETAIL.md (5 min)
2. [ ] Open PROMPT_GEMINI_LATAR_BELAKANG_2PARAGRAF_AKHIR.md (2 min)

**Within 1 Hour:**
3. [ ] Copy prompt section to Gemini (3 min)
4. [ ] Generate output (5 min wait)
5. [ ] Quick review against checklist (5 min)

**Within Next 2 Hours:**
6. [ ] Do any re-prompts if needed (5-10 min)
7. [ ] Manual refinement (5-10 min)
8. [ ] Integrate to thesis (10 min)
9. [ ] Final read-through 5 paragraf (10 min)

**Result:** ✅ BAB 1.2 Latar Belakang Masalah COMPLETE & READY

---

## 📞 SIAP EKSEKUSI?

**Step 0:** Baca file ini (selesai ✓)

**Step 1:** Buka: `REFERENSI_TEKNIS_MODEL_DETAIL.md`  
**Step 2:** Buka: `PROMPT_GEMINI_LATAR_BELAKANG_2PARAGRAF_AKHIR.md`  
**Step 3:** Copy prompt → Paste ke Gemini  
**Step 4:** Generate!

→ **Ada pertanyaan sebelum generate? Tanyakan sekarang!**  
→ **Sudah siap? Langsung eksekusi di Gemini!** 🚀

---

**NEXT MILESTONES (BAB 1.2 complete → apa selanjutnya?):**

- ✅ BAB 1.1 Pengenalan (existing)
- ✅ BAB 1.2 Latar Belakang (just completed)
- ✅ BAB 1.3 Identifikasi Masalah (ready prompt: README_KONSULTASI_FINAL.md)
- ✅ BAB 1.4 Batasan Masalah (ready prompt: PROMPT_GEMINI_BATASAN_MASALAH.md)
- ⏳ BAB 1.5 Tujuan & Kontribusi (next)
- ⏳ BAB 1.6 Manfaat & Relevansi (next)
- ⏳ **BAB 1 COMPLETE** (then move to BAB 2: Literature Review)

---

**Status:** 🟢 READY TO EXECUTE  
**Last Updated:** April 13, 2026  
**Estimated Completion:** ~25 minutes from now
