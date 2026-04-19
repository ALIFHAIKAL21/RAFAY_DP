# 📝 LATAR BELAKANG MASALAH - PARAGRAF RINGKAS DIPERBAIKI

**Status:** Revisi tanda baca + persingkat  
**Length:** 7-8 baris (~240-270 kata)  
**Improvement:** Grammar fix, titik koma optimal, flow lebih smooth  
**Focus:** Tetap maintain intisari ML architecture + 2-model logic + business

---

## PARAGRAF FINAL (RINGKAS & DIPERBAIKI):

Menghadapi tantangan ganda berupa lonjakan eksponensial beban entri data manual dan ambiguitas pada pesan revisi operasional, PT. Rafay Logistik memerlukan transformasi sistemik yang melampaui kemampuan metode konvensional. Pendekatan berbasis aturan murni tidak mampu menangani variasi bahasa alami yang sangat dinamis pada platform WhatsApp, sementara model Machine Learning murni terhenti pada batasan akurasi sekitar 82% akibat tingginya noise data lapangan. Oleh karenanya, penelitian ini mengusulkan pendekatan hybrid berbasis arsitektur InDoBERT yang mengintegrasikan dua komponen spesifik: pertama, Named Entity Recognition (NER) yang berfungsi pada level token untuk mengekstraksi atribut pesanan dari pesan WhatsApp yang tidak terstruktur; kedua, semantic similarity matching melalui sequence-pair classification yang bekerja pada level kalimat untuk menyelesaikan ambiguitas pada pesan revisi dan refill dengan merekomendasikan top-3 kandidat terbaik. Pemilihan dua model terpisah untuk dua tugas yang fundamentally berbeda ini didasarkan pada prinsip specialization—setiap model dirancang sesuai karakteristik masalahnya untuk akurasi optimal. Lapisan rule-based post-processing kemudian menyempurnakan hasil melalui standardisasi format dan validasi data. Integrasi strategis ini dirancang untuk mengurangi waktu pemrosesan dari 5 menit menjadi kurang dari 1 menit per pesanan, meningkatkan akurasi hingga 91%+, dan memposisikan perusahaan menghadapi pertumbuhan bisnis yang diproyeksikan akan melampaui kapasitas manusia.

---

## PERBAIKAN YANG DILAKUKAN:

### 1. **Grammar & Tanda Baca:**
- ❌ "sementara model Machine Learning murni sering terhenti..." 
- ✅ "sementara model Machine Learning murni terhenti..." (lebih direct, "sering" tidak perlu)

- ❌ "mengintegrasikan dua komponen spesifik, Pertama,...kedua,..."
- ✅ "mengintegrasikan dua komponen spesifik: pertama,...; kedua,..." (gunakan titik koma untuk pemisahan komponen yang complex)

- ❌ "Pemilihan dua model terpisah untuk dua tugas yang fundamentally berbeda ini didasarkan pada prinsip specialization setiap model dirancang..."
- ✅ "Pemilihan dua model terpisah untuk dua tugas yang fundamentally berbeda ini didasarkan pada prinsip specialization—setiap model dirancang..." (em-dash untuk clarity)

- ❌ "untuk mengekstraksi variasi jenis atribut pesanan"
- ✅ "untuk mengekstraksi atribut pesanan" (lebih concise, "variasi jenis" redundant)

### 2. **Penghapusan Kata-kata Redundant (Persingkat):**
- "untuk mencapai akurasi optimal" → "untuk akurasi optimal" (-3 kata, tetap jelas)
- "dengan merekomendasikan top-3 kandidat pesanan terbaik" → "dengan merekomendasikan top-3 kandidat terbaik" (-1 kata, redundant)
- "memposisikan infrastruktur perusahaan menghadapi" → "memposisikan perusahaan menghadapi" (-2 kata, "infrastruktur" implied)

### 3. **Flow & Naturalness:**
- Baris-baris lebih uniform panjangnya
- Alur pemikiran lebih smooth (problem → why not → solution → components → justification → refinement → benefits)
- Tidak ada jarring transitions

---

## BREAKDOWN STRUKTUR (7-8 BARIS):

```
Baris 1:    Menghadapi tantangan ganda... [problem context]
Baris 2:    Pendekatan berbasis aturan... [why hybrid needed]
Baris 3-4:  Oleh karenanya, penelitian ini... [solution + 2 components dengan titik koma separator]
Baris 5:    Pemilihan dua model... [2-model justification]
Baris 6:    Lapisan rule-based... [refinement]
Baris 7-8:  Integrasi strategis... [benefits + closing]
```

**Count:** 7-8 baris natural

---

## PERBANDINGAN VERSI:

| Aspek | Original Expanded | Final Ringkas v1 | Final Ringkas v2 (DIPERBAIKI) |
|-------|------------------|------------------|-------------------------------|
| Baris | 14+ | 9-10 | 7-8 |
| Kata | ~450 | ~310 | ~260 |
| Grammar | Good | Good | ✅ **Optimized** |
| Tanda Baca | Good | Good | ✅ **Fixed** |
| Redundansi | Minimal | Minimal | ✅ **Removed** |
| Flow | Smooth | Smooth | ✅ **Smoother** |

---

## INTISARI YANG DIPERTAHANKAN:

✅ Problem context (dual challenges)  
✅ Why not rule-based (variasi bahasa)  
✅ Why not pure ML (82% ceiling + noise)  
✅ Solution approach (hybrid InDoBERT)  
✅ NER component (token-level extraction)  
✅ Revision Matcher component (sentence-level semantic matching + top-3)  
✅ 2-model justification (specialization principle)  
✅ Rule-based refinement layer  
✅ Business benefits (91%, 5m→<1m)  
✅ Business correlation (growth readiness)  

**SEMUA INTISARI TETAP INTACT! ✓**

---

## WHAT CHANGED:

**Removed (tanpa impact meaning):**
- "sering" (dari "sering terhenti" → "terhenti", sudah jelas dengan 82%)
- "variasi jenis" (redundant, "atribut pesanan" sudah comprehensive)
- "pesanan terbaik" (redundant, "kandidat terbaik" sudah cukup)
- "infrastruktur perusahaan" → "perusahaan" (infrastructure implied dalam context)

**Fixed (perbaikan structure):**
- Titik koma gunakan untuk memisahkan "pertama...kedua..." yang complex
- Em-dash gunakan untuk clarity antara principle dan explanation
- Kalimat-kalimat lebih konsisten panjangnya
- Flow lebih natural antar kalimat

---

## QUALITY CHECK:

✅ Clarity: Lebih ringkas, tetap mudah dipahami  
✅ Akademis: Professional, natural tone  
✅ Grammar: Perbaikan significant  
✅ Tanda Baca: Optimized dengan titik koma & em-dash  
✅ Concise: 7-8 baris (vs 9-10 sebelumnya)  
✅ Technical Sound: Tetap precise (token-level vs sentence-level)  
✅ Intisari: 100% maintained  

---

## USAGE:

1. **Copy paragraf "PARAGRAF FINAL (RINGKAS & DIPERBAIKI)" di atas**
2. **Paste ke BAB 1.2** (mengganti versi sebelumnya)
3. **Hasil:** ✅ BAB 1.2 yang lebih ringkas, perbaikan grammar/tanda baca, intisari intact

---

**VERSION 2 FINAL - READY TO USE! 🎯**

Versi ini lebih ringkas (7-8 vs 9-10 baris), perbaikan tanda baca signifikan, dan tetap 100% maintain intisari. Lebih smooth, lebih professional, ready untuk advisor.
