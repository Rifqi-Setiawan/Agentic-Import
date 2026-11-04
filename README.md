# Artha — Agentic Import MVP

Workspace pemeriksaan dokumen impor dengan FastAPI, PostgreSQL, LangGraph, React/Vite dan AI melalui **9Router**. Satu pengguna terikat ke satu perusahaan.

## Demo

- Web: https://artha.rifqisetiawan.my.id
- API: https://artha.rifqisetiawan.my.id/docs
- Health: https://artha.rifqisetiawan.my.id/health
- Staf: staf@mitrakemas.co.id
- Reviewer: reviewer@mitrakemas.co.id
- Admin: admin@mitrakemas.co.id
- Password akun demo: imporjaga123

Data perusahaan dan berkas contoh fiktif. Pengajuan PIB tetap dilakukan manusia di luar aplikasi.

## Alur mencoba

1. Login staf, buat kiriman dengan referensi unik. Isi kurs demo secara eksplisit atau CIF rupiah yang sudah diketahui. Untuk melihat SMTP sandbox, gunakan penerima fiktif `tim-impor@mitrakemas.co.id`; tidak ada pengiriman eksternal.
2. Unggah invoice PDF berteks di tab Dokumen. Worker mengekstrak barang dan menjalankan model 9Router, menyimpan bukti serta langkah secara langsung.
3. Buka Barang dan Jejak. Jawab pertanyaan atau unggah datasheet bila atribut kurang. Usulan baru membutuhkan review manusia.
4. Login reviewer, setujui atau ubah kode katalog dengan catatan. Sistem menghitung ulang kepatuhan dan pungutan.
5. Kelengkapan invoice, packing list, B/L/AWB dan izin yang relevan diperiksa. Dokumen pending dan review terbuka menghalangi kesiapan.
6. Admin dapat menjalankan aturan SIMULASI pos 8481; pencocokan dilakukan menurut HS, bukan nomor kiriman tetap.

## Batas prototipe yang perlu diketahui

- Retrieval saat ini **lexical catalogue**, bukan embedding/vector search. Pemilihan dan penalaran menggunakan model nyata melalui 9Router; kode dan kutipan divalidasi terhadap katalog.
- Tarif/kurs dataset demo memerlukan verifikasi sumber sebelum penggunaan kepabeanan sungguhan. Kurs baru tidak diasumsikan otomatis dari model. Pungutan adalah estimasi demonstrasi.
- SMTP default adalah **sandbox lokal 127.0.0.1:1025**, tidak meneruskan pesan ke internet. Receipt disimpan privat. Status sent berarti adapter SMTP menerima pesan, bukan pemasok eksternal membacanya.
- Tidak ada pengajuan CEISA, IMAP produksi, vision/OCR, atau jaminan klasifikasi hukum. PDF scan/terenkripsi tidak didukung MVP ini.
- Biaya USD tidak diisi bila harga model belum dikonfigurasi. Token diambil dari respons gateway; tidak ada angka token buatan.
- Recovery menggunakan pekerjaan persisten dan pass idempoten; tidak mengklaim PostgresSaver checkpoint LangGraph.
- Angka akurasi pada laporan lama tidak valid sebagai benchmark agent live. Lihat reports/README.md. Tidak ada klaim akurasi final sebelum evaluasi yang dapat direproduksi.

## Arsitektur

- src/domain: kalkulasi Decimal, readiness dan aturan murni.
- src/services: repository transaksi, ekstraksi PDF, retrieval, loop model/tools, bukti, checklist, dan hasil pass.
- src/agent: adapter jaringan 9Router dan graph orkestrasi.
- src/api: kontrak HTTP, otorisasi, upload, read models dan SSE.
- src/worker: dispatcher, lease/heartbeat, outbox dan followup.
- frontend/src/components: detail kiriman, trace, antrean kerja dan referensi; hasil diambil dari API.

## Menjalankan dan memverifikasi

Gunakan Python3.12, PostgreSQL, .venv dan konfigurasi .env dari .env.example. Rahasia dan runtime mailbox tidak masuk Git.

```bash
pip install -e .
PYTHONPATH=. python scripts/migrate_runtime.py
PYTHONPATH=. uvicorn src.api.main:app --host 127.0.0.1 --port 8120
PYTHONPATH=. python -m src.worker.main
python scripts/smtp_sandbox.py
cd frontend && npm ci && npm run build
```

Pengujian yang melakukan mutasi harus memakai imporjaga_test, bukan database demo aktif:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_acceptance_protected.py tests/test_audit_api_regressions.py tests/test_audit_acceptance_v2.py -q
PYTHONPATH=. .venv/bin/python tests/live_pipeline_smoke.py
```

Suite pengujian dilengkapi dengan guard isolasi sesi penuh (`tests/conftest.py`) yang secara ketat memaksa `TEST_DATABASE_URL` (`imporjaga_test`) sebelum modul tes di-load dan memverifikasi koneksi database aktif via raw connection dan SQLAlchemy engine.

### Sinkronisasi Katalog Referensi & Fixtures Demo

Data referensi resmi BTKI 2022 (2.614 kode HS dari DJBC), perpustakaan regulasi JDIH Kemenkeu (5 PMK), serta fixtures fiktif realistis (14 kiriman fiktif, 28 item, dan 41 PDF watermarked DEMO di `data/demo/documents/`) disinkronkan secara aditif dan idempoten via `scripts/import_reference_catalog.py`:

```bash
# 1. Mode Uji / Test Database (default, wajib lolos guard imporjaga_test)
.venv/bin/python scripts/import_reference_catalog.py --company-id <COMPANY_ID>

# 2. Mode Live Production Apply (HANYA dijalankan oleh operator Parent berwenang setelah verifikasi PASS)
.venv/bin/python scripts/import_reference_catalog.py --company-id 1 --live --apply
```

Perintah di atas:
- Mengarsipkan aturan placeholder lartas global warisan (`company_id IS NULL AND source = 'INSW Official Regulatory Database'`) menjadi `is_active = false` dan `source = 'Legacy Seed (Archived Placeholder)'` tanpa menghapus riwayat baris (tanpa DELETE).
- Mempertahankan aturan simulasi spesifik perusahaan (`company_id IS NOT NULL`) dan modifikasi reviewer manusia yang sudah ada.
- Memperbarui deskripsi kode HS resmi dan menandai tarif/lartas yang belum terverifikasi secara jujur (`NULL` / `unknown`).

### Verifikasi Lengkap Kandidat

```bash
.venv/bin/python -m pytest -p no:cacheprovider tests/test_acceptance_protected.py tests/test_audit_api_regressions.py tests/test_audit_acceptance_v2.py tests/test_review_normalization.py tests/test_detail_readiness.py tests/test_reference_data_acceptance.py tests/test_reference_import_integration.py -q && .venv/bin/ruff check src scripts tests && /srv/apps/hermes/.local/bin/npm --prefix frontend run build
```

Sebelum deployment jalankan migrasi, build frontend, verifikasi kandidat dan restart hanya layanan ImporJaga. Backup sebelum remediasi tersedia di direktori backup VPS operator. Bukti audit awal dan perbaikan fixture dipertahankan di docs/.
