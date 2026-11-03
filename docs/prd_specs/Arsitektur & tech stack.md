# Arsitektur dan tech stack

## Keputusan tech stack

Stack dipilih supaya bisa dibangun dua orang dalam sembilan hari, memakai VPS yang sudah ada, dan mudah dijelaskan di bagian arsitektur proposal (bobot 15%).

| Lapisan | Pilihan | Alasan |
| --- | --- | --- |
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui | Cepat dibuat, komponen siap pakai, gratis di-deploy ke Vercel |
| State dan data fetching | TanStack Query, react-hook-form, zod | Cache dan refetch otomatis, validasi form sama dengan skema API |
| Live update | Server-Sent Events (EventSource bawaan browser) | Satu arah dari server ke browser sudah cukup untuk jejak agent, lebih sederhana dari WebSocket |
| Backend API | Python 3.12 + FastAPI + Pydantic v2 | Ekosistem AI paling lengkap, dokumentasi OpenAPI otomatis di `/docs` |
| ORM dan migrasi | SQLAlchemy 2 + Alembic | Skema tercatat di migrasi, mudah direset untuk demo |
| Kerangka agent | LangGraph + paket checkpoint Postgres | Alur berupa graph dengan cabang, jeda untuk pertanyaan balik (interrupt), dan state yang tersimpan di database |
| Klien LLM | OpenAI Python SDK yang diarahkan ke 9Router (endpoint kompatibel OpenAI) | Satu klien untuk semua provider, ganti model cukup lewat env |
| Model LLM | Model utama dengan tool calling dan structured output yang andal, plus model cadangan dari provider berbeda | Cadangan mencegah demo gagal saat rate limit |
| Embedding | `intfloat/multilingual-e5-base` (768 dimensi) dijalankan lokal dengan sentence-transformers | Gratis, mendukung bahasa Indonesia, tidak tergantung API luar |
| Database | PostgreSQL 16 + ekstensi pgvector | Satu database untuk data relasional, pencarian vektor, full-text search, dan checkpoint agent |
| Ekstraksi dokumen | pdfplumber untuk PDF berteks, PyMuPDF untuk mengubah halaman jadi gambar, lalu model vision untuk scan dan foto | Tidak perlu memasang OCR terpisah |
| Antrean dan penjadwal | Tabel `jobs` di Postgres (`SELECT ... FOR UPDATE SKIP LOCKED`) + APScheduler di proses worker | Tanpa Redis atau Celery, komponen lebih sedikit |
| Retry | tenacity | Backoff eksponensial untuk LLM dan tool |
| Auth | JWT (PyJWT) + bcrypt | Sederhana, cukup untuk tiga peran |
| Rate limit | slowapi | Melindungi login dan endpoint analisis |
| Log | structlog (JSON) | Mudah dicari saat debugging di VPS |
| Infrastruktur | Docker Compose di VPS Tencent yang sudah ada, Caddy untuk HTTPS otomatis, domain `.my.id` | Memakai server yang sudah dibayar, HTTPS gratis dari Let's Encrypt |
| Pengujian | pytest (backend), Playwright (end-to-end), skrip evaluasi akurasi HS | Bukti kualitas untuk juri dan dokumentasi |
| CI | GitHub Actions: lint, test, build | Riwayat commit dan badge CI menambah kesan rapi di repo |

**Kenapa tidak memakai Hermes atau n8n:** juri secara eksplisit meminta nilai tambah buatan tim terlihat jelas. Graph LangGraph yang kita tulis sendiri membuat alur, jeda, dan pemulihan error terlihat di kode dan mudah digambar di proposal. 9Router tetap dipakai sebagai gateway model.

## Diagram arsitektur

Browser hanya berkomunikasi dengan API. API tidak menjalankan agent secara langsung, melainkan menaruh pekerjaan di tabel `jobs`. Worker mengambil pekerjaan itu, menjalankan graph agent, dan menulis setiap langkah ke tabel `agent_steps`. API membaca tabel itu dan mengirimkannya ke browser lewat SSE.

&#91;embedded content: arsitektur sistem · 9 komponen\]

Kenapa API dan worker dipisah: analisis bisa makan waktu 1 sampai 2 menit. Kalau dijalankan di dalam request HTTP, request bisa timeout dan agent ikut mati. Dengan worker terpisah, analisis tetap jalan walau browser ditutup, dan juri bisa membuka ulang halaman untuk melihat hasilnya.

| Komponen | Tugas | Port internal |
| --- | --- | --- |
| Frontend (Vercel) | Semua halaman UI, memanggil API dengan token Bearer | - |
| Caddy | Terminasi HTTPS untuk `api.<domain>`, meneruskan ke API | 80, 443 |
| API (FastAPI, uvicorn) | Auth, CRUD, unggah file, membuat job, SSE jejak agent | 8000 |
| Worker | Mengambil job, menjalankan graph agent, menjalankan jadwal harian (pemantau aturan pukul 07.00 WIB, reset demo pukul 00.00 WIB) | - |
| PostgreSQL + pgvector | Semua data, indeks vektor, checkpoint LangGraph, antrean job | 5432, tidak dibuka ke publik |
| Volume uploads | Menyimpan file dokumen, di-mount ke API dan worker | - |
| Model embedding | Dimuat di dalam proses API dan worker (sentence-transformers), bukan container terpisah | - |
| Gateway LLM (9Router) | Endpoint kompatibel OpenAI ke provider utama dan cadangan | Sesuai konfigurasi 9Router yang sudah berjalan |

## Struktur repositori

Satu repo publik (monorepo) dengan folder terpisah, sesuai saran panitia agar juri tidak berpindah-pindah repo. Nama repo yang disarankan: `imporjaga`.

```
imporjaga/
├── README.md                  # deskripsi, fitur, arsitektur, cara menjalankan, akun demo, link live
├── .env.example               # daftar nama env tanpa nilai
├── .gitignore                 # wajib berisi .env, data/uploads, data/raw, __pycache__, node_modules
├── docs/
│   ├── architecture.png
│   ├── agent-graph.png
│   └── erd.png
├── infra/
│   ├── docker-compose.yml
│   ├── Caddyfile
│   └── backup.sh
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/       # migrasi
│   ├── app/
│   │   ├── main.py             # membuat FastAPI app, middleware, router
│   │   ├── core/               # config.py, security.py, logging.py, errors.py
│   │   ├── db/                 # session.py, models.py
│   │   ├── schemas/            # Pydantic request/response per resource
│   │   ├── api/v1/             # auth.py, shipments.py, documents.py, items.py, runs.py,
│   │   │                       # clarifications.py, reviews.py, regulations.py, hs.py,
│   │   │                       # notifications.py, dashboard.py, admin.py
│   │   ├── services/           # duty.py, risk.py, checklist.py, lartas.py, hs_search.py,
│   │   │                       # pib.py, storage.py, notify.py, masking.py, embeddings.py
│   │   ├── agent/
│   │   │   ├── graph.py        # graph analisis kiriman
│   │   │   ├── watcher.py      # graph pemantau aturan
│   │   │   ├── state.py        # TypedDict state
│   │   │   ├── nodes/          # satu file per node
│   │   │   ├── tools/          # satu file per tool + registry
│   │   │   ├── prompts/        # file .md prompt sistem
│   │   │   ├── llm.py          # klien LLM, fallback, retry
│   │   │   └── trace.py        # menulis agent_steps
│   │   ├── worker/
│   │   │   ├── main.py         # loop job + APScheduler
│   │   │   └── jobs.py
│   │   ├── scripts/            # dijalankan dengan python -m app.scripts.<nama>
│   │   │   ├── extract_btki.py
│   │   │   ├── validate_seed.py
│   │   │   ├── ingest.py       # semua CSV di data/seed + embedding
│   │   │   ├── seed_demo.py    # akun, perusahaan, kiriman, memori demo (juga dipakai reset)
│   │   │   └── make_sample_invoices.py
│   │   └── eval/
│   │       └── eval_hs.py      # evaluasi akurasi pada set uji
│   └── tests/                  # test_duty.py, test_risk.py, test_api_*.py, test_agent_tools.py,
│                               # test_watcher_scenario.py
├── frontend/
│   ├── package.json
│   ├── src/app/                # halaman (lihat tab Frontend)
│   ├── src/components/         # ui/ (shadcn), agent/, shipment/, review/, common/
│   ├── src/lib/                # api.ts, auth.ts, sse.ts, format.ts, schemas.ts
│   ├── src/types/api.ts        # hasil generate dari OpenAPI
│   └── e2e/                    # tes Playwright
├── data/                       # di-mount ke /app/data di container api dan worker
│   ├── raw/                    # PDF BTKI asli, tidak di-commit
│   ├── seed/                   # hs_codes.csv, hs_notes.csv, regulations.csv, lartas_rules.csv,
│   │                           # pph22_lampiran.csv, exchange_rates.csv
│   ├── demo/invoices/          # invoice dan packing list contoh
│   └── eval/eval_hs.csv        # set uji 60 barang
└── .github/workflows/ci.yml
```

Aturan commit: pakai format `tipe: deskripsi` (`feat`, `fix`, `docs`, `test`, `chore`, `refactor`). Contoh: `feat: tambah node klasifikasi HS dengan validasi kode`. Riwayat commit dilihat juri sebagai bukti progres.

## Variabel environment

Nilai asli disimpan di file `.env` di VPS dan di pengaturan Vercel. Repo hanya berisi `.env.example` dengan nama variabel.

| Nama | Dipakai oleh | Contoh nilai | Keterangan |
| --- | --- | --- | --- |
| `APP_ENV` | API, worker | `production` | `development` atau `production` |
| `DATABASE_URL` | API, worker | `postgresql+psycopg://imporjaga:***@db:5432/imporjaga` | Koneksi SQLAlchemy |
| `JWT_SECRET` | API | 64 karakter acak | Buat dengan `openssl rand -hex 32` |
| `JWT_EXPIRES_HOURS` | API | `12` | Masa berlaku token |
| `CORS_ORIGINS` | API | `https://imporjaga.vercel.app` | Dipisah koma |
| `UPLOAD_DIR` | API, worker | `/data/uploads` | Path volume |
| `MAX_UPLOAD_MB` | API | `10` | Batas ukuran file |
| `LLM_BASE_URL` | Worker, API | `https://<host-9router>/v1` | Endpoint kompatibel OpenAI |
| `LLM_API_KEY` | Worker, API | rahasia | Kunci ke 9Router |
| `LLM_MODEL_PRIMARY` | Worker | nama model di 9Router | Model utama untuk klasifikasi |
| `LLM_MODEL_FALLBACK` | Worker | nama model di 9Router | Model cadangan dari provider berbeda |
| `LLM_MODEL_VISION` | Worker | nama model di 9Router | Untuk dokumen hasil scan dan foto |
| `LLM_TIMEOUT_SECONDS` | Worker | `45` | Timeout per panggilan |
| `EMBEDDING_MODEL` | API, worker | `intfloat/multilingual-e5-base` | Dimensi 768 |
| `CONFIDENCE_REVIEW_THRESHOLD` | Worker | `0.70` | Di bawah ini risiko tinggi |
| `CONFIDENCE_MEDIUM_THRESHOLD` | Worker | `0.85` | Di bawah ini risiko sedang |
| `WATCHER_CRON` | Worker | `0 7 * * *` | Jadwal pemantau aturan (zona waktu Asia/Jakarta) |
| `DEMO_RESET_CRON` | Worker | `0 0 * * *` | Jadwal reset data demo |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Worker | opsional | Wajib untuk email agent ke pemasok (P0) dan notifikasi email. Untuk demo pakai Gmail khusus agent dengan app password (smtp.gmail.com, port 587) |
| `NEXT_PUBLIC_API_URL` | Frontend | `https://api.imporjaga.my.id/api/v1` | Diset di Vercel |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Container db | rahasia | Untuk image `pgvector/pgvector:pg16` |
| `LLM_DAILY_TOKEN_BUDGET` | API, worker | `2000000` | Batas token per hari untuk semua run, melindungi kunci API karena akun demo publik |
| `LLM_MODE` | API, worker, tes | `live` | live atau fake. fake membaca respons berskrip untuk tes, ditolak di production |
| `IMAP_HOST, IMAP_USER, IMAP_PASSWORD` | Worker | `imap.gmail.com` | Inbox agent (P1). Kosongkan untuk mematikan pemeriksaan inbox |
| `INBOX_POLL_SECONDS` | Worker | `60` | Jeda pemeriksaan inbox |
| `FOLLOWUP_DELAY_MINUTES` | Worker | `3` | Khusus demo: memaksa semua jadwal tindak lanjut menjadi sekian menit. Kosongkan agar memakai jeda pilihan agent |
| `AGENT_EMAIL_DAILY_LIMIT` | Worker | `20` | Batas email keluar dari agent per hari |
| `AGENT_EMAIL_ALLOWED_DOMAINS` | Worker | `gmail.com` | Daftar domain tujuan yang diizinkan, dipisah koma. Untuk demo, hanya domain inbox milik tim |

Nama domain di atas hanya contoh. Ganti dengan domain yang benar-benar kalian beli.
