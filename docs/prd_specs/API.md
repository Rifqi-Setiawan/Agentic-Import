# API

## Konvensi API

Semua endpoint REST memakai JSON, kecuali unggah file (multipart) dan stream SSE. Dokumentasi interaktif otomatis tersedia di `https://api.<domain>/docs` dari FastAPI, dan link ini ikut dicantumkan di README.

| Hal | Aturan |
| --- | --- |
| Base URL | `https://api.<domain>/api/v1` |
| Auth | Header `Authorization: Bearer <access_token>`. Token didapat dari `POST /auth/login`. Semua endpoint wajib token kecuali `/auth/login` dan `/health` |
| Auth untuk SSE | `EventSource` tidak bisa mengirim header, jadi stream memakai query `?token=<stream_token>`. Stream token didapat dari `POST /runs/{id}/stream-token`, berlaku 10 menit dan hanya untuk satu run |
| Penamaan | URL memakai kata benda jamak dan kebab-case. Field JSON memakai snake\_case |
| ID | UUID v4 dalam bentuk string |
| Waktu | ISO 8601 UTC, contoh `2026-11-05T03:12:45Z`. Tanggal saja memakai `YYYY-MM-DD` |
| Uang | String desimal agar tidak kehilangan presisi, contoh `"12500000.00"`. Frontend memformat ke Rupiah |
| Persen | Angka persen, contoh `7.5` berarti 7,5% |
| Paginasi | Query `page` (mulai 1) dan `page_size` (bawaan 20, maksimal 100). Respons memuat `meta.page`, `meta.page_size`, `meta.total` |
| Filter dan urutan | Query sederhana, contoh `?status=needs_review&sort=-created_at` |
| Versi | Prefiks `/api/v1`. Perubahan yang merusak kompatibilitas tidak dilakukan selama lomba |

### Format respons sukses

```json
{
  "data": { "...": "objek atau array" },
  "meta": { "page": 1, "page_size": 20, "total": 42 }
}
```

`meta` hanya ada di endpoint daftar.

### Format respons error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Data yang dikirim belum lengkap.",
    "details": [
      { "field": "eta", "message": "Tanggal ETA wajib diisi." }
    ],
    "request_id": "req_7f3a2c"
  }
}
```

`message` selalu dalam bahasa Indonesia dan aman ditampilkan langsung ke pengguna. `request_id` juga dicatat di log server untuk debugging.

| HTTP | `error.code` | Kapan |
| --- | --- | --- |
| 400 | `BAD_REQUEST` | Permintaan tidak bisa diproses, misalnya status kiriman tidak mengizinkan aksi ini |
| 401 | `UNAUTHORIZED` | Token tidak ada, salah, atau kedaluwarsa |
| 403 | `FORBIDDEN` | Peran tidak punya hak |
| 404 | `NOT_FOUND` | Data tidak ada atau milik perusahaan lain |
| 409 | `CONFLICT` | Bentrok, misalnya nomor referensi sudah dipakai atau analisis sedang berjalan |
| 413 | `FILE_TOO_LARGE` | File melebihi `MAX_UPLOAD_MB` |
| 415 | `UNSUPPORTED_FILE` | Tipe file selain PDF, JPG, PNG |
| 422 | `VALIDATION_ERROR` | Validasi field gagal |
| 429 | `RATE_LIMITED` | Terlalu banyak permintaan |
| 500 | `INTERNAL_ERROR` | Error tak terduga |
| 503 | `LLM_UNAVAILABLE` | Semua model LLM gagal setelah fallback |

Batas permintaan: login 5 per menit per IP, `POST /shipments/{id}/analyze` 6 per menit per pengguna, endpoint lain 120 per menit per pengguna.

## Daftar endpoint

Kolom Peran: **S** = `importer_staff`, **R** = `ppjk_reviewer`, **A** = `admin`. Semua data otomatis dibatasi ke perusahaan pengguna yang login. Path ditulis relatif terhadap `/api/v1`.

| Metode | Path | Peran | Fungsi |
| --- | --- | --- | --- |
| GET | `/health` | Publik | Cek status API, database, dan worker |
| POST | `/auth/login` | Publik | Login, mengembalikan token dan profil |
| GET | `/auth/me` | S R A | Profil pengguna yang login |
| GET | `/dashboard/summary` | S R A | Angka ringkas untuk dashboard |
| GET | `/shipments` | S R A | Daftar kiriman, filter `status`, `risk_level`, `q` |
| POST | `/shipments` | S A | Buat kiriman |
| GET | `/shipments/{id}` | S R A | Detail kiriman beserta ringkasan |
| PATCH | `/shipments/{id}` | S A | Ubah data kiriman (hanya saat `draft`, `ready`, atau `failed`) |
| DELETE | `/shipments/{id}` | A | Hapus kiriman |
| POST | `/shipments/{id}/mark-submitted` | S A | Tandai PIB sudah diajukan di luar sistem |
| POST | `/shipments/{id}/mark-arrived` | S A | Tandai barang tiba |
| POST | `/shipments/{id}/documents` | S A | Unggah dokumen (multipart) |
| GET | `/shipments/{id}/documents` | S R A | Daftar dokumen |
| GET | `/documents/{id}/file` | S R A | Unduh file asli |
| DELETE | `/documents/{id}` | S A | Hapus dokumen (hanya saat `draft`) |
| POST | `/shipments/{id}/analyze` | S A | Mulai analisis agent, mengembalikan `run_id` |
| GET | `/shipments/{id}/runs` | S R A | Riwayat agent run |
| GET | `/runs/{id}` | S R A | Status satu run |
| GET | `/runs/{id}/steps` | S R A | Semua langkah run (untuk memuat ulang panel jejak) |
| POST | `/runs/{id}/stream-token` | S R A | Token sementara untuk SSE |
| GET | `/runs/{id}/stream?token=...` | Token stream | Stream SSE langkah agent |
| POST | `/runs/{id}/cancel` | S A | Batalkan run yang sedang berjalan |
| GET | `/shipments/{id}/items` | S R A | Daftar barang beserta klasifikasi, lartas, pungutan, dan risiko terbaru |
| GET | `/items/{id}` | S R A | Detail satu barang termasuk semua versi klasifikasi |
| PATCH | `/items/{id}` | S A | Koreksi data barang hasil ekstraksi (deskripsi, jumlah, harga) |
| POST | `/items/{id}/reanalyze` | S A | Analisis ulang satu barang |
| GET | `/clarifications` | S A | Kotak masuk pertanyaan, filter `status` |
| POST | `/clarifications/{id}/answer` | S A | Jawab pertanyaan agent, otomatis melanjutkan run |
| GET | `/reviews` | R A | Antrean review, filter `status` |
| GET | `/reviews/{id}` | R A | Detail review dengan alasan agent dan sumber |
| POST | `/reviews/{id}/decision` | R A | Putuskan review |
| GET | `/shipments/{id}/duties` | S R A | Rincian pungutan per barang dan total |
| GET | `/shipments/{id}/checklist` | S R A | Checklist dokumen |
| PATCH | `/checklist/{id}` | S A | Ubah status checklist, opsional tautkan dokumen |
| GET | `/shipments/{id}/pib-draft` | S R A | Draf PIB versi terbaru |
| GET | `/shipments/{id}/pib-draft/pdf` | S R A | Unduh draf PIB sebagai PDF (P1) |
| GET | `/shipments/{id}/plan` | S R A | Rencana agent versi terbaru beserta riwayat revisinya |
| GET | `/shipments/{id}/messages` | S R A | Email keluar dan masuk antara agent dan pemasok untuk kiriman ini |
| PATCH | `/messages/{id}` | S A | Ubah subjek atau isi draf email (hanya status draft) |
| POST | `/messages/{id}/send` | S A | Kirim draf email buatan agent (tingkat otonomi assist) |
| POST | `/messages/{id}/cancel` | S A | Batalkan draf atau email yang masih antre |
| GET | `/regulations` | S R A | Daftar aturan, termasuk simulasi |
| POST | `/regulations` | A | Tambah aturan baru beserta aturan lartas, memicu agent pemantau |
| POST | `/regulations/simulate-demo` | A | Terbitkan aturan simulasi bawaan untuk demo dalam satu klik |
| GET | `/regulations/{id}/impacts` | S R A | Kiriman dan barang yang terdampak |
| GET | `/hs-codes/search?q=&chapter=` | S R A | Pencarian kode HS manual |
| GET | `/hs-codes/{code}` | S R A | Detail kode, catatan bab, lartas, dan tarif |
| GET | `/notifications` | S R A | Notifikasi pengguna |
| POST | `/notifications/{id}/read` | S R A | Tandai terbaca |
| POST | `/notifications/read-all` | S R A | Tandai semua terbaca |
| GET | `/admin/users` | A | Daftar pengguna |
| POST | `/admin/demo/reset` | A | Reset data demo |
| GET | `/admin/company-settings` | A | Lihat tingkat otonomi agent dan alamat inbox agent |
| PATCH | `/admin/company-settings` | A | Ubah tingkat otonomi: { "autonomy\_level": "assist" \| "auto" } |

## Detail endpoint inti

Contoh di bawah adalah bentuk final yang dipakai frontend dan backend. Endpoint lain mengikuti pola yang sama.

### POST /auth/login

```json
// Request
{ "email": "staf@demo.imporjaga.id", "password": "Demo2026!" }

// 200 OK
{
  "data": {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_at": "2026-11-05T15:00:00Z",
    "user": {
      "id": "6f1c...", "email": "staf@demo.imporjaga.id", "full_name": "Rina Staf Impor",
      "role": "importer_staff",
      "company": { "id": "a0b1...", "name": "PT Mitra Kemas Nusantara", "has_api": true }
    }
  }
}
```

### POST /shipments

```json
// Request
{
  "ref_no": "MKN-IMP-2611-007",
  "supplier_name": "Zhejiang Valve Industrial Co.",
  "supplier_email": "sales@zhejiang-valve.example",
  "origin_country": "CN",
  "incoterm": "FOB",
  "currency": "USD",
  "invoice_value": "18450.00",
  "freight_value": "950.00",
  "insurance_value": null,
  "transport_mode": "sea",
  "port_of_loading": "Ningbo",
  "port_of_entry": "Tanjung Priok",
  "eta": "2026-11-20"
}

// 201 Created
{ "data": { "id": "3c9e...", "status": "draft", "risk_level": null, "created_at": "2026-11-05T02:10:00Z", "...": "semua field request" } }
```

Validasi: `ref_no` unik per perusahaan, `origin_country` 2 huruf ISO, `currency` 3 huruf ISO dan harus ada di `exchange_rates`, `invoice_value` lebih dari 0, `eta` tidak boleh lebih dari 1 tahun ke depan.

### POST /shipments/{id}/documents

Request `multipart/form-data` dengan field `file` (wajib) dan `doc_type` (wajib, salah satu enum `documents.doc_type`).

```json
// 201 Created
{
  "data": {
    "id": "d71a...", "doc_type": "invoice", "original_filename": "INV-ZV-8812.pdf",
    "mime_type": "application/pdf", "size_bytes": 184233, "page_count": 2,
    "extraction_status": "pending", "created_at": "2026-11-05T02:12:10Z"
  }
}
```

Backend memeriksa magic bytes file, bukan hanya ekstensi. Nama file di disk diganti UUID. File PDF yang dienkripsi ditolak dengan `UNSUPPORTED_FILE`.

Pemicu otomatis: unggahan `doc_type = invoice` pada kiriman berstatus `draft` langsung membuat job `analyze_shipment` dengan trigger `document_uploaded`. Dokumen apa pun yang diunggah ke kiriman berstatus `needs_clarification` atau `needs_review` membuat run `items_subset`. Beberapa unggahan dalam 10 detik digabung menjadi satu run. Respons unggah menambahkan field `auto_run_id` (null bila tidak ada run baru), dan frontend langsung membuka panel jejak untuk run itu. `supplier_email` di `POST /shipments` bersifat opsional, tetapi tanpa itu agent tidak bisa meminta dokumen ke pemasok dan akan membuat tugas staf sebagai gantinya.

### POST /shipments/{id}/analyze

```json
// Request (opsional)
{ "force": false }

// 202 Accepted
{ "data": { "run_id": "8b2f...", "status": "queued", "shipment_status": "analyzing" } }
```

Aturan: minimal satu dokumen `invoice` sudah terunggah. Kalau ada run berstatus `queued`, `running`, atau `paused`, respons 409 `CONFLICT` dengan `run_id` yang sedang aktif di `details`.

### GET /shipments/{id}/items

```json
// 200 OK (satu elemen ditampilkan)
{
  "data": [
    {
      "id": "it01...",
      "line_no": 1,
      "description_raw": "Gate valve DN50 PN16, cast iron body, flanged",
      "attributes": { "material": "besi cor", "function": "katup gerbang untuk pipa air", "size": "DN50" },
      "quantity": "120.000", "unit": "PCS", "unit_price": "38.5000", "fob_value": "4620.00",
      "status": "classified",
      "risk_level": "medium",
      "risk_reasons": [ { "code": "CONFIDENCE_MEDIUM", "message": "Keyakinan klasifikasi 0,81." } ],
      "classification": {
        "id": "cl01...", "version": 1, "hs_code": "84818099",
        "hs_description_id": "(uraian sesuai BTKI)",
        "confidence": 0.81,
        "gri_applied": ["KUMHS 1", "KUMHS 6"],
        "rationale": "Barang adalah katup gerbang berbadan besi cor untuk pipa...",
        "alternatives": [ { "hs_code": "84813090", "why_not": "Pos ini untuk katup searah, sedangkan barang adalah katup gerbang." } ],
        "citations": [ { "type": "hs_code", "ref": "8481", "quote": "(kutipan uraian pos)" }, { "type": "note", "ref": "Bab 84 Catatan 2", "quote": "(kutipan catatan)" } ],
        "decided_by": "agent", "status": "proposed"
      },
      "lartas": [
        {
          "rule_id": "lr07...", "permit_name": "(nama izin sesuai INSW)", "issuing_agency": "(instansi)",
          "stage": "border", "requires_surveyor": false, "regulation_number": "(nomor aturan)",
          "retrieved_at": "2026-11-02"
        }
      ],
      "duty": {
        "currency": "USD", "cif_value": "4857.89", "exchange_rate": "16250.0000", "cif_idr": "78940712.50",
        "bm_rate": 5.0, "bm_amount": "3948000.00",
        "import_value": "82888712.50",
        "ppn_rate_effective": 11.0, "ppn_amount": "9118000.00",
        "pph22_rate": 2.5, "pph22_basis": "with_api", "pph22_amount": "2073000.00",
        "total_amount": "15139000.00",
        "warnings": [ "Nilai asuransi belum diisi, dihitung 0." ]
      },
      "open_clarification_id": null,
      "open_review_id": null
    }
  ]
}
```

Angka dan kode HS di contoh ini hanya ilustrasi bentuk data, bukan klasifikasi atau tarif yang benar. Nilai sebenarnya berasal dari data BTKI dan INSW yang di-seed.

### POST /clarifications/{id}/answer

```json
// Request
{ "answer": "Baja tahan karat" }

// 200 OK
{ "data": { "id": "cq01...", "status": "answered", "resumed_run_id": "8b2f..." } }
```

Setelah semua pertanyaan terbuka di run itu dijawab, backend membuat job `resume_run` dan run berlanjut dari titik jeda (checkpoint LangGraph).

### POST /reviews/{id}/decision

```json
// Request: setujui
{ "action": "approve", "note": "Sesuai spesifikasi pemasok." }

// Request: ganti kode
{ "action": "modify", "hs_code": "84818063", "note": "Badan katup dari baja, bukan besi cor." }

// Request: tolak (barang perlu data tambahan)
{ "action": "reject", "note": "Minta datasheet ke pemasok." }

// 200 OK
{ "data": { "id": "rv01...", "status": "modified", "new_classification_version": 2, "recalc_run_id": "9c11..." } }
```

Aturan: `hs_code` wajib untuk `modify` dan harus ada di `hs_codes`. `note` wajib untuk `modify` dan `reject`. Keputusan `approve` dan `modify` disimpan ke `classification_memory`. Setelah keputusan, job `reanalyze_item` dijalankan dengan mode tanpa klasifikasi ulang, hanya menghitung ulang lartas, pungutan, checklist, dan risiko.

### GET /shipments/{id}/duties

```json
{
  "data": {
    "exchange_rate": { "currency": "USD", "rate_idr": "16250.0000", "valid_from": "2026-11-04", "valid_to": "2026-11-10", "source": "Kurs Menteri Keuangan" },
    "items": [ { "item_id": "it01...", "line_no": 1, "hs_code": "84818099", "...": "field sama dengan objek duty di atas" } ],
    "totals": { "cif_idr": "315250000.00", "bm_amount": "15622000.00", "ppn_amount": "36396000.00", "pph22_amount": "8272000.00", "total_amount": "60290000.00" },
    "is_estimate": true
  }
}
```

### GET /shipments/{id}/checklist

```json
{
  "data": [
    { "id": "ck01...", "item_id": null, "requirement_code": "INVOICE", "label": "Commercial invoice", "reason": "Wajib untuk setiap kiriman.", "status": "provided", "source": "rule", "document_id": "d71a..." },
    { "id": "ck05...", "item_id": "it03...", "requirement_code": "PERMIT:(kode izin)", "label": "(nama izin)", "reason": "Barang baris 3 kena lartas tahap border.", "status": "missing", "source": "lartas", "document_id": null },
    { "id": "ck06...", "item_id": null, "requirement_code": "INSURANCE_VALUE", "label": "Bukti nilai asuransi", "reason": "Incoterm FOB dan nilai asuransi kosong.", "status": "missing", "source": "rule", "document_id": null }
  ]
}
```

### GET /shipments/{id}/pib-draft

```json
{
  "data": {
    "version": 1, "status": "ready", "created_at": "2026-11-05T02:20:00Z",
    "payload": {
      "header": {
        "importer_name": "PT Mitra Kemas Nusantara", "importer_has_api": true,
        "supplier_name": "Zhejiang Valve Industrial Co.", "origin_country": "CN",
        "port_of_loading": "Ningbo", "port_of_entry": "Tanjung Priok", "transport_mode": "sea",
        "incoterm": "FOB", "currency": "USD", "exchange_rate": "16250.0000",
        "fob_value": "18450.00", "freight_value": "950.00", "insurance_value": "0.00", "cif_value": "19400.00"
      },
      "items": [
        { "seq": 1, "hs_code": "84818099", "description": "Gate valve DN50 PN16, cast iron body", "quantity": "120.000", "unit": "PCS",
          "origin_country": "CN", "cif_value": "4857.89", "bm_rate": 5.0, "bm_amount": "3948000.00",
          "ppn_amount": "9118000.00", "pph22_amount": "2073000.00", "permits": [] }
      ],
      "totals": { "bm_amount": "15622000.00", "ppn_amount": "36396000.00", "pph22_amount": "8272000.00", "total_amount": "60290000.00" },
      "blocking_issues": []
    }
  }
}
```

`blocking_issues` berisi alasan draf belum siap, misalnya `[{"code":"OPEN_REVIEW","message":"Masih ada 1 review terbuka."}]`.

### POST /regulations

```json
// Request
{
  "number": "Permendag 99/2026 (SIMULASI)",
  "title": "Simulasi: kewajiban persetujuan impor untuk katup industri",
  "issuer": "Kementerian Perdagangan",
  "summary": "Katup industri pos 8481 wajib persetujuan impor sebelum masuk.",
  "effective_date": "2026-11-06",
  "is_simulated": true,
  "lartas_rules": [
    { "hs_prefix": "8481", "permit_name": "Persetujuan Impor (simulasi)", "permit_code": "PI-SIM-01",
      "issuing_agency": "Kementerian Perdagangan", "stage": "border", "requires_surveyor": false }
  ]
}

// 201 Created
{ "data": { "id": "rg09...", "watch_run_id": "aa71..." } }
```

`POST /regulations/simulate-demo` tidak menerima body. Endpoint ini menerbitkan aturan simulasi bawaan yang sudah disiapkan untuk skenario demo, lalu mengembalikan format respons yang sama. Setiap aturan simulasi wajib berlabel "SIMULASI" di nomor dan judulnya agar tidak disangka aturan sungguhan.

### GET /regulations/{id}/impacts

```json
{
  "data": {
    "regulation": { "id": "rg09...", "number": "Permendag 99/2026 (SIMULASI)", "effective_date": "2026-11-06" },
    "affected_shipments": [
      {
        "shipment_id": "3c9e...", "ref_no": "MKN-IMP-2611-007", "eta": "2026-11-20", "status_before": "ready", "status_after": "needs_review",
        "items": [ { "item_id": "it01...", "line_no": 1, "hs_code": "84818099", "impact_type": "new_permit", "permit_name": "Persetujuan Impor (simulasi)" } ]
      }
    ],
    "unaffected_count": 4
  }
}
```

### GET /dashboard/summary

```json
{
  "data": {
    "active_shipments": 6, "needs_clarification": 1, "needs_review": 2, "ready": 2,
    "affected_by_new_rules": 1, "estimated_duties_idr": "184500000.00",
    "avg_analysis_seconds": 74.2,
    "recent_runs": [ { "run_id": "8b2f...", "shipment_ref": "MKN-IMP-2611-007", "status": "succeeded", "finished_at": "2026-11-05T02:20:00Z" } ]
  }
}
```

### GET /health

```json
{ "status": "ok", "db": "ok", "worker_last_heartbeat": "2026-11-05T02:21:30Z", "version": "1.0.0" }
```

Worker memeriksa tabel jobs setiap 2 detik dengan application\_name imporjaga-worker, dan endpoint ini membaca waktu query terakhir worker dari pg\_stat\_activity (detail di tab Infrastruktur & keamanan). `status` bernilai `degraded` bila heartbeat lebih lama dari 2 menit.

## Event SSE jejak agent

Endpoint `GET /runs/{id}/stream?token=...&after_seq=0` mengirim langkah agent secara langsung. Backend membaca tabel `agent_steps` setiap 700 milidetik untuk baris dengan `seq` lebih besar dari yang terakhir dikirim, lalu mengirimkannya. Header respons: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`.

| Event | Kapan | Isi `data` |
| --- | --- | --- |
| `step` | Setiap baris baru di `agent_steps` | Objek langkah (lihat contoh) |
| `run_status` | Status run berubah | `{ "run_id", "status", "shipment_status" }` |
| `heartbeat` | Setiap 15 detik bila tidak ada event lain | `{ "ts" }`, menjaga koneksi tetap hidup |
| `end` | Run selesai, gagal, dibatalkan, atau berhenti menunggu jawaban | `{ "run_id", "status" }`, lalu server menutup stream |

Contoh aliran event:

```
id: 14
event: step
data: {"run_id":"8b2f...","seq":14,"step_type":"tool_call","node":"classify_item","tool_name":"search_hs_candidates","item_id":"it01...","title":"Mencari kandidat kode HS untuk baris 1","detail":"Kata kunci: gate valve besi cor DN50","status":"ok","duration_ms":null,"created_at":"2026-11-05T02:14:03Z"}

id: 15
event: step
data: {"run_id":"8b2f...","seq":15,"step_type":"tool_result","node":"classify_item","tool_name":"search_hs_candidates","item_id":"it01...","title":"Ditemukan 10 kandidat, teratas pos 8481","detail":null,"status":"ok","duration_ms":412,"created_at":"2026-11-05T02:14:04Z"}

id: 16
event: step
data: {"run_id":"8b2f...","seq":16,"step_type":"fallback","node":"classify_item","tool_name":null,"item_id":"it01...","title":"Model utama kena rate limit, pindah ke model cadangan","detail":null,"status":"warning","duration_ms":null,"created_at":"2026-11-05T02:14:09Z"}

event: run_status
data: {"run_id":"8b2f...","status":"paused","shipment_status":"needs_clarification"}

event: end
data: {"run_id":"8b2f...","status":"paused"}
```

Aturan untuk frontend:

- Saat halaman dibuka, ambil dulu `GET /runs/{id}/steps` untuk menampilkan langkah lama, lalu buka stream dengan `after_seq` sama dengan `seq` terakhir.
- Kalau koneksi putus, `EventSource` otomatis menyambung ulang dan mengirim header `Last-Event-ID`. Backend memakai nilai itu sebagai `after_seq`, jadi tidak ada langkah yang terlewat atau dobel.
- Isi `title` selalu kalimat bahasa Indonesia yang siap ditampilkan. `payload` lengkap (argumen dan hasil tool) tidak dikirim lewat SSE, tetapi bisa dibuka lewat `GET /runs/{id}/steps?include_payload=true` untuk panel detail.
- Caddy harus meneruskan stream tanpa buffering. Konfigurasinya ada di tab Infrastruktur & keamanan.
