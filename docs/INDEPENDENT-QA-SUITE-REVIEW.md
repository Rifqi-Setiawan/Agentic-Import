# Independent review of native audit acceptance suite

Reviewed read-only: `/srv/hermes-control/services/agentic-import/tests/test_audit_acceptance.py`, 4 Nov 2026.
No protected test or implementation changed by this review.

## Contract defects and false-green risks

1. **F01 is structural, not pipeline acceptance** (lines 118–139). It checks a client function name exists and two literal strings are absent from graph.py. A no-op function and graph that still appends fixed text pass. Does not upload PDF, invoke gateway, persist items, assert input-dependent classifications, inspect tool sources, measure token usage, or run worker. Also original fixed token/cost lives worker/main.py, so search only graph.py misses the actual defect.
2. **Database isolation is incomplete** (57–60). Changing settings.DATABASE_URL does not rebind src.core.database.engine/SessionLocal already created at module import. Existing tests/test_api_integration.py imports app during collection, so seed/global ORM paths can remain production-bound even when request psycopg reads test DB. F14 proves one explicit test-URL connection, not every path used by app/worker/seed. Guard target DB parsed database name exactly, fail before writes on any non-test target, use DI/engine factory or override all session providers. Test DB URL substring `test` is insufficient: hostname/password can contain it while database is production. Do not run suite before binding corrected.
3. **F03 can pass for nonexistence** (179–193). Foreign company/shipment are only flush()'d, not committed. HTTP uses a separate connection that cannot see them, so 404 may pass without ownership check. Establish rows visible on endpoint connection; same-company 200 control required before foreign 404.
4. **Synthetic users conflict with proper auth** (193, 215–217, 278, 299, 443, 473). Tokens name user IDs never persisted. Fixing active-user verification correctly returns 401, which breaks tests expecting 403/200/409. Create real active users and login, then separately test revoked/nonexistent users ->401. F03 also uses legacy role `staf` rather than canonical importer_staff.
5. **F09 fixture violates baseline schema** (407–410). Two shipments share MKN-011 while Shipment.shipment_number currently globally unique. This fails before reset. Contract should either explicitly require migration to UNIQUE(company_id,shipment_number), or use distinct company-specific numbers and test general reset isolation. Do not weaken tenant test to keep broken fixture.
6. **F10 can pass from wrong request shape** (450). Sends action/suggested_hs while current DecisionRequest requires decision/modified_hs_code. A 422 missing decision passes without checking invalid HS. Use actual frontend/OpenAPI contract and verify valid modification succeeds, invalid format and unknown valid-format code both fail, no memory written.
7. **F04 role allow positive controls too weak** (236–242). `!=403` permits 401,422,500. Reviewer target 99999 is nonexistent; malformed action can produce 422. Create actual review and authenticated users; assert positive reviewer action succeeds, staff fails before write, admin valid simulation succeeds. Uncommitted company also invisible to endpoint.
8. **F05 is not audited readiness case** (247–285). It creates needs_clarification item; baseline already blocks this, so test misses the bug accepting classified/unapproved item with no documents, missing checklist permits, open reviews, active jobs, unknown coverage. Error `detail` existence does not prove blocking_issues contents.
9. **F06 only tests create API, not UI**. UI can still call list then falsely report success while POST endpoint test passes. Real browser create form -> persisted new ref is required.
10. **F07 tests only negative adapter case** (324–341). No positive SMTP network receipt, persisted message transition, retry/dedupe, actual worker routing, recipient allowlist, or exactly-one reminder. Assumes result.status which baseline uses delivery_status; explicitly choose adapter contract rather than accidental naming requirement.
11. **F08 tests a helper, not watcher pipeline**. One matching proposed dotted HS item; no nonmatching, arrived, submitted, overdue-not-arrived, company isolation, accepted-vs-proposed precedence, repeated-event dedupe, checklist/task/recalc evidence. Native endpoint could still be hardcoded.
12. **F11 docstring overclaims** (460–485). Only EXE rejection implemented; no oversized upload, forged MIME/magic bytes, encrypted PDF, valid PDF creation/version increment/job queue, or true PDF extraction.
13. **F12 only tests reclaim helper** (490–522). No crash after claim, recovery process, distinct job type dispatch, event race, dedupe, active-run invariant, or real external side-effect safety.
14. **F13 is vacuous** (528–535). No stale heartbeat seeded; status=UP with any status key passes. Need stale fixture -> degraded; fresh heartbeat ->healthy; workers idle must continue heartbeat.
15. **Commit/cleanup mismatch**. test_db_session finally rollback cannot undo earlier commit. Repeated runs leave fixed refs (READINESS-001 etc), causing collisions and order dependency. Use transaction-aware overrides or dedicated recreated test DB and deterministic full cleanup; never drop/reset production.

Author-controlled acceptance correction is appropriate because defects are in test fixtures, not permission to lower product requirements. Preserve this original suite and hash/failure history; add corrected contract version and independent E2E checks rather than coder silently editing protected tests.

## Required final E2E evidence

### Environment and safety
- Snapshot candidate SHA, clean tracked tree, protected spec/test hashes, exact deploy SHA, GitHub SHA.
- Explicit test DB current_database verified for API, ORM seed, worker, and any session provider. Test-only files/storage and SMTP sandbox. No resets in production verification.
- Real active staff/reviewer/admin in company A; real staff/admin company B. Test every entity ownership; positive read then cross-tenant 404.

### Arbitrary invoice / real 9Router
- Generate/upload two invoices with fresh, non-MKN references and different items/counts/values. Inputs differ from seed. PDF upload must create job automatically.
- Trace live while worker runs: before completion observe genuine extraction/tool/model steps, later terminal outcome. Browser refresh resumes without duplicates.
- Gateway actually called with configured model and nonzero measured usage; no fixed token or result strings. Keep request ID/model/usage and validated masked response, not secret.
- Item descriptions, counts, quantities/prices persisted reflect each PDF, classifications use catalog candidates and actual sources/quotes. Unknown/out-of-scope input cannot invent HS or tariff.
- Verify at least one clarifying item while complete items persist; answer or datasheet changes only related items, question count decreases, new run auto starts and links parent.
- Reviewer approve/modify updates exact item/version and queues real recalc, valid HS only; reject still blocks readiness. Assist does not autosend/approve; auto only under actual memory + attributes + low risk gate.

### Readiness and calculated data
- Independently recalculate one invoice using DB rates and Decimal; compare values API/UI/PIB. Different shipment values yield different totals. UI null data shows unavailable, not sample defaults.
- A classified but unapproved item, missing required doc, pending permit, open review, unknown lartas, or active job each blocks submit; exhaustive negative rows with positive all-complete control.
- Submission preserves real submitted fact during later rule changes.

### SMTP / followup
- Send a real request into isolated SMTP sandbox; inspect captured MIME recipient/template/thread tag, verify one DB message sent only after transport accepts.
- Closed port ->not sent; after-DATA uncertainty ->unknown, no blind retry. Duplicate event/crash does not duplicate capture.
- Approved team recipient only. At followup one reminder then staff task. Assist produces draft with no network.

### Generic watcher
- Fresh arbitrary shipment IDs/ref numbers: accepted HS 8481 matching, nonmatching HS, arrived matching, submitted matching, overdue-but-not-arrived matching, foreign-company matching.
- Rule effective today: only in-scope non-arrived matches get impact/recalc/new requirement; submitted stays submitted. Repeated same rule event creates no duplicate impact/checklist/messages. Future rule warns without premature activation.

### Worker recovery and frontend
- Terminate test worker after lease acquired; restart/reclaim -> terminal result with exactly one current classification/duty and no doubled email/review.
- Verify distinct send_email/followup/watch/analysis dispatch, leases renewed for long LLM calls, token cap all triggers, fresh idle heartbeat.
- Browser actual create form persists reference, upload input works, answer/review works, source links and actual SSE steps visible, no success toast without mutation.
- Five consecutive fresh runs against live 9Router, recording outcome, wait time vs compute, tokens, errors and screenshot. No invisible fake-model substitution.

### Evaluation/release
- Live eval runner derives metrics from per-item results; freeze dataset/prompt/model and record hashes. Recompute summary independently, include abstentions/failures in denominator, compare equivalent retrieval-only baseline.
- Remove unmeasured benchmark claims, verify data provenance and label unknown/simulation.
- Native Sentinel review on final exact candidate with these real evidence artifacts. Any subsequent candidate code change requires re-review; deploy and push main only same approved hash.
