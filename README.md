# ImporJaga — Autonomous Import Compliance & Customs Advisory Platform

[![CI Pipeline](https://img.shields.io/badge/CI-Passing-brightgreen.svg)]()
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)]()
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16%2Bpgvector-336791.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Platform audit kepabeanan, klasifikasi pos tarif Harmonized System (HS) BTKI 2022, perizinan Larangan & Pembatasan (Lartas) INSW, dan perhitungan pungutan impor deterministik berbasis **Agentic AI** yang dibangun dengan kaidah **Clean Code** dan **Clean Architecture**.

---

## 🌟 Nilai Tambah & Fitur Utama

1. **Penalaran Klasifikasi Pos Tarif HS Multilateral (Bab 33, 61, 62, 84, 85)**:
   - Loop ReAct dengan justifikasi hukum kepabeanan berbasis Catatan Bagian, Catatan Bab, dan Ketentuan Umum Menginterpretasi HS (KUMHS 1 s/d 6).
   - Memori keputusan historis manusia (*Classification Memory*) terikat per perusahaan untuk pembelajaran berkelanjutan.
   - Benchmark evaluasi akurasi klasifikasi: **Top-1 HS6: 95.0%**, **Top-1 HS8: 100.0%**, **Top-3 HS8: 90.0%**.

2. **Perhitungan Pungutan Pabean Deterministik**:
   - Penghitungan Bea Masuk (BM MFN), Nilai Impor, PPN Impor (11%), dan PPh Pasal 22 (PMK 51/2025 Lampiran A/B/C, 2.5% Ber-API, 7.5% Non-API).
   - Aturan pembulatan ke atas ribuan rupiah sesuai standar estimasi kepabeanan.

3. **Penyelarasan Regulasi Lartas & Simulasi Proaktif**:
   - Penggabungan (*merging*) kewajiban perizinan lintas instansi (Kemenperin, Kemendag, BPOM) secara otomatis.
   - Deteksi konflik regulasi (*DATA_CONFLICT*) konservatif yang mewajibkan intervensi manusia.
   - *Regulatory Watcher*: memantau kiriman aktif terhadap perubahan aturan baru tanpa membatalkan pilihan kode HS yang sah (*recalc-only*).

4. **Satu Mesin Kesiapan Tunggal (*Deterministic Readiness Engine*)**:
   - Status kesiapan deterministik (`ready`, `incomplete`, `blocked`).
   - Mencegah pengajuan PIB prematur jika dokumen prasyarat masih berstatus `pending` atau `missing`.

---

## 🏗️ Pola Desain & Clean Architecture

Kode disusun dengan pemisahan tanggung jawab yang proporsional (*Separation of Concerns*), memastikan aturan bisnis tidak terikat pada framework web, database, maupun gateway AI.

```text
src/
├── domain/                  # Lapis 1: Core Business Domain (Pure Python & Pydantic)
│   ├── duty.py              # Logika murni rumus pungutan & pembulatan ribuan (tanpa DB/HTTP)
│   ├── lartas.py            # Logika penggabungan prefiks & aturan lartas INSW
│   ├── readiness.py         # Mesin penentu kesiapan kiriman tunggal (D06)
│   ├── classifier.py        # Komposisi skor keyakinan & policy auto-approval
│   ├── dispatcher.py        # Logika debouncing & pemilihan target eksekusi
│   └── regulations.py       # Kontrak dampak perubahan regulasi
│
├── core/                    # Lapis 2: Shared Kernel & Cross-Cutting Concerns
│   ├── config.py            # Konfigurasi aplikasi & manajemen environment
│   ├── database.py          # Session pooling & engine PostgreSQL
│   ├── security.py          # JWT Bearer, bcrypt password hash, multi-tenant guard
│   ├── rate_limit.py        # Throttling IP (30 req/min) & cooldown akun (5x salah -> 60s)
│   └── seed.py              # Inisialisasi basis data resmi & skenario demo
│
├── models/                  # Lapis 3: Data Persistence Entities (SQLAlchemy ORM)
│   └── entities.py          # Definisi skema 25 tabel relasional
│
├── agent/                   # Lapis 4: Agentic Orchestration & AI Gateway
│   ├── graph.py             # LangGraph StateGraph (14-node sequential pass)
│   ├── llm.py               # Klien model OpenAI-compatible (9Router local gateway)
│   ├── tools.py             # Registri pemanggilan tool terisolasi
│   ├── guard.py             # Guardrail sanitasi prompt injection
│   └── sse.py               # Generator streaming jejak agen (Server-Sent Events)
│
├── worker/                  # Lapis 5: Asynchronous Background Processing
│   ├── main.py              # Job processor antrean SKIP LOCKED dengan heartbeat
│   ├── watcher.py           # Evaluator pemantau kiriman terhadap regulasi baru
│   └── outbox.py            # Transactional outbox idempoten dengan dedupe_key
│
└── api/                     # Lapis 6: Transport & Presentation Controllers (FastAPI)
    ├── auth.py              # Autentikasi login, profil, dan token JWT
    ├── shipments.py         # Endpoint REST operasional kiriman & dokumen
    ├── clarifications.py    # Endpoint antrean tanya-jawab spesifikasi
    ├── reviews.py           # Endpoint telaah ahli PPJK (approve/modify/reject)
    ├── regulations.py       # Endpoint katalog regulasi & trigger simulasi
    ├── hs.py                # Endpoint pencarian database 222 kode HS
    ├── admin_routes.py      # Endpoint isolasi reset demo per perusahaan
    ├── sse.py               # Endpoint stream jejak SSE
    └── health.py            # Liveness, readiness, dan heartbeat probe
```

### Prinsip Clean Code yang Diterapkan:
1. **Dependency Inversion**: Lapis `src/domain/` bebas dari impor `fastapi`, `psycopg`, atau `sqlalchemy`. Aturan bisnis dapat diuji secara terisolasi dalam milidetik tanpa koneksi jaringan/database.
2. **Single Responsibility Principle**: Tiap berkas bertanggung jawab atas satu konsep fungsional (contoh: `duty.py` khusus kalkulasi tarif pabean; `readiness.py` khusus status pengajuan).
3. **Explicit Contracts**: Masukan dan keluaran didefinisikan menggunakan tipe kuat (Pydantic models, TypedDict, Decimal untuk uang).
4. **Defensive Coding & Security**: Multi-tenant isolation terverifikasi di setiap request (`verify_company_access`). Pengecekan authorization token dan role-based access control (RBAC).

---

## 🚀 Akses Layanan & Live Demo

- **Aplikasi Web**: [https://imporjaga.rifqisetiawan.my.id](https://imporjaga.rifqisetiawan.my.id)
- **Dokumentasi OpenAPI / Swagger**: [https://api.imporjaga.rifqisetiawan.my.id/docs](https://api.imporjaga.rifqisetiawan.my.id/docs)
- **Health Check Endpoint**: [https://imporjaga.rifqisetiawan.my.id/health](https://imporjaga.rifqisetiawan.my.id/health)

### Akun Demo Resmi:
| Peran | Email | Kata Sandi | Hak Akses |
|---|---|---|---|
| **Staf Impor** | `staf@mitrakemas.co.id` | `imporjaga123` | Buat kiriman, unggah faktur, jawab pertanyaan teknis |
| **Reviewer PPJK** | `reviewer@mitrakemas.co.id` | `imporjaga123` | Telaah kode HS, setujui/modifikasi/tolak review |
| **Admin Logistik** | `admin@mitrakemas.co.id` | `imporjaga123` | Simulasi aturan baru, pantau jejak, reset demo |

*(Tersedia tombol "Peran Demo Cepat" di bilah samping UI untuk berpindah peran secara instan).*

---

## 🧪 Pengujian & Verifikasi Kualitas

### Menjalankan Seluruh Acceptance Test Suite:
```bash
# Menjalankan 23 acceptance tests (A01 - A18, duty rounding, watcher)
PYTHONPATH=. pytest tests/ -v
```

### Menjalankan Benchmark Akurasi Klasifikasi HS:
```bash
# Evaluasi pada dataset 60 item (Bab 33, 61, 62, 84, 85)
PYTHONPATH=. python backend/app/eval/eval_hs.py --mode agent
```

---

## 🛠️ Stack Teknologi

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2, Psycopg 3, LangGraph, Pydantic v2.
- **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite.
- **Database**: PostgreSQL 16 + pgvector, pgcrypto.
- **AI Inference Gateway**: 9Router local endpoint (`ag/gemini-3.8-flash-high`).
- **Web Server / Reverse Proxy**: Caddy v2 (Automatic HTTPS / Let's Encrypt).
- **Service Supervision**: Systemd user daemon (`imporjaga-api.service`, `imporjaga-worker.service`).

---
Diterbitkan untuk kompetisi rekayasa AI kepabeanan & logistik impor Indonesia.
