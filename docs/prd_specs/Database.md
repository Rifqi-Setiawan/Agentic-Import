# Database

## Gambaran entitas

Ada 25 tabel dalam 6 kelompok. Tabel `shipments` dan `shipment_items` adalah pusatnya: hampir semua hasil analisis menyimpan `item_id` atau `shipment_id`.

&#91;embedded content: relasi tabel · 25 tabel dalam 6 kelompok\]

Relasi penting yang tidak digambar agar diagram tetap terbaca: `notifications.user_id` dan `audit_logs.actor_id` merujuk `users`. `hs_classifications.hs_code`, `pph22_rates.hs_code`, dan `classification_memory.hs_code` merujuk `hs_codes`. `lartas_rules.regulation_id` dan `regulation_impacts.regulation_id` merujuk `regulations`. `duty_calculations.exchange_rate_id` merujuk `exchange_rates`.

| Kelompok | Tabel | Isi |
| --- | --- | --- |
| Organisasi | `companies`, `users` | Perusahaan importir dan akun tiga peran |
| Kiriman | `shipments`, `documents`, `shipment_items` | Data kiriman, file yang diunggah, dan daftar barang hasil ekstraksi |
| Hasil analisis | `hs_classifications`, `clarifications`, `duty_calculations`, `checklist_items`, `review_tasks`, `pib_drafts`, `regulation_impacts` | Semua keluaran agent, per versi, sehingga riwayat perubahan bisa ditelusuri |
| Agent | `agent_runs`, `agent_steps`, `jobs`, `classification_memory` | Satu baris per eksekusi, langkah-langkahnya untuk panel jejak, antrean, dan memori klasifikasi |
| Referensi | `hs_codes`, `hs_notes`, `regulations`, `lartas_rules`, `pph22_rates`, `exchange_rates` | Data resmi yang di-seed dari CSV. Aturan simulasi juga masuk ke `regulations` dengan `is_simulated = true` |
| Sistem | `notifications`, `messages`, `audit_logs` | Notifikasi pengguna, email keluar dan masuk antara agent dan pemasok, serta catatan perubahan oleh manusia |

## Enum dan status

Semua enum disimpan sebagai `TEXT` dengan `CHECK` constraint, bukan tipe enum Postgres, supaya mudah diubah lewat migrasi. Nilai di bawah wajib sama persis di backend (Pydantic `Literal`) dan frontend (`types.ts`).

| Kolom | Nilai yang diizinkan |
| --- | --- |
| `users.role` | `importer_staff`, `ppjk_reviewer`, `admin` |
| `shipments.status` | `draft`, `analyzing`, `needs_clarification`, `needs_review`, `ready`, `submitted`, `arrived`, `failed` |
| `shipments.incoterm` | `EXW`, `FCA`, `FOB`, `CFR`, `CIF`, `DAP`, `DDP` |
| `shipments.transport_mode` | `sea`, `air` |
| `*.risk_level` | `low`, `medium`, `high` |
| `documents.doc_type` | `invoice`, `packing_list`, `bill_of_lading`, `permit`, `spec`, `insurance`, `other` |
| `documents.extraction_status` | `pending`, `done`, `failed` |
| `shipment_items.status` | `extracted`, `classifying`, `needs_clarification`, `classified`, `needs_review`, `approved`, `out_of_scope` |
| `hs_classifications.status` | `proposed`, `approved`, `modified`, `rejected`, `superseded` |
| `hs_classifications.decided_by` | `agent`, `reviewer` |
| `hs_notes.level` | `section`, `chapter`, `heading` |
| `clarifications.status` | `open`, `answered`, `cancelled` |
| `lartas_rules.stage` | `border`, `post_border` |
| `pph22_rates.lampiran` | `A`, `B`, `C` |
| `duty_calculations.pph22_basis` | `lampiran_a`, `lampiran_b`, `lampiran_c`, `with_api`, `without_api` |
| `checklist_items.status` | `missing`, `pending`, `provided`, `not_needed` |
| `checklist_items.source` | `rule`, `lartas`, `agent` |
| `review_tasks.status` | `open`, `approved`, `modified`, `rejected` |
| `pib_drafts.status` | `draft`, `ready`, `submitted` |
| `agent_runs.run_type` | `analyze`, `reanalyze_item`, `regulation_watch` |
| `agent_runs.trigger` | `manual`, `clarification_answer`, `review_decision`, `regulation_event`, `schedule`, `document_uploaded`, `inbound_email`, `followup` |
| `agent_runs.status` | `queued`, `running`, `paused`, `succeeded`, `failed`, `cancelled` |
| `agent_steps.step_type` | `plan`, `llm`, `tool_call`, `tool_result`, `decision`, `clarification`, `retry`, `fallback`, `error`, `info`, `done` |
| `agent_steps.status` | `ok`, `warning`, `error` |
| `jobs.status` | `queued`, `running`, `done`, `failed` |
| `regulation_impacts.impact_type` | `new_permit`, `permit_removed`, `rule_changed` |
| `companies.autonomy_level` | `assist` (email jadi draf, tanpa persetujuan otomatis), `auto` (email terkirim otomatis, persetujuan otomatis untuk barang berkeyakinan tinggi) |
| `clarifications.channel` | `staff`, `supplier` |
| `messages.direction` | `outbound`, `inbound` |
| `messages.kind` | `supplier_request, supplier_reminder, supplier_reply, new_shipment, other` |
| `messages.status` | `draft, queued, sent, failed, received, answered, ignored, cancelled` |

## Skema SQL lengkap

Skema ini menjadi acuan migrasi Alembic pertama (`0001_initial`). Semua timestamp memakai `timestamptz` dan disimpan dalam UTC. Konversi ke WIB dilakukan di frontend. Nilai uang disimpan sebagai `numeric`, tidak pernah `float`.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- ===== Organisasi dan pengguna =====
CREATE TABLE companies (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name          text NOT NULL,
  npwp          text,                       -- dummy, disamarkan sebelum ke LLM
  has_api       boolean NOT NULL DEFAULT false,  -- Angka Pengenal Importir
  autonomy_level text NOT NULL DEFAULT 'auto' CHECK (autonomy_level IN ('assist','auto')),
  address       text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id     uuid NOT NULL REFERENCES companies(id),
  email          text NOT NULL UNIQUE,      -- disimpan lowercase
  password_hash  text NOT NULL,
  full_name      text NOT NULL,
  role           text NOT NULL CHECK (role IN ('importer_staff','ppjk_reviewer','admin')),
  is_active      boolean NOT NULL DEFAULT true,
  last_login_at  timestamptz,
  created_at     timestamptz NOT NULL DEFAULT now()
);

-- ===== Data referensi =====
CREATE TABLE hs_codes (
  code            char(8) PRIMARY KEY CHECK (code ~ '^[0-9]{8}$'),
  chapter         char(2) NOT NULL,
  heading         char(4) NOT NULL,
  subheading      char(6) NOT NULL,
  description_id  text NOT NULL,
  description_en  text,
  description_raw text,                     -- uraian asli BTKI, sering hanya 'Lain-lain'
  note            text,                     -- 'BELUM DIVERIFIKASI' atau catatan perubahan tarif
  unit            text,
  bm_rate         numeric(6,3) NOT NULL,    -- persen, contoh 7.500 = 7,5%
  is_luxury       boolean NOT NULL DEFAULT false,
  is_active       boolean NOT NULL DEFAULT true,
  source          text NOT NULL DEFAULT 'BTKI 2022 (PMK 26/PMK.010/2022)',
  search_tsv      tsvector GENERATED ALWAYS AS (
                    to_tsvector('simple', coalesce(description_id,'') || ' ' || coalesce(description_en,''))
                  ) STORED,
  embedding       vector(768)
);

CREATE TABLE hs_notes (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  level       text NOT NULL CHECK (level IN ('section','chapter','heading')),
  ref         text NOT NULL,                -- contoh '84' atau '8481'
  title       text,
  body        text NOT NULL,
  source      text NOT NULL,
  embedding   vector(768)
);

CREATE TABLE regulations (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  number          text NOT NULL,            -- contoh 'Permendag 8/2024'
  title           text NOT NULL,
  issuer          text NOT NULL,
  summary         text,
  effective_date  date NOT NULL,
  source_url      text,
  is_simulated    boolean NOT NULL DEFAULT false,
  created_by      uuid REFERENCES users(id),
  created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE lartas_rules (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  regulation_id      uuid REFERENCES regulations(id),
  hs_prefix          varchar(8) NOT NULL CHECK (hs_prefix ~ '^[0-9]{4,8}$'),
  permit_name        text NOT NULL,
  permit_code        text,
  issuing_agency     text NOT NULL,
  stage              text NOT NULL CHECK (stage IN ('border','post_border')),
  requires_surveyor  boolean NOT NULL DEFAULT false,
  effective_from     date NOT NULL,
  effective_to       date,
  source_url         text,
  retrieved_at       date NOT NULL,         -- tanggal data diambil dari INSW
  note               text
);

CREATE TABLE pph22_rates (
  hs_code     char(8) PRIMARY KEY REFERENCES hs_codes(code),
  lampiran    text NOT NULL CHECK (lampiran IN ('A','B','C')),
  rate        numeric(5,3) NOT NULL,        -- persen
  regulation  text NOT NULL DEFAULT 'PMK 51/2025'
);

CREATE TABLE exchange_rates (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  currency    char(3) NOT NULL,
  rate_idr    numeric(18,4) NOT NULL,       -- NDPBM / kurs Menteri Keuangan
  valid_from  date NOT NULL,
  valid_to    date NOT NULL,
  source      text NOT NULL,
  UNIQUE (currency, valid_from)
);

-- ===== Kiriman dan dokumen =====
CREATE TABLE shipments (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id       uuid NOT NULL REFERENCES companies(id),
  ref_no           text NOT NULL,
  supplier_name    text NOT NULL,
  supplier_email   text,                    -- satu-satunya alamat yang boleh dikirimi email oleh agent
  origin_country   char(2) NOT NULL,        -- ISO 3166-1 alpha-2
  incoterm         text NOT NULL CHECK (incoterm IN ('EXW','FCA','FOB','CFR','CIF','DAP','DDP')),
  currency         char(3) NOT NULL,        -- ISO 4217
  invoice_value    numeric(18,2) NOT NULL CHECK (invoice_value > 0),
  freight_value    numeric(18,2) NOT NULL DEFAULT 0,
  insurance_value  numeric(18,2),           -- NULL = belum diketahui
  transport_mode   text NOT NULL CHECK (transport_mode IN ('sea','air')),
  port_of_loading  text,
  port_of_entry    text NOT NULL,
  eta              date NOT NULL,
  status           text NOT NULL DEFAULT 'draft' CHECK (status IN
                     ('draft','analyzing','needs_clarification','needs_review','ready','submitted','arrived','failed')),
  risk_level       text CHECK (risk_level IN ('low','medium','high')),
  created_by       uuid NOT NULL REFERENCES users(id),
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (company_id, ref_no)
);

CREATE TABLE documents (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id        uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  doc_type           text NOT NULL CHECK (doc_type IN ('invoice','packing_list','bill_of_lading','permit','spec','insurance','other')),
  original_filename  text NOT NULL,
  storage_path       text NOT NULL,         -- path di UPLOAD_DIR, nama file = uuid
  mime_type          text NOT NULL,
  size_bytes         integer NOT NULL,
  sha256             char(64) NOT NULL,
  page_count         integer,
  extraction_status  text NOT NULL DEFAULT 'pending' CHECK (extraction_status IN ('pending','done','failed')),
  extracted_text     text,
  uploaded_by        uuid NOT NULL REFERENCES users(id),
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE shipment_items (
  id                         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id                uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  line_no                    integer NOT NULL,
  description_raw            text NOT NULL,
  description_normalized     text,
  attributes                 jsonb NOT NULL DEFAULT '{}'::jsonb,  -- material, fungsi, komposisi, dll
  quantity                   numeric(18,3) NOT NULL,
  unit                       text NOT NULL,
  unit_price                 numeric(18,4) NOT NULL,
  fob_value                  numeric(18,2) NOT NULL,
  origin_country             char(2),
  source_document_id         uuid REFERENCES documents(id),
  status                     text NOT NULL DEFAULT 'extracted' CHECK (status IN
                               ('extracted','classifying','needs_clarification','classified','needs_review','approved','out_of_scope')),
  risk_level                 text CHECK (risk_level IN ('low','medium','high')),
  risk_reasons               jsonb NOT NULL DEFAULT '[]'::jsonb,
  current_classification_id  uuid,          -- FK ditambahkan di bawah
  embedding                  vector(768),
  created_at                 timestamptz NOT NULL DEFAULT now(),
  updated_at                 timestamptz NOT NULL DEFAULT now(),
  UNIQUE (shipment_id, line_no)
);

-- ===== Agent =====
CREATE TABLE agent_runs (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id        uuid REFERENCES shipments(id) ON DELETE CASCADE,
  run_type           text NOT NULL CHECK (run_type IN ('analyze','reanalyze_item','regulation_watch')),
  trigger            text NOT NULL CHECK (trigger IN ('manual','clarification_answer','review_decision','regulation_event','schedule','document_uploaded','inbound_email','followup')),
  status             text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','paused','succeeded','failed','cancelled')),
  thread_id          text NOT NULL,         -- thread_id checkpoint LangGraph
  model_primary      text,
  fallback_used      boolean NOT NULL DEFAULT false,
  prompt_tokens      integer NOT NULL DEFAULT 0,
  completion_tokens  integer NOT NULL DEFAULT 0,
  error_code         text,
  error_message      text,
  created_by         uuid REFERENCES users(id),
  created_at         timestamptz NOT NULL DEFAULT now(),
  started_at         timestamptz,
  finished_at        timestamptz
);

CREATE TABLE agent_steps (
  id           bigserial PRIMARY KEY,
  run_id       uuid NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  seq          integer NOT NULL,
  step_type    text NOT NULL CHECK (step_type IN
                 ('plan','llm','tool_call','tool_result','decision','clarification','retry','fallback','error','info','done')),
  node         text NOT NULL,
  tool_name    text,
  item_id      uuid REFERENCES shipment_items(id) ON DELETE CASCADE,
  title        text NOT NULL,               -- kalimat singkat untuk UI
  detail       text,
  payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
  status       text NOT NULL DEFAULT 'ok' CHECK (status IN ('ok','warning','error')),
  duration_ms  integer,
  created_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (run_id, seq)
);

CREATE TABLE hs_classifications (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id             uuid NOT NULL REFERENCES shipment_items(id) ON DELETE CASCADE,
  run_id              uuid REFERENCES agent_runs(id),
  version             integer NOT NULL,
  hs_code             char(8) NOT NULL REFERENCES hs_codes(code),
  confidence          numeric(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  llm_confidence      numeric(4,3),
  retrieval_score     numeric(4,3),
  memory_score        numeric(4,3),
  gri_applied         text[] NOT NULL DEFAULT '{}',   -- contoh {'KUMHS 1','KUMHS 6'}
  rationale           text NOT NULL,
  alternatives        jsonb NOT NULL DEFAULT '[]'::jsonb,  -- [{hs_code, why_not}]
  citations           jsonb NOT NULL DEFAULT '[]'::jsonb,  -- [{type, ref, quote}]
  missing_attributes  jsonb NOT NULL DEFAULT '[]'::jsonb,
  decided_by          text NOT NULL CHECK (decided_by IN ('agent','reviewer')),
  status              text NOT NULL DEFAULT 'proposed' CHECK (status IN ('proposed','approved','modified','rejected','superseded')),
  reviewer_id         uuid REFERENCES users(id),
  review_note         text,
  created_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (item_id, version)
);

ALTER TABLE shipment_items
  ADD CONSTRAINT fk_items_current_classification
  FOREIGN KEY (current_classification_id) REFERENCES hs_classifications(id) ON DELETE SET NULL;

CREATE TABLE classification_memory (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id                uuid NOT NULL REFERENCES companies(id),
  item_description          text NOT NULL,
  attributes                jsonb NOT NULL DEFAULT '{}'::jsonb,
  hs_code                   char(8) NOT NULL REFERENCES hs_codes(code),
  source_classification_id  uuid REFERENCES hs_classifications(id) ON DELETE SET NULL,
  embedding                 vector(768) NOT NULL,
  created_at                timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE clarifications (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id  uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  item_id      uuid NOT NULL REFERENCES shipment_items(id) ON DELETE CASCADE,
  run_id       uuid NOT NULL REFERENCES agent_runs(id),
  question     text NOT NULL,
  channel      text NOT NULL DEFAULT 'staff' CHECK (channel IN ('staff','supplier')),
  message_id   uuid,                        -- email permintaan ke pemasok bila channel = 'supplier' (FK ditambahkan setelah tabel messages)
  options      jsonb NOT NULL DEFAULT '[]'::jsonb,   -- ["Besi cor","Baja tahan karat",...]
  answer       text,
  status       text NOT NULL DEFAULT 'open' CHECK (status IN ('open','answered','cancelled')),
  answered_by  uuid REFERENCES users(id),
  asked_at     timestamptz NOT NULL DEFAULT now(),
  answered_at  timestamptz
);

-- ===== Hasil analisis =====
CREATE TABLE duty_calculations (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  item_id             uuid NOT NULL REFERENCES shipment_items(id) ON DELETE CASCADE,
  classification_id   uuid NOT NULL REFERENCES hs_classifications(id) ON DELETE CASCADE,
  exchange_rate_id    uuid NOT NULL REFERENCES exchange_rates(id),
  currency            char(3) NOT NULL,
  fob_value           numeric(18,2) NOT NULL,
  freight_alloc       numeric(18,2) NOT NULL,
  insurance_alloc     numeric(18,2) NOT NULL,
  cif_value           numeric(18,2) NOT NULL,
  cif_idr             numeric(20,2) NOT NULL,
  bm_rate             numeric(6,3) NOT NULL,
  bm_amount           numeric(20,2) NOT NULL,
  import_value        numeric(20,2) NOT NULL,
  ppn_rate_effective  numeric(6,3) NOT NULL,     -- 11.000 untuk barang bukan mewah
  ppn_amount          numeric(20,2) NOT NULL,
  pph22_rate          numeric(5,3) NOT NULL,
  pph22_basis         text NOT NULL CHECK (pph22_basis IN ('lampiran_a','lampiran_b','lampiran_c','with_api','without_api')),
  pph22_amount        numeric(20,2) NOT NULL,
  total_amount        numeric(20,2) NOT NULL,
  warnings            jsonb NOT NULL DEFAULT '[]'::jsonb,
  is_current          boolean NOT NULL DEFAULT true,
  created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE checklist_items (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id       uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  item_id           uuid REFERENCES shipment_items(id) ON DELETE CASCADE,
  requirement_code  text NOT NULL,          -- contoh 'INVOICE', 'PERMIT:PI-BAJA', 'INSURANCE_VALUE'
  label             text NOT NULL,
  reason            text NOT NULL,
  status            text NOT NULL DEFAULT 'missing' CHECK (status IN ('missing','pending','provided','not_needed')),
  source            text NOT NULL CHECK (source IN ('rule','lartas','agent')),
  lartas_rule_id    uuid REFERENCES lartas_rules(id),
  document_id       uuid REFERENCES documents(id) ON DELETE SET NULL,
  updated_by        uuid REFERENCES users(id),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE (shipment_id, item_id, requirement_code)
);

CREATE TABLE review_tasks (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id        uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  item_id            uuid NOT NULL REFERENCES shipment_items(id) ON DELETE CASCADE,
  classification_id  uuid REFERENCES hs_classifications(id),
  reasons            jsonb NOT NULL,       -- [{code, message}]
  status             text NOT NULL DEFAULT 'open' CHECK (status IN ('open','approved','modified','rejected')),
  decision_hs_code   char(8) REFERENCES hs_codes(code),
  decision_note      text,
  decided_by         uuid REFERENCES users(id),
  decided_at         timestamptz,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE pib_drafts (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id  uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  version      integer NOT NULL,
  payload      jsonb NOT NULL,              -- {header:{...}, items:[...], totals:{...}}
  status       text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','ready','submitted')),
  created_at   timestamptz NOT NULL DEFAULT now(),
  UNIQUE (shipment_id, version)
);

CREATE TABLE regulation_impacts (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  regulation_id  uuid NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
  shipment_id    uuid NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  item_id        uuid REFERENCES shipment_items(id) ON DELETE CASCADE,
  impact_type    text NOT NULL CHECK (impact_type IN ('new_permit','permit_removed','rule_changed')),
  detail         jsonb NOT NULL,
  run_id         uuid REFERENCES agent_runs(id),
  created_at     timestamptz NOT NULL DEFAULT now()
);

-- ===== Infrastruktur aplikasi =====
CREATE TABLE jobs (
  id            bigserial PRIMARY KEY,
  job_type      text NOT NULL,              -- 'analyze_shipment', 'resume_run', 'watch_regulation', 'reset_demo', 'followup_check', 'poll_inbox', 'send_email'
  payload       jsonb NOT NULL,
  status        text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','running','done','failed')),
  attempts      integer NOT NULL DEFAULT 0,
  max_attempts  integer NOT NULL DEFAULT 3,
  run_after     timestamptz NOT NULL DEFAULT now(),
  locked_at     timestamptz,
  locked_by     text,
  last_error    text,
  created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE notifications (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type        text NOT NULL,                -- 'clarification_needed','review_needed','analysis_done','regulation_impact','analysis_failed','staff_task','supplier_reply','email_sent'
  title       text NOT NULL,
  body        text NOT NULL,
  link        text,                         -- path frontend, contoh '/shipments/<id>'
  is_read     boolean NOT NULL DEFAULT false,
  emailed     boolean NOT NULL DEFAULT false,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE messages (
  id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  shipment_id              uuid REFERENCES shipments(id) ON DELETE CASCADE,  -- NULL untuk email masuk yang belum dicocokkan
  run_id                   uuid REFERENCES agent_runs(id),
  direction                text NOT NULL CHECK (direction IN ('outbound','inbound')),
  kind                     text NOT NULL CHECK (kind IN ('supplier_request','supplier_reminder','supplier_reply','new_shipment','other')),
  to_address               text,
  from_address             text,
  subject                  text NOT NULL,
  body                     text NOT NULL,
  thread_tag               text,             -- contoh 'IMJ-7K2Q', untuk mencocokkan balasan
  requested                jsonb NOT NULL DEFAULT '{}'::jsonb,  -- {question_ids:[], documents:[{doc_type, reason}]}
  attachment_document_ids  uuid[] NOT NULL DEFAULT '{}',
  status                   text NOT NULL DEFAULT 'draft' CHECK (status IN
                             ('draft','queued','sent','failed','received','answered','ignored','cancelled')),
  error_message            text,
  approved_by              uuid REFERENCES users(id),  -- diisi bila staf mengirim draf (tingkat assist)
  sent_at                  timestamptz,
  created_at               timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_thread_tag ON messages (thread_tag);
CREATE INDEX idx_messages_shipment ON messages (shipment_id, created_at DESC);
ALTER TABLE clarifications
  ADD CONSTRAINT fk_clarifications_message FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL;

CREATE TABLE audit_logs (
  id           bigserial PRIMARY KEY,
  actor_id     uuid REFERENCES users(id),
  action       text NOT NULL,              -- 'review.decide', 'shipment.update', 'regulation.create', ...
  entity_type  text NOT NULL,
  entity_id    uuid,
  before       jsonb,
  after        jsonb,
  created_at   timestamptz NOT NULL DEFAULT now()
);
```

Tabel checkpoint LangGraph (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`, dan sejenisnya) tidak ditulis manual. Tabel itu dibuat otomatis dengan memanggil `PostgresSaver.setup()` sekali saat worker pertama kali berjalan.

## Indeks, query penting, dan catatan migrasi

```sql
-- Pencarian kode HS (hybrid: full-text + vektor)
CREATE INDEX idx_hs_codes_tsv        ON hs_codes USING gin (search_tsv);
CREATE INDEX idx_hs_codes_embedding  ON hs_codes USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_hs_codes_chapter    ON hs_codes (chapter);
CREATE INDEX idx_hs_notes_ref        ON hs_notes (level, ref);
CREATE INDEX idx_hs_notes_embedding  ON hs_notes USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_memory_embedding    ON classification_memory USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_memory_company      ON classification_memory (company_id);

-- Operasional
CREATE INDEX idx_shipments_company_status ON shipments (company_id, status);
CREATE INDEX idx_shipments_eta            ON shipments (eta);
CREATE INDEX idx_items_shipment           ON shipment_items (shipment_id);
CREATE INDEX idx_class_item               ON hs_classifications (item_id, version DESC);
CREATE INDEX idx_steps_run_seq            ON agent_steps (run_id, seq);
CREATE INDEX idx_runs_shipment            ON agent_runs (shipment_id, created_at DESC);
CREATE INDEX idx_clarif_open              ON clarifications (shipment_id) WHERE status = 'open';
CREATE INDEX idx_review_open              ON review_tasks (status, created_at) WHERE status = 'open';
CREATE INDEX idx_lartas_prefix            ON lartas_rules (hs_prefix);
CREATE INDEX idx_duty_current             ON duty_calculations (item_id) WHERE is_current;
CREATE INDEX idx_notif_user_unread        ON notifications (user_id, created_at DESC) WHERE NOT is_read;
CREATE INDEX idx_jobs_queue               ON jobs (run_after) WHERE status = 'queued';
```

**Query pencarian kandidat HS** (dipakai tool `search_hs_candidates`). Skor gabungan memakai reciprocal rank fusion supaya hasil full-text dan vektor bisa digabung tanpa menyamakan skala:

```sql
WITH fts AS (
  SELECT code, row_number() OVER (ORDER BY ts_rank(search_tsv, q) DESC) AS r
  FROM hs_codes, plainto_tsquery('simple', :query_text) q
  WHERE search_tsv @@ q AND chapter = ANY(:chapters) AND is_active
  ORDER BY ts_rank(search_tsv, q) DESC
  LIMIT 30
), vec AS (
  SELECT code, row_number() OVER (ORDER BY embedding <=> :query_vec) AS r
  FROM hs_codes
  WHERE chapter = ANY(:chapters) AND is_active
  ORDER BY embedding <=> :query_vec
  LIMIT 30
)
SELECT h.code, h.description_id, h.description_en, h.bm_rate,
       COALESCE(1.0/(60+fts.r),0) + COALESCE(1.0/(60+vec.r),0) AS score
FROM hs_codes h
LEFT JOIN fts ON fts.code = h.code
LEFT JOIN vec ON vec.code = h.code
WHERE fts.code IS NOT NULL OR vec.code IS NOT NULL
ORDER BY score DESC
LIMIT :top_k;
```

**Query lartas untuk satu kode** (prefiks terpanjang yang cocok dianggap paling spesifik):

```sql
SELECT * FROM lartas_rules
WHERE :hs_code LIKE hs_prefix || '%'
  AND effective_from <= :on_date
  AND (effective_to IS NULL OR effective_to >= :on_date)
ORDER BY length(hs_prefix) DESC;
```

**Query kurs yang berlaku:**

```sql
SELECT * FROM exchange_rates
WHERE currency = :currency AND :on_date BETWEEN valid_from AND valid_to
ORDER BY valid_from DESC LIMIT 1;
```

Catatan migrasi:

- Image database: `pgvector/pgvector:pg16`, jadi ekstensi `vector` sudah tersedia.
- Model e5 membutuhkan awalan teks: ` query:  ` untuk teks pencarian dan ` passage:  ` untuk teks yang disimpan. Lupa awalan ini akan menurunkan kualitas pencarian.
- Kolom `updated_at` diperbarui oleh SQLAlchemy (`onupdate=func.now()`), tidak memakai trigger.
- Reset data demo menghapus isi tabel transaksi (shipments dan semua turunannya, agent\_runs, notifications, messages, jobs, audit\_logs, classification\_memory selain data awal) lalu menjalankan `seed_demo.py`. Data referensi (hs\_codes, hs\_notes, lartas\_rules non-simulasi, pph22\_rates, exchange\_rates) tidak ikut dihapus.
