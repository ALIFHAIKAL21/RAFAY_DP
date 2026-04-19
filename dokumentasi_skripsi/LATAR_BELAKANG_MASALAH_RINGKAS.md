# LATAR BELAKANG MASALAH - RINGKAS (3-5 Paragraf)

## Konteks Masalah

PT. Rafay Logistik adalah perusahaan ekspedisi Indonesia yang saat ini beroperasi dengan volume ~200-300 orders per bulan yang dikelola oleh 2 orang admin melalui proses manual berbasis spreadsheet Excel. Dengan pertumbuhan yang diproyeksikan mencapai 500+ orders dalam 2 tahun ke depan, sistem manual saat ini menghadapi bottleneck serius. Data order berasal dari komunikasi WhatsApp grup operasR 1"), field vaional yang sangat tidak terstruktur—field labels bervariasi (misalnya "driver" vs "Driver" vs "DRIVElues penuh typo (lokasi "ARGOPANTES" vs "argo pantes*", plat "L 9511 AL" vs "L9511AL", nomor telp dengan format berbeda), dan format tanggal tidak konsisten. Proses input manual memakan waktu 3-5 menit per order dengan error rate 5-8% pada field kritis, sementara dengan pertumbuhan menjadi 500 orders/bulan akan membutuhkan tambahan 10+ admin atau solusi automation.

Masalah teknis yang dihadapi adalah: **(1) Inconsistency & Typo Handling** - field labels dan values sangat variatif dan memerlukan standardisasi otomatis, **(2) Multi-Slot Order Complexity** - satu order sering terdiri dari 5+ unit dengan data lengkap (driver, plat, phone) hanya pada 1 slot sementara slot lainnya partial dan menyusul kemudian via pesan terpisah, memerlukan tracking dan merge yang akurat, **(3) Revision Management & Disambiguation** - revisi data sering datang kapan saja dan format variatif ("REVISI DRIVER", "Rev: masih 18:00 CGK-SUB ganti driver Budi") dengan matching ke order mana yang ambiguous, dan **(4) Scalability Bottleneck** - sistem manual 2 admin dengan kapasitas maksimal 300 orders tidak sustainable untuk target pertumbuhan 500-10,000 orders.

Kesenjangan teknologi saat ini adalah pendekatan rule-based dan regex klasik tidak mampu menangani variasi dan ambiguitas dalam unstructured WhatsApp text. Diperlukan pendekatan Natural Language Processing berbasis deep learning yang dapat: (a) mengekstrak informasi terstruktur dari unstructured chat dengan toleransi typo tinggi, dan (b) melakukan semantic matching untuk menyelesaikan ambiguous reference dalam pesan revisi. Solusi yang diusulkan adalah **dual-model approach**: **(1) InDoBERT NER** (Named Entity Recognition) untuk mengekstrak 21 entity labels dari chat mentah dengan target 89% F1, dan **(2) Revision Matcher** (Semantic Similarity Classification) untuk match pesan revisi ke historical orders dengan akurasi target 90%, yang outperform rule-based matching sebesar 9%.

Kontribusi penelitian ini adalah: (a) **Akademis** - publikasi tentang aplikasi BERT untuk NER pada domain logistics Indonesia dan semantic matching untuk revision disambiguation, (b) **Praktis** - implementasi pipeline end-to-end yang menghasilkan automasi 92% dengan error <1% untuk PT. Rafay, meningkatkan kapasitas dari 300 ke 10,000+ orders dan mengurangi waktu input dari 3-5 menit ke <30 detik per order, dan (c) **Industrial** - template yang dapat diadaptasi untuk ekspedisi lain di Indonesia. ROI proyeksi adalah break-even dalam 5-6 bulan dengan penghematan operational sebesar 12-15M IDR per tahun, menjadikan RAFAY IDP v2.0 sebagai case study berharga untuk automation dalam logistics.

---

**Catatan:**
- Dokumen ini merangkum semua 4 masalah utama + konteks + solusi dalam 4 paragraf padat
- Cocok untuk quick reference, executive summary, atau foundation ketika generate dengan Gemini
- Tingkat detail seimbang antara business perspective dan technical perspective
- Siap digunakan langsung dalam skripsi atau diperluas menjadi versi 2000-3000 kata
