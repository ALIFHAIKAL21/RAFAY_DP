# Lingkungan Aman Pengujian Fitur Sesi

Lingkungan ini dipakai untuk mengembangkan fitur sesi tanpa menyentuh data aplikasi utama.

## Pemisahan

- Aplikasi utama: `stage2_pair_visual_test.py`
- Aplikasi test: `stage2_pair_visual_test copy.py`
- Port utama: `8501`
- Port test: `8502`
- DB utama: `logistic_parser`
- DB test: `logistic_parser_session_test`
- Model NER dan SPC tetap memakai artefak lokal yang sama secara read-only.

File aplikasi test memiliki guard fail-closed. File tersebut menolak start jika:

- `IDP_SESSION_TEST_MODE` tidak aktif;
- `DATABASE_URL` tidak diberikan;
- nama database tidak sama dengan `IDP_SESSION_TEST_DB_NAME`; atau
- nama database tidak berakhiran `_session_test`.

Karena itu, jangan menjalankan file copy langsung dengan perintah `streamlit run`.

## Menjalankan

```powershell
.\run_session_test.ps1
```

Buka:

```text
http://localhost:8502
```

Untuk port lain:

```powershell
.\run_session_test.ps1 -Port 8503
```

Untuk menghentikan server test:

```powershell
.\stop_session_test.ps1
```

Script stop memeriksa command line proses. Jika port dipakai aplikasi lain, penghentian
dibatalkan.

Launcher akan:

1. membaca kredensial PostgreSQL lokal;
2. membuat DB test jika belum tersedia;
3. memvalidasi bahwa nama DB aman;
4. membuat schema hanya pada DB test;
5. menyetel environment test sebelum modul `db.*` diimpor; dan
6. menjalankan Streamlit pada port test.

## Verifikasi

```powershell
.\venv\Scripts\python.exe .\scripts\verify_session_test_isolation.py
```

Output harus menunjukkan `Source DB` dan `Test DB` yang berbeda.

## Konfigurasi Lokal

Jika kredensial PostgreSQL berbeda, salin `.env.session_test.example` menjadi
`.env.session_test`, lalu isi nilai lokal. File `.env.session_test` diabaikan Git.

Jangan arahkan `IDP_SESSION_TEST_ADMIN_URL` ke database produksi jarak jauh.

## Aturan Pengembangan

- Implementasi eksperimen fitur sesi hanya dilakukan pada aplikasi copy dan DB test.
- Tombol `Reset Output` pada aplikasi test hanya boleh menghapus DB test.
- Jangan mengubah suffix `_session_test`.
- Sebelum memindahkan fitur ke aplikasi utama, jalankan test regresi NER, rekonsiliasi,
  reset, download, pergantian sesi, dan isolasi analytics antarsesi.

## Fitur Workspace Sesi

Versi test menggunakan satu schema PostgreSQL per sesi:

```text
public.extraction_sessions
extract_session_<uuid>.raw_chats
extract_session_<uuid>.order_dataset
extract_session_<uuid>.stage2_match_audits
```

Fitur yang tersedia:

- membuat sesi baru dari sidebar;
- berpindah sesi melalui riwayat sesi;
- pencarian sesi;
- nama sesi otomatis dari rentang Tgl RO;
- rename manual yang tidak ditimpa nama otomatis;
- arsip dan pemulihan sesi;
- hapus sesi dengan konfirmasi;
- reset hanya untuk sesi aktif;
- analitik NER dan rekonsiliasi terisolasi per sesi; dan
- backup ZIP per sesi yang berisi CSV order, raw chat, audit matcher, dan metadata.
