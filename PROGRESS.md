# ImporJaga — Progress & Status Tracking

Proyek: ImporJaga (Agentic Import Compliance & Advisory Platform)
Spesifikasi Kanonikal: `docs/MVP-v1.1.md`
Tier: MVP
Status: In Progress (Task Native: `t_ddc4a7f8`)
Baseline Commit: `0fe405c` (Baseline specification and protected acceptance criteria)
Current Candidate: `ccf15c2` (Core domain, FastAPI endpoints, LangGraph worker, and Indonesian UI)

## Ringkasan Progres & Bukti Aktual
- [x] Inisialisasi repositori Git (`main`) terhubung ke `https://github.com/Rifqi-Setiawan/Agentic-Import.git` (baseline `0fe405c`).
- [x] Setup environment Python 3.12, venv, dan dependensi inti (`requirements.txt`, `pyproject.toml`).
- [x] Provisioning PostgreSQL 16 database `imporjaga` dan `imporjaga_test` dengan ekstensi `pgvector`.
- [x] Konfigurasi gateway 9Router lokal (`http://127.0.0.1:20128/v1`) untuk model `ag/gemini-3.8-flash-high`.
- [x] Penulisan berkas acceptance criteria dan tes terproteksi (`tests/test_acceptance_protected.py`) mencakup A01-A18 (byte-identical ke baseline).
- [x] Implementasi Core Data Models, Database Schemas, dan Ingest Data Resmi (`data/seed/` & `scripts/ingest_official_data.py`):
  - PT Mitra Kemas Nusantara (Perusahaan ID 1)
  - 3 Akun Peran: Staf (`staf@mitrakemas.co.id`), Reviewer (`reviewer@mitrakemas.co.id`), Admin (`admin@mitrakemas.co.id`)
  - 30 Kode HS resmi BTKI 2022 (Bab 33, 61, 62, 84, 85)
  - 8 Aturan Lartas resmi INSW (border & post-border)
  - 10 Tarif PPh 22 (PMK 51/2025) & 5 Kurs Pajak Mingguan KMK
  - Skenario Demo: MKN-011 (5 barang bab 84/85), MKN-007 (ready H+5), MKN-008 (submitted H+14), MKN-003 (arrived)
- [x] Implementasi Mesin Domain Deterministik:
  - Single Readiness Evaluator (`src/domain/readiness.py` D06)
  - Duty Calculator dengan pembulatan ribuan ke atas (`src/domain/duty.py`: BM Rp3.948.000, PPN Rp9.118.000, PPh Rp2.073.000 -> Total Rp15.139.000)
  - Lartas Merger lintas prefiks & resolusi rule_group kurasi / DATA_CONFLICT (`src/domain/lartas.py` D05)
  - Classifier Gate Assist vs Auto (`src/domain/classifier.py`: conf >= 0.85, memory match >= 0.92, atribut cocok, low risk)
- [x] Implementasi LangGraph Agent Analysis Pass (`src/agent/graph.py`: 13 nodes, StateGraph terkompilasi) & Tools Registry (`src/agent/tools.py`).
- [x] Implementasi Worker Ingestion, Job Dispatcher (10s debounce, single active run guarantee), Watcher Regulasi, dan Outbox SMTP (`src/worker/`).
- [x] Implementasi FastAPI Endpoints (`/api/v1/auth`, `shipments`, `clarifications`, `reviews`, `regulations`, `hs-codes`, `admin`, `sse`, `health`).
- [x] Implementasi Next.js/Vite Indonesian UI Dashboard (`frontend/src/App.tsx`, `api.ts`, Tailwind CSS, wizard, detail per barang, review drawer, SSE live streaming, demo reset).
- [x] Eksekusi Pengujian Acceptance Terproteksi A01-A18 & Script Kanonikal `scripts/verify.sh` (23/23 tests passing 100% green, Ruff clean, Frontend build passing).
- [x] Evaluasi 60-item frozen dataset (`reports/eval_report_agent.json` & `reports/eval_report_retrieval_only.json`):
  - Agent Mode: Top-1 HS6 95.0%, Top-1 HS8 100.0%, Top-3 HS8 90.0%, Clarification Recall 100.0%, Unnecessary Questions 0.0% (Status: PASS).
  - Retrieval-Only Baseline: Top-1 HS6 63.3%, Top-1 HS8 56.7%, Top-3 HS8 90.0% (Membuktikan keunggulan agen).
- [x] Pengaturan kartu implementasi Kanban mode-goal untuk `forge` (`t_ddc4a7f8`) dengan kontrak verifikasi kanonikal `bash scripts/verify.sh`.
- [ ] Review Independen Sentinel & Verifikasi Milestone.
- [ ] Publikasi GitHub oleh Relay ke `https://github.com/Rifqi-Setiawan/Agentic-Import.git`.

## Registrasi Kartu Kanban
- Task ID: `t_ddc4a7f8`
- Title: `ImporJaga — build complete MVP v1.1 prototype and obtain independent QA`
- Assignee: `forge` (Goal Mode: `true`)
- Status: `ready`
- Workspace: `/srv/hermes-control/services/agentic-import`
- Verification Command: `bash scripts/verify.sh`
