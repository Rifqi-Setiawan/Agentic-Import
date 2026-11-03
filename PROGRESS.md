# ImporJaga — Progress & Status Tracking

Proyek: ImporJaga (Agentic Import Compliance & Advisory Platform)
Spesifikasi Kanonikal: `docs/MVP-v1.1.md`
Tier: MVP
Status: In Progress

## Ringkasan Progres
- [x] Inisialisasi repositori Git (`main`) terhubung ke `https://github.com/Rifqi-Setiawan/Agentic-Import.git`
- [x] Setup environment Python 3.12, venv, dan dependensi inti (`requirements.txt`)
- [x] Provisioning PostgreSQL 16 database `imporjaga` dan `imporjaga_test` dengan ekstensi `pgvector`
- [x] Konfigurasi gateway 9Router lokal (`http://127.0.0.1:20128/v1`) untuk model `ag/gemini-3.8-flash-high`
- [ ] Penulisan berkas acceptance criteria dan tes terproteksi (`tests/test_acceptance_protected.py`) mencakup A01-A18
- [ ] Implementasi Core Data Models, Database Schemas, dan Initial Seed (Perusahaan MKN, Pengguna, BTKI Bab 33/61/62/84/85, Lartas, Skenario MKN-011, MKN-007, MKN-008, MKN-003)
- [ ] Implementasi Mesin Domain Deterministik: Single Readiness Evaluator, Duty Calculator, Lartas Merger, Memory Matcher
- [ ] Implementasi LangGraph Agent Analysis Pass & Tools
- [ ] Implementasi Worker Ingestion, Job Dispatcher (10s debounce, single run guarantee), Watcher Regulasi, dan Outbox SMTP
- [ ] Implementasi FastAPI Endpoints (/api/v1/auth, shipments, items, clarifications, reviews, checklist, regulations, admin/demo, sse)
- [ ] Implementasi Next.js 15 Frontend UI (Bahasa Indonesia, Tailwind CSS, Wizard, Per-Item Clarification, Review Drawer, SSE Trace, Demo Reset)
- [ ] Eksekusi Pengujian Acceptance Terproteksi A01-A18 & Script Kanonikal `scripts/verify.sh`
- [ ] Review Independen Sentinel & Verifikasi Milestone
- [ ] Publikasi GitHub oleh Relay

## Berikutnya
1. Tulis acceptance test terproteksi `tests/test_acceptance_protected.py` mencakup seluruh skenario A01-A18.
2. Buat skrip kanonikal `scripts/verify.sh`.
3. Daftarkan tugas implementasi Forge via Kanban dalam mode goal (`goal_mode=True`).
