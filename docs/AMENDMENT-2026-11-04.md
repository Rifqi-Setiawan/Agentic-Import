# Normative Amendment: Corrected Audit Acceptance Contract v1.2 (F01–F14)

- **Date**: 2026-11-04 WIB
- **Author**: Jarvis (VPS Chief Orchestrator / Author of Acceptance Suite)
- **Role**: Test Suite Author & Acceptance Authority
- **Target Task**: `t_1bf95ae7` (Implementer: `@forge`, Reviewer: `@sentinel`)
- **Reference**: `docs/AUDIT-2026-11-04.md`, `docs/PARENT-QA-NOTES.md`, `docs/INDEPENDENT-QA-SUITE-REVIEW.md`, `tests/test_audit_api_regressions.py`
- **Original Pinned Suite**: `tests/test_audit_acceptance.py` (SHA256: `6baeaf5ae759c05937a0138b103b8e376dceddb847c2402f92116cb265a2373e`)

---

## 1. Rationale & Defect Provenance

An independent review documented in `docs/INDEPENDENT-QA-SUITE-REVIEW.md` and parent notes identified intrinsic fixture flaws in the initial protected acceptance suite `tests/test_audit_acceptance.py` (v1.1). Under the Clean Architecture, Clean Code, and Sentinel Native QA Feedback standards, test defects must be resolved by the test author through contract-safe provenance. Implementers (`@forge`) are strictly forbidden from weakening application code or security checks to satisfy invalid test fixtures.

The original file `tests/test_audit_acceptance.py` and its hash `6baeaf5ae759c05937a0138b103b8e376dceddb847c2402f92116cb265a2373e` are preserved intact in source control for historical audit and failure evidence. This amendment provides the normative specification and corrected acceptance suite `tests/test_audit_acceptance_v2.py`.

---

## 2. Intrinsic Fixture Defects & Normative Corrections

### Defect 1: F03 Flush vs Commit on Foreign Shipment Fixture
- **Issue**: In `test_f03_pib_multi_tenant_isolation`, the fixture only calls `flush()` on Company 2's shipment `s2` without committing. The FastAPI `TestClient` executes queries on a separate database connection/session under PostgreSQL's Read Committed isolation level, which cannot see uncommitted data from `test_db_session`. Consequently, the API returns `404 Not Found` because the shipment does not exist on that connection, producing a false-positive pass regardless of tenancy isolation logic. Additionally, there is no positive control verifying that Company 1 can access its own shipment.
- **Correction**: Commit all test fixtures (`c1`, `c2`, `s1`, `s2`) so they are visible to the application's connection. Perform a positive control test verifying that Company 1 staff successfully accesses Company 1's shipment (HTTP 200), followed by asserting that Company 1 staff receives HTTP 404 (or 403) when attempting to access Company 2's shipment.

### Defect 2: Security & Authentication Token Fixtures (F04, F03, F10)
- **Issue**: The `create_test_token` helper generated synthetic tokens with user IDs (e.g. 801, 802, 803) that were never persisted in the `users` table. When standard, robust active-user database authentication is implemented, requests return `401 Unauthorized` instead of the expected `403 Forbidden` on role-restricted endpoints.
- **Correction**: Test fixtures must persist authentic, active `User` records in the test database (`imporjaga_test`) before generating access tokens:
  - `importer_staff` user (role: `importer_staff`, active: True)
  - `ppjk_reviewer` user (role: `ppjk_reviewer`, active: True)
  - `admin` user (role: `admin`, active: True)
  Tests then verify that authenticated staff receives HTTP 403 on reviewer/admin actions, while authorized roles succeed (positive control).

### Defect 3: Database Isolation & SessionLocal Production-Leak Risk (F14)
- **Issue**: `setup_test_database` monkeypatched `settings.DATABASE_URL = db_url`, but `src.core.database.engine` and `src.core.database.SessionLocal` are instantiated at module import time. Reassigning `settings.DATABASE_URL` does not rebind already imported SQLAlchemy engines or session factories. Ingestion scripts, seed functions, or endpoints using `SessionLocal` risk connecting to the production `imporjaga` database.
- **Correction**: Enforce absolute database isolation:
  - Assert `settings.TEST_DATABASE_URL` database name strictly equals `imporjaga_test`.
  - Override FastAPI's database dependencies (`get_db` and `get_db_cursor`) to bind exclusively to the test database engine and test database connection.
  - Assert `SELECT current_database()` returns `imporjaga_test` across all test database sessions.
  - Fail immediately before any write operation if the connected database is not `imporjaga_test`.

### Defect 4: F09 Duplicate Unique Key Violation
- **Issue**: `test_f09_tenant_isolated_demo_reset` created two shipments for two different companies with the identical `shipment_number="MKN-011"`. In schemas with a global unique constraint on `shipment_number`, this triggers a database `UniqueConstraintViolation` during fixture setup prior to running the reset logic.
- **Correction**: Use distinct shipment numbers (`MKN-C1-011` and `MKN-C2-011`) for the two tenant companies. Assert that resetting Company 2 purges Company 2 records while Company 1 records remain 100% intact.

### Defect 5: F01 Elevate from AST-Only to Real Pipeline Execution
- **Issue**: Original F01 only inspected source code AST via `inspect.getsource(graph)`. This does not prove that the real vertical pipeline actually functions end-to-end.
- **Correction**: Test F01 requires genuine end-to-end pipeline execution:
  - Text extraction from input document / PDF.
  - Item persistence into database.
  - Lexical and semantic retrieval from BTKI 2022 dataset.
  - Real LLM call to 9Router (`gemini-3.8-flash-n`) with explicit `stream: false`, returning authentic JSON and non-zero prompt/completion token usage.
  - Duty and tariff calculation with exact mathematical formulas.
  - Dynamic SSE progress steps with measured token counts and costs.

---

## 3. Supplemental 8 HTTP Regression Suite

- Suite: `tests/test_audit_api_regressions.py`
- All 8 black-box regression tests authored by independent parent QA must pass.
- Safety: These tests forbid real database connections (`psycopg.connect` and `Engine.connect` raise `AssertionError`) and use `ScenarioCursor`.
- Adaptation note: The `ScenarioCursor` fixture adapter in `test_audit_api_regressions.py` may independently adapt if repositories or SQL queries are refactored, provided the external HTTP response contracts (404 foreign, 403 staff, 409 unapproved, 400/422 bad HS, 400/415 non-PDF) remain strictly preserved.

---

## 4. Live Gateway & Infrastructure Parameters

1. **9Router LLM Gateway**:
   - Model: `ag/gemini-3.8-flash-high` (routed to `gemini-3.8-flash-n`).
   - Request requirement: Must explicitly pass `"stream": false` in JSON payloads. Live testing confirmed that omitting `stream` may return chunked non-JSON data, whereas `stream: false` consistently returns standard OpenAI-compatible JSON with real `usage` metrics.
2. **PostgreSQL Test Database**:
   - URL: `settings.TEST_DATABASE_URL` (`postgresql://imporjaga_user:...@localhost:5432/imporjaga_test`).
   - Sudo inside worker is forbidden.
3. **Outbox SMTP Delivery**:
   - Localhost sandbox labeled `demo` is used for email delivery.
   - If SMTP is unreachable or fails, outbox status must transition to `draft`, `failed`, or `unknown`.
   - Outbox messages must NEVER be marked `sent` without verified network transmission.

---

## 5. Artifact Summary

1. `docs/INDEPENDENT-QA-SUITE-REVIEW.md` — Detailed review of contract defects.
2. `docs/PARENT-QA-NOTES.md` — Independent parent QA notes.
3. `tests/test_audit_acceptance.py` — Original v1.1 suite (SHA: `6baeaf5ae759c05937a0138b103b8e376dceddb847c2402f92116cb265a2373e`), preserved for history.
4. `tests/test_audit_acceptance_v2.py` — Corrected v1.2 acceptance suite with clean fixtures and authentic E2E pipeline verification.
5. `tests/test_audit_api_regressions.py` — Protected HTTP regression suite (SHA: `1ded4ca7f1788c7f4f82ab4eff597ca85d7136a9f25b84b22c776c7c81eabe7d`).
