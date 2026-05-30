## PROMPT GEMINI - BATASAN MASALAH FINAL (MAKS. 12 POIN)

Gunakan prompt di bawah ini langsung ke Gemini untuk menyusun kalimat final BAB 1.4.

```text
Anda berperan sebagai editor akademik skripsi. Tulis section "Batasan Masalah" BAB 1.4 berdasarkan konteks proyek nyata berikut, dengan gaya formal, natural, dan defensif (strategic scope, bukan nada minta maaf).

KONTEKS PROYEK (WAJIB JADI ACUAN):
- Proyek: RAFAY IDP (Intelligent Document Processing) untuk PT Rafay Logistik.
- Tujuan bisnis: mempercepat konversi chat order WhatsApp menjadi data operasional terstruktur, menekan human error, membantu admin menangani volume order yang meningkat.
- Status saat ini: masih fase pengembangan purwarupa/POC, belum implementasi operasional penuh.
- Pipeline utama: ekstraksi entitas order (NER), klasifikasi event pesan (order/revisi/non-order), pencocokan revisi/refill terhadap order existing, lalu normalisasi rule-based.
- Input dominan: chat operasional WhatsApp berbahasa Indonesia dengan typo, variasi format waktu/tanggal, dan data parsial.
- Output utama: tabel hasil parsing, status unit (ASSIGNED/PARTIAL/UNASSIGNED), ekspor Excel, dan opsi simpan database.

BATASAN MASALAH FIKS (MAKSIMAL 12, WAJIB TERCAKUP SEMUA):
1) Sumber data dibatasi hanya pada teks chat WhatsApp operasional PT Rafay Logistik; data dari SPK, sistem alokasi armada, GPS tracking, pricing engine, dan sistem eksternal lain tidak termasuk objek ekstraksi.
2) Cakupan pesan difokuskan pada pesan order baru, revisi, dan refill yang relevan dengan pembentukan data order; pesan negosiasi komersial, keluhan pelanggan, dan komunikasi non-operasional di luar scope.
3) Entitas yang diekstrak dibatasi pada field inti operasional (mis. tanggal RO, waktu/tanggal loading, jumlah unit, jenis unit, lokasi asal, tujuan/rute, driver, nopol, no HP); field bisnis lanjutan di luar teks tidak dipaksakan terisi.
4) Sistem tidak melakukan imputasi otomatis untuk data yang benar-benar tidak ada di pesan; field yang hilang dibiarkan kosong/parsial dan diserahkan ke proses verifikasi admin.
5) Model bersifat domain-specific untuk pola data PT Rafay Logistik; generalisasi ke perusahaan logistik lain tidak dijamin tanpa pelatihan ulang dan penyesuaian aturan.
6) Pendekatan model dibatasi pada transfer learning berbasis InDoBERT (fine-tuning), bukan pengembangan arsitektur foundation model baru dari nol.
7) Komponen rule-based post-processing disusun manual dari observasi pola historis (typo label, variasi no HP, format nopol/waktu/tanggal), bukan automatic rule learning.
8) Sistem diposisikan sebagai decision-support (human-in-the-loop), bukan decision-maker penuh; validasi akhir dan keputusan operasional tetap berada pada admin.
9) Implementasi operasional real-time belum menjadi cakupan: belum mencakup integrasi API WhatsApp Business, orkestrasi message queue, dan SLA produksi.
10) Pengujian skala produksi (load/stress test), hardening keamanan, dan reliability engineering (failover/observability penuh) belum menjadi fokus penelitian ini.
11) Evaluasi kinerja difokuskan pada metrik NLP/ekstraksi dan matching (precision, recall, F1, serta metrik ketepatan parsing/matching yang relevan), bukan metrik finansial bisnis seperti ROI atau efisiensi biaya menyeluruh.
12) Validasi dilakukan pada data historis internal periode penelitian (Oktober 2025-Maret 2026) dan skenario uji terkontrol; hasil belum merepresentasikan seluruh variasi musiman multi-tahun.

INSTRUKSI OUTPUT:
- Berikan 2 versi output:
  A. Versi daftar bernomor 1-12 (setiap poin 1-2 kalimat akademik yang tegas).
  B. Versi naratif 4-6 paragraf yang koheren, siap tempel ke BAB 1.4.
- Bahasa: Indonesia formal akademik, kalimat jelas, tidak bertele-tele.
- Dilarang mengubah substansi 12 batasan di atas; Anda hanya boleh merapikan redaksi.
- Pastikan ada benang merah: fokus riset adalah kualitas ekstraksi dan ketepatan pengolahan revisi pada fase POC, bukan deployment produksi penuh.
```

