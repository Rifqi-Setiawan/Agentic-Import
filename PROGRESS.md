# ImporJaga remediation

Audit baseline801ffab: docs/AUDIT-2026-11-04.md. Native task t_1bf95ae7 berhenti setelah dua timeout; riwayat dipertahankan, tidak direset atau dinyatakan PASS. Parent Codex melanjutkan integrasi secara langsung.

- Frontend modular dengan create/upload dan data API aktual, jejak SSE dan bukti per item.
- Pipeline operasional melalui9Router, ekstraksi PDF, tool-call HS, validasi kutipan, perhitungan dari DB, checklist dan review.
- Otorisasi/PIB tenant, validasiHS/upload, worker durable, SMTPsandbox lokal dan heartbeat diperbaiki.
- 42 core/regression/audit-v2 checks pass pada perubahan gabungan.
- 2026-11-04: Katalog resmi BTKI 2022 (2.614 kode HS), perpustakaan regulasi JDIH (5 PMK), demo fixtures (14 pengiriman, 28 item, 41 dokumen PDF watermarked DEMO), dan CLI importer aditif selesai. Verifikasi: 49 tests pass, ruff clean, frontend build pass.
- 2026-11-04: Pengarsipan aturan placeholder lartas global warisan (`company_id IS NULL`), tautan starter dokumen fiktif baru (`INV-DEMO-MKN-001.pdf`), asersi integrasi test DB, dan panduan operator selesai. Verifikasi: 49 tests pass, ruff clean, frontend build pass.
- 2026-11-04: Guard isolasi test DB sesi penuh (`tests/conftest.py`), perbaikan ranking retrieval leksikal leaf-weighted + IDF + sinonim teknis di `src/services/analysis.py`, deduplikasi kanonikal & isolasi tenant di `/api/v1/hs-codes/search` & `/hs-codes/{code}` di `src/api/hs.py`, serta tampilan 5 referensi regulasi publik & label status di UI `WorkQueue.tsx` selesai. Verifikasi: 52 tests pass (49 dilindungi + 3 regresi), ruff clean, frontend build pass. Smoke live case 1 sensor PASS (85365099), case 2 ditangani oleh eksekusi persisten operator Parent.
- Smoke live case 2, review kandidat, deploy dan push menunggu verifikasi akhir. Jangan menyimpulkan release-ready dari status ini.

## Berikutnya
1. Penyelesaian smoke live case 2 oleh sesi persisten Parent.
2. Review kandidat komit.
3. Parent live backup dan production apply via CLI importer (--live --apply).
