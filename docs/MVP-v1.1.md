# ImporJaga — keputusan dan revisi spesifikasi MVP v1.1

Tanggal: 4 November 2026, WIB.

Dokumen ini mengganti ketentuan yang bertentangan pada 11 tab [artifact sumber](https://claude.ai/artifact/JYUvHx68Z9Z6AYHanNY7S8). Bagian sumber yang tidak diubah tetap berlaku. Ini adalah revisi spesifikasi untuk implementasi; kode aplikasi, VPS, dan artifact sumber belum diubah. Kontrol edit artifact tidak tersedia pada sesi yang diperiksa.

Tujuan MVP: juri dapat mengalami satu kiriman dari invoice sampai draf siap ditinjau/diajukan, melihat alasan dan bukti setiap keputusan, lalu melihat sistem bereaksi terhadap aturan simulasi. Keberhasilan dinilai dari perilaku yang berjalan dan hasil uji yang dapat ditelusuri.

## Keputusan yang dikunci

| ID | Keputusan final | Tab terdampak |
|---|---|---|
| D01 | Satu pengguna mempunyai tepat satu perusahaan; semua peran, termasuk admin, hanya mengakses perusahaan itu | PRD, Database, API, Frontend, Model bisnis, Infrastruktur |
| D02 | Target minimum HS6 top-1 80%, HS8 top-1 65%, HS8 top-3 85%; target lanjutan masing-masing 85%, 70%, 90% | PRD, Data & seed, QA, Audit |
| D03 | Login: batas request per IP dan pembatasan kegagalan per akun adalah dua kontrol berbeda, didefinisikan di bawah | PRD, API, Infrastruktur, QA |
| D04 | Proses barang yang dapat dikerjakan sampai selesai; pertanyaan tertunda disimpan sebagai data, bukan interrupt seluruh kiriman | PRD, Agent & AI, API, Database, Frontend, QA |
| D05 | Semua kewajiban lartas yang berlaku digabung; prefiks terpanjang hanya menyelesaikan variasi dalam satu kelompok aturan yang sudah dikurasi | Database, Agent & AI, Data & seed, QA |
| D06 | Status siap hanya berasal dari satu fungsi readiness deterministik; pending bukan terpenuhi; penolakan reviewer bukan persetujuan | PRD, Agent & AI, API, Database, Frontend, QA |
| D07 | Persetujuan HS dan kelengkapan kepatuhan dipisah; perubahan aturan tidak otomatis membatalkan pilihan HS yang benar | Agent & AI, Database, Frontend |
| D08 | Replay pekerjaan tidak menggandakan job, review, email, atau hasil aktif | Arsitektur, Database, Agent & AI, Infrastruktur, QA |
| D09 | Demo utama memakai satu perusahaan, live LLM, data contoh berlabel, SMTP nyata ke inbox tim, serta unggahan datasheet sebagai jalur P0 | Semua tab demo |
| D10 | Klaim hasil, regulasi, dan rubrik harus dibuktikan; dokumen ini tidak mengesahkan klaim hukum atau menjamin kemenangan | Data & seed, QA, Model bisnis, Audit |

## 1. PRD — ruang lingkup, status, dan penerimaan

### Satu perusahaan per pengguna

- `users.company_id` wajib, tepat satu. Perusahaan ditentukan server dari identitas pengguna aktif; field perusahaan tidak dapat diganti di request kiriman.
- Staf mengelola kiriman perusahaan sendiri; reviewer adalah ahli yang ditugaskan ke perusahaan itu; admin adalah admin perusahaan, bukan superadmin lintas perusahaan.
- Login staf/reviewer/admin demo mengakses PT Mitra Kemas Nusantara yang sama. Perusahaan kedua hanya fixture tes isolasi dan contoh opsional dengan akun terpisah.
- Hilangkan dropdown pemilihan perusahaan pada wizard. Tampilkan nama perusahaan sebagai teks tetap.
- Data referensi resmi dibaca bersama. Aturan simulasi, dampak, reset, email, job, dan memori terisolasi per perusahaan.
- Untuk MVP, pengguna disediakan lewat seed. Manajemen pengguna lengkap, pergantian perusahaan, membership multi-klien, dan billing ditunda.

### Prioritas MVP

P0: login tiga peran, invoice PDF berteks, ekstraksi, klasifikasi dan sumber, klarifikasi per barang, pencarian HS dasar, lartas dengan status cakupan data, pungutan deterministik, readiness, review, draf PIB layar, trace langsung, rencana agent, pemeriksaan konsistensi, SMTP ke inbox tim, satu pengingat, unggah datasheet yang memicu proses lanjutan, simulasi aturan, memori keputusan manusia, notifikasi aplikasi, mode assist/auto, demo yang dapat direset dan dievaluasi.

P1 setelah P0 stabil: vision untuk JPG/PNG/PDF scan, inbox IMAP, ekspor PDF, email notifikasi pengguna, dan contoh perusahaan kosmetik. Pemindahan vision dari P0 adalah keputusan ruang lingkup v1.1: bila belum aktif, UI menjelaskan bahwa versi ini membutuhkan PDF berteks, menolak format yang belum didukung dengan pesan 415, dan mendeteksi scan tanpa menghasilkan hasil palsu. Batas upload P0 tetap 10 MB/file, 5 file/kiriman, maksimum 20 halaman PDF.

Cakupan pencarian tetap empat kelompok dalam lima bab (33, 61, 62, 84, 85). Barang nyata yang ternyata di luar cakupan tidak dipaksa masuk bab terdekat. Integrasi CEISA, pengajuan PIB, multi-klien, pembayaran, dan seluruh bab BTKI adalah roadmap.

### Readiness tunggal

Tambahkan `shipments.readiness_status = incomplete | blocked | ready`, dihitung oleh `evaluate_readiness(shipment_id)`; hasilnya dipakai API, draf PIB, dan UI. `ready` berarti siap menurut pemeriksaan prototipe, bukan pengesahan hukum.

Fungsi mengembalikan `ready`, `blocking_issues[]`, `warnings[]`, dan hitungan item/dokumen. Ready hanya jika:

1. Semua item mempunyai keputusan klasifikasi yang diterima sesuai kebijakan assist/auto; tidak ada item out_of_scope atau keputusan rejected yang belum diganti.
2. Tidak ada pertanyaan yang masih memengaruhi klasifikasi/kepatuhan; pertanyaan yang tidak relevan lagi dibatalkan dengan alasan.
3. Tidak ada review terbuka dan semua temuan wajib sudah diselesaikan dengan bukti. Reviewer tidak dapat menghilangkan kewajiban izin hanya dengan menekan Setujui.
4. Dokumen yang menjadi prasyarat pengajuan berstatus `provided` dan mempunyai bukti terhubung. `missing` dan `pending` sama-sama menghalangi. `not_needed` hanya diperbolehkan jika aturan deterministik menyatakan tidak wajib dan alasannya disimpan.
5. Cakupan lartas telah diperiksa, kurs tersedia untuk tanggal perhitungan, dan tidak ada data referensi kritis yang belum diverifikasi/konflik.
6. Perhitungan terbaru sesuai versi item, pilihan HS, dan data referensi; tidak ada pekerjaan analisis tertunda atau berjalan.

`incomplete`: ada data/pertanyaan/dokumen yang belum lengkap. `blocked`: ada penolakan, di luar cakupan, konflik data, atau review yang wajib. Bila keduanya ada, `blocked` menjadi ringkasan; seluruh sebab tetap ditampilkan. Risiko rendah/sedang/tinggi bukan pengganti readiness.

### Status kiriman yang konsisten

Tambahkan `needs_documents` untuk kiriman yang tinggal menunggu dokumen. Untuk kiriman belum diajukan, proyeksi status berurutan: pekerjaan aktif → `analyzing`; kegagalan teknis tak pulih → `failed`; pertanyaan terbuka → `needs_clarification`; temuan/review wajib → `needs_review`; kekurangan dokumen → `needs_documents`; semua syarat lolos → `ready`. `draft` hanya sebelum analisis pertama. Semua alasan paralel ditampilkan, walau badge utama hanya satu.

`submitted` dan `arrived` adalah fakta operasional, bukan hasil analisis. Kiriman submitted tetap submitted saat aturan berubah; tampilkan badge tambahan “Perlu tindakan — perubahan aturan” dari readiness dan dampaknya. Run analisis punya status sendiri. Arrived tidak dianalisis otomatis oleh watcher.

`mark-submitted` memeriksa readiness dan ketiadaan pekerjaan aktif secara atomik sebelum mencatat `submitted_at`. Dokumen kurang yang sedang diminta ke pemasok belum membuat kiriman siap. `mark-arrived` hanya dari submitted. Keputusan review mengantrekan evaluasi ulang, tidak langsung menetapkan ready.

### Acceptance criteria pengganti

- US-07: pertanyaan salah satu barang tidak menghalangi hasil barang lain; jawaban memicu pekerjaan baru untuk barang terkait tanpa menunggu seluruh pertanyaan dijawab.
- US-10: approve/modify/reject menghasilkan audit; hanya approve/modify yang menjadi memori. Reject tetap menghalangi readiness sampai ada revisi dan keputusan baru.
- US-11: tombol pengajuan nonaktif selama `blocking_issues` tidak kosong; termasuk dokumen pending.
- US-15: permintaan pemasok dibuat setelah semua kekurangan pada pass itu dikumpulkan; hanya satu pesan per permintaan gabungan dan satu pengingat yang dijadwalkan.
- US-18: unggahan datasheet atau jawaban memicu proses otomatis; IMAP adalah jalur tambahan P1, bukan syarat demo P0.

## 2. Arsitektur & tech stack — proses singkat dan dapat dilanjutkan

Stack inti tetap Next.js, FastAPI, LangGraph, PostgreSQL/pgvector, worker, SSE, dan gateway model kompatibel OpenAI. Gunakan versi paket yang dipin setelah diuji bersama.

Untuk MVP, gunakan satu worker eksekusi dan satu scheduler; pemrosesan item di dalam run maksimal tiga paralel. PostgreSQL jobs tetap menjadi antrean. `SKIP LOCKED` cocok untuk pengambilan pekerjaan antrean, tetapi tidak menggantikan penguncian kiriman atau deduplikasi. [PostgreSQL SELECT](https://www.postgresql.org/docs/16/sql-select.html).

Setiap run adalah satu pass yang mengerjakan semua pekerjaan yang tersedia, menyimpan hasil, lalu berakhir. Menunggu manusia/pemasok disimpan di tabel klarifikasi, dokumen, dan checklist. Event berikutnya membuat run baru yang terhubung lewat `parent_run_id`. Checkpoint LangGraph dipakai untuk pemulihan run yang terputus, dengan `thread_id = run_id`, bukan untuk menahan satu run sepanjang umur kiriman. Pemisahan state per thread dan data lintas run sesuai kemampuan persistence LangGraph. [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence).

Keputusan ini mengganti node `wait_for_answers`, job `resume_run` untuk jawaban manusia, serta kontrak yang mengharuskan semua pertanyaan dijawab dahulu. Enum paused boleh dipertahankan sebagai reserved untuk migrasi, tetapi tidak dihasilkan alur klarifikasi MVP.

API menyimpan event dan job dalam transaksi yang sama. Event yang datang saat run aktif tidak dibuang: dicatat sebagai job tertunda dan digabung selama debounce 10 detik. Run baru baru dibuat ketika dispatcher mendapat kunci kiriman. Pada akhirnya hanya satu run queued/running per kiriman; pekerjaan tertunda tetap terlihat di UI.

## 3. Database — perubahan skema yang diperlukan

Angka 25 tabel adalah baseline dokumen awal, bukan batas desain. Jangan mempertahankan klaim jumlah tabel setelah migrasi mengubahnya. Perubahan berikut menjadi migrasi v1.1; bukan skrip yang langsung dijalankan ke VPS.

| Entitas | Perubahan |
|---|---|
| shipments | Tambah `readiness_status`, `submitted_at`, `arrived_at`, `input_version`; tambahkan enum needs_documents |
| agent_runs | Tambah `parent_run_id`, `input_version`, `mode`, `target_item_ids`, `outcome` (complete / waiting_external / action_required); succeeded berarti pass sukses, bukan kiriman ready |
| jobs | Tambah `dedupe_key` unik, `heartbeat_at`, `lease_expires_at`; simpan company_id dan event/version pada payload atau kolom yang dapat divalidasi |
| messages | Tambah `dedupe_key` unik, `provider_message_id`, `sent_at`, `delivery_status` termasuk unknown; jangan menganggap SMTP accepted sebagai bukti dibaca/diterima inbox |
| clarifications | Tambah `attribute`, `reason`, `answer_source`, `answered_message_id`, `answer_version`, `resolution_evidence`; reviewer/manual answer boleh tanpa message_id |
| review_tasks | Tambah `review_type` classification/compliance dan versi sumber; reject memblokir, review lama dapat superseded setelah input berubah |
| checklist_items | Tambah `required_before_submission`, `resolution_reason`; unik walau item_id NULL; verifikasi bukti sebelum provided |
| regulations | Tambah company_id untuk simulasi; referensi resmi company_id NULL; endpoint admin perusahaan hanya membuat simulasi untuk perusahaan sendiri |
| lartas_rules | Tambah `requirement_key`, `rule_group`, `supersedes_rule_id`, applicability yang dikurasi; bukan diputuskan model |
| hs_codes | Tambah `lartas_coverage = verified_rules | verified_none | unknown`, tanggal pemeriksaan dan sumber; nilai unknown adalah bawaan |
| classification_memory | Tambah is_active/superseded_by untuk keputusan yang sudah digantikan; sumber harus keputusan manusia |

Kunci minimum: satu review terbuka per item + jenis + versi; satu pungutan is_current per item; satu job per event/version; satu email per permintaan; satu klasifikasi current per item. Tambahkan pemeriksaan hubungan perusahaan pada FK turunan melalui service, termasuk run, message, file, dan memori.

Contoh indeks untuk migrasi, sesudah audit duplikat dan penyesuaian constraint lama:

```sql
CREATE UNIQUE INDEX uq_active_shipment_run ON agent_runs (shipment_id)
  WHERE shipment_id IS NOT NULL AND status IN ('queued', 'running');
CREATE UNIQUE INDEX uq_current_duty ON duty_calculations (item_id)
  WHERE is_current;
CREATE UNIQUE INDEX uq_checklist_requirement
  ON checklist_items (shipment_id, item_id, requirement_code) NULLS NOT DISTINCT;
```

PostgreSQL secara default memperlakukan NULL berbeda pada indeks unik; karena itu constraint awal checklist dengan item_id NULL belum mencegah duplikat dokumen tingkat kiriman. [PostgreSQL 16 unique indexes](https://www.postgresql.org/docs/16/indexes-unique.html).

## 4. API — kontrak pengganti

Pertahankan base /api/v1, envelope, uang string desimal, JWT terpisah untuk SSE, dan pemfilteran perusahaan. Regenerasi tipe frontend dari OpenAPI setelah perubahan ini.

| Endpoint/kontrak | Perilaku final |
|---|---|
| POST /auth/login | Request limiter 30/menit/IP untuk semua percobaan; 5 password salah/10 menit per akun memicu cooldown 60 detik, reset jendela setelah cooldown; respons 429 + Retry-After. Akun tidak dikenal diperlakukan sama; sukses menghapus counter kegagalan akun. Tidak ada penguncian permanen |
| Semua rate limiter | Counter disimpan bersama di Postgres untuk seluruh proses API; tambahkan tabel auth_throttle/limiter sederhana. IP hanya dari proxy tepercaya, bukan header bebas |
| POST /shipments | Company berasal dari user; tolak company_id di body. supplier_email untuk demo hanya alamat inbox tim yang terdaftar |
| Upload dokumen | Invoice pertama memicu analisis. Dokumen baru pada kiriman aktif yang belum arrived memicu event berisi document_id, versi input, dan item terkait. Debounce tidak menunda penyimpanan file |
| POST /clarifications/{id}/answer | Simpan jawaban per pertanyaan, naikkan versi input, antrekan subset; respons 202 dengan question_id, job_id, next_run_id nullable, processing_status. Hapus field resumed_run_id |
| POST /shipments/{id}/analyze | Manual tanpa perubahan ketika run aktif menjawab 409 + run_id. Retry request ber-Idempotency-Key yang sama mengembalikan hasil pertama. Event otomatis tidak menjawab 409 ke pengguna; diantrekan |
| GET /shipments/{id} | Tambah readiness_status, blocking_issues, warnings, active_run_id, pending_job_count, input_version, waiting_counts per pihak, submitted_at |
| GET /runs/{id} dan SSE run_status/end | Tambah outcome dan readiness_status; end hanya menutup pass. Frontend memantau kiriman untuk run berikutnya ketika masih ada pertanyaan/job |
| GET /items/{id} | Bedakan status keputusan klasifikasi, risiko kepatuhan, coverage lartas, serta versi input/referensi |
| POST /reviews/{id}/decision | Approve/modify menyelesaikan review klasifikasi, mencatat manusia, membuat recalc. Reject membuat action_required + permintaan data dan tidak memanggil jalur persetujuan |
| POST /items/{id}/compliance-verification | Reviewer/admin mencatat hasil pemeriksaan manual untuk versi item dan tanggal tertentu: sumber, checked_at, aturan/izin relevan, dan bukti. Tidak mengubah referensi global atau menghapus kewajiban; coverage unknown hanya terselesaikan bila bukti pemeriksaan lengkap |
| PATCH /items/{id} | Tolak perubahan ketika run memakai versi yang sama, atau simpan versi baru dan jadwalkan subset; MVP memilih 409 saat run aktif agar implementasi sederhana. Perubahan relevan membatalkan penerapan persetujuan HS lama secara eksplisit |
| PATCH /checklist/{id} | Verifikasi akses, bukti file, dan jenis persyaratan; model tidak dapat menghapus persyaratan wajib |
| POST /shipments/{id}/mark-submitted | Transaksi dengan lock kiriman, evaluasi readiness terbaru dan pending jobs; 409 beserta blocking_issues jika belum siap |
| POST /regulations/simulate-demo | Idempoten per company + seed scenario; memengaruhi perusahaan sendiri; effective_date menggunakan tanggal demo hari ini |
| POST /admin/demo/reset | Hanya seed milik perusahaan pengguna; ditolak jika ada pekerjaan aktif atau dijadwalkan setelah idle. Tidak menghapus pekerjaan pengguna lain |
| GET /health | Tambah heartbeat eksplisit dari worker; query_start database bukan heartbeat liveness yang andal |

Kebijakan throttle di atas adalah pilihan MVP, bukan angka yang diwajibkan OWASP. OWASP merekomendasikan kontrol berbasis akun, respons generik, dan mempertimbangkan risiko denial-of-service akibat lockout. Ukur dan sesuaikan jika login juri dari jaringan bersama terganggu. [OWASP Authentication](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html).

## 5. Agent & AI — alur dan keputusan

### Graph analisis final

```text
load_context → extract_pending_documents → extract_or_update_items
→ plan_shipment → classify_actionable_items → verify_consistency
→ check_lartas → calculate_duties → assess_risk_and_checklist
→ resolve_gaps → create_or_update_reviews → draft_pib → finalize_pass
```

- classify_actionable_items melewati item yang menunggu jawaban, tetapi memproses item lain. Maksimal dua pertanyaan per item per versi data, delapan tool call per percobaan. Pencarian dokumen mendahului pertanyaan.
- resolve_gaps tetap berjalan sebelum pass berakhir, sehingga email pemasok benar-benar dapat terkirim. Outcome waiting_external menampilkan apa yang sedang ditunggu.
- Jawaban/unggahan membuat pass items_subset. Ekstraksi ulang invoice tidak boleh membuat baris item ganda; gunakan identitas dokumen dan line_no serta versi.
- Untuk dokumen yang keterkaitannya tidak jelas, simpan sebagai unassigned dan minta staf memilih item. Jangan memperbarui seluruh barang berdasarkan tebakan.
- recalc_only setelah perubahan aturan mengulang kepatuhan/pungutan/checklist/readiness tanpa mengubah kode yang diterima. Jika atribut barang berubah, persetujuan lama ditandai superseded, lalu klasifikasi baru masuk review.
- Klaim “approved tidak pernah disentuh” diganti: pilihan HS yang diterima tetap berlaku selama input relevan tidak berubah; kepatuhan selalu dapat diperiksa ulang.
- Review yang telah diputuskan tidak dibuat ulang hanya karena confidence lama masih rendah. Keputusan berlaku untuk versi item dan temuan yang sama; temuan baru atau perubahan input/referensi yang relevan membuat review versi baru. Risiko historis tetap terlihat bersama mitigasi manusianya.
- Out-of-scope diakhiri tool `report_out_of_scope`, tanpa kode HS palsu, tanpa pungutan lengkap, dengan review. Tambahkan tool ini pada registry dan jumlah tools; jangan lagi mengunci klaim “8 tools” bila registry berubah.
- Lengkapi skema search_shipment_documents dan ask_supplier yang hanya disebut pada tabel sumber. Test registry wajib memastikan semua tools dalam prompt tersedia.

### Assist dan auto

Assist: email menjadi draf; semua usulan HS baru membuat review klasifikasi. Reviewer dapat menyetujui beberapa item yang telah dibaca lewat aksi batch dengan audit per item (opsional P1); endpoint per item tetap P0.

Auto: persetujuan otomatis hanya jika confidence ≥0,85, memori manusia aktif cocok ≥0,92 dengan kode sama, atribut material/fungsi/konstruksi kompatibel, tidak ada kritik pemeriksa, sumber terverifikasi, dan risiko low. Ketiadaan memori tidak sama dengan memori cocok. Semua item lain mendapat review klasifikasi. Persetujuan agent tidak memperbarui memori. Ini mengganti klaim bahwa semua risiko low/medium otomatis siap.

Skor heuristik: tanpa bukti memori yang relevan, confidence = 0,625 × llm_confidence + 0,375 × retrieval_score. Dengan memori relevan, gunakan bobot 0,5/0,3/0,2; konflik memori membentuk temuan eksplisit. UI menyebut “skor keyakinan”, bukan probabilitas benar; validasi lewat set evaluasi.

### Lartas dan data tidak lengkap

Ambil semua aturan yang tanggalnya berlaku dan prefiksnya cocok. Gabungkan kewajiban berbeda (izin, surveyor, instansi, tahap). Urutan prefiks hanya untuk tampilan/spesifisitas; jangan membuang seluruh aturan pendek secara global.

Dalam rule_group yang dikurasi sebagai variasi dari kewajiban yang sama, gunakan aturan lebih spesifik hanya jika hubungan override/supersedes telah diverifikasi dan disimpan. Jika dua kewajiban tidak dapat direkonsiliasi, beri DATA_CONFLICT, tampilkan kedua sumber, dan wajib review. Ini kebijakan konservatif mesin prototipe, bukan interpretasi hukum berdasarkan panjang kode saja.

Tidak ditemukannya baris lartas tidak berarti bebas lartas. `verified_none` dengan sumber/tanggal berarti tidak ditemukan kewajiban dalam cakupan pemeriksaan; `unknown` berarti belum diketahui, blokir ready sampai ahli memverifikasi dan mencatat bukti. Post-border yang tidak wajib sebelum pengajuan tetap muncul sebagai tugas bertenggat; tidak boleh menghilang dari checklist.

Watcher memeriksa seluruh kiriman sudah dianalisis dan belum arrived, termasuk yang ETA-nya terlewat. ETA tidak boleh menjadi alasan mengabaikan kiriman yang masih berjalan. Aturan akan datang menghasilkan peringatan terpisah; aktivasi kewajiban mengikuti effective_date. Demo memakai aturan berlaku hari ini. Submitted tetap submitted.

### Replay, biaya, dan pengiriman email

Simpan niat pengiriman di messages/outbox dan gunakan send_email job. Kunci deduplikasi dibangun dari company, shipment, kumpulan gap dan nomor reminder; retry tidak membuat pesan baru. Checkpoint tidak menjamin efek eksternal exactly-once; operasi sebelum/selama replay harus idempoten. [LangGraph functional API — idempotency](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/functional-api.mdx).

SMTP timeout sesudah server mungkin menerima pesan: tandai delivery_status unknown; jangan kirim ulang membabi buta. Tampilkan “Status pengiriman belum pasti” dan tugas pemeriksaan. Retry otomatis hanya untuk kegagalan yang diketahui terjadi sebelum penerimaan. Jangan menjanjikan exactly-once SMTP.

P0: satu permintaan gabungan per kiriman/pemasok/gap dalam 24 jam, satu reminder setelah jeda yang dikonfigurasi, kemudian tugas staf. FOLLOWUP_DELAY_MINUTES=3 hanya demo dan diberi label jadwal demo dipercepat. Hanya alamat tepat dalam AGENT_EMAIL_ALLOWED_RECIPIENTS milik tim, bukan semua alamat gmail.com. Header, penerima, dan lampiran ditentukan backend.

Terapkan batas token/biaya pada SEMUA trigger, termasuk upload, watcher, followup, review, dan retry. Batas per-run 60.000 token dan batas harian adalah plafon; biaya dicatat per panggilan/model dengan snapshot harga, termasuk fallback/vision. Batasi uang juga, karena token lintas model tidak setara biaya. Bila kuota habis, simpan hasil parsial dan status jelas tanpa otomatis mengulang tanpa batas.

## 6. Frontend — pengalaman juri

Halaman awal sesudah login memuat “Coba alur impor” dengan tiga langkah: 1) analisis invoice, 2) selesaikan pertanyaan/review, 3) lihat dampak aturan. Label peran terlihat. Pergantian peran demo tetap melalui login akun sah dan pemeriksaan backend.

Detail kiriman menampilkan ringkasan tetap: “4/5 barang selesai; 1 menunggu spesifikasi pemasok; 1 dokumen belum tersedia”. Per barang tampil pihak yang perlu bertindak, pertanyaan, hasil sementara, dan next action. Readiness dan status submitted ditampilkan terpisah.

Panel agent menampilkan rencana singkat, tindakan/tool, sumber, hasil, dan pemulihan; jangan menampilkan chain-of-thought internal atau mengisi animasi seolah hasil sudah terjadi. Saat menunggu, tampilkan alasan dan waktu followup, bukan spinner tanpa akhir. Selesai satu pass tidak menutup akses ke hasil parsial.

Sediakan tombol “Unduh contoh invoice” dan “Unduh datasheet contoh” yang berlabel data demo. Unggahan mengikuti pipeline yang sama dengan dokumen lain. Tombol lihat sumber mengarah ke uraian/rule yang benar. Semua hasil mempunyai versi, waktu, sumber, serta penanda agent/manusia.

TanStack Query memantau shipment saat ada pending job/pertanyaan (misalnya 3 detik) dan menghubungkan SSE ke active_run_id baru. SSE deduplikasi berdasarkan run_id + seq. Sertakan tombol retry koneksi tanpa mengulang analisis. Halaman tetap berguna ketika browser ditutup dan dibuka lagi.

## 7. Data & seed — demo yang dapat dibuktikan

Demo utama MKN-011 berisi lima barang yang benar-benar termasuk bab 84/85: mesin sealing, motor, panel kontrol, katup ambigu, dan sensor proximity. Ganti sabuk konveyor karet pada demo utama/memori dengan barang dalam cakupan; jika klasifikasi terverifikasi menunjukkan sabuk berada di luar lima bab, jadikan fixture out-of-scope terpisah. Jangan menentukan kode final sebelum verifikasi data.

Siapkan bukti dokumen yang membuat skenario bisa mencapai ready: invoice, packing list, BL/AWB contoh, nilai asuransi lengkap, dan setiap izin yang memang diwajibkan referensi demo. Sebagian boleh sudah diunggah dan dilabeli seed. Datasheet katup sengaja belum tersedia. Keputusan HS seed/memori harus berlabel keputusan fiktif untuk data demo, bukan keluaran run live.

MKN-007 ready H+5 dan MKN-008 submitted H+14 terkena aturan simulasi pos 8481 yang efektif hari ini; MKN-003 arrived tidak terkena. Tombol simulasi berulang mengembalikan event yang sama. Tambahkan tes kiriman terlambat yang belum arrived tetap diperiksa. Reset menghitung tanggal relatif terhadap WIB saat reset.

### Evaluasi yang sama di semua tab

| Metrik | Target minimum MVP | Target lanjutan |
|---|---:|---:|
| HS6 top-1 | ≥80% | ≥85% |
| HS8 top-1 | ≥65% | ≥70% |
| HS8 top-3 | ≥85% | ≥90% |
| Retrieval recall@10 | ≥90% | Diukur per bab |
| Klarifikasi tepat pada 15 item sulit | ≥80% | Laporkan numerator/denominator |
| Pertanyaan tak perlu pada 20 item mudah | <10% | Laporkan hitungan |
| Lartas pada fixture berlabel + kode benar | Semua kewajiban cocok | Tidak digeneralisasi ke seluruh INSW |
| Watcher fixture 007/008/003 | 2 terdeteksi, 1 arrived diabaikan | Semua alasan dapat ditelusuri |
| Alur demo live penuh | 5 kali berturut-turut selesai tanpa kegagalan tak tertangani | Laporkan waktu dan biaya |

Tetap 60 item, 12/bab: 4 mudah, 5 sedang, 3 sulit. Pisahkan data pengembangan prompt dari 60 item evaluasi final. Bekukan dataset dan prompt sebelum uji final; simpan hash dataset, commit, model, tanggal, serta konfigurasi. Memori demo dimatikan untuk evaluasi utama. Laporkan first-pass sebelum jawaban dan final setelah jawaban baku secara terpisah; abstain/tidak selesai dihitung gagal pada akurasi keseluruhan, bukan dibuang dari denominator. Alternatif top-3 harus unik dan tervalidasi; acceptable_hs8 tidak menaikkan strict top-1.

Bandingkan retrieval-only dengan agent pada input/versi referensi yang sama. Jangan memberi jawaban klarifikasi ke satu metode saja lalu mengklaim perbandingan setara; pisahkan baseline awal dan baseline setelah atribut lengkap. Uji pipeline agent yang gagal dengan fake model adalah tes, bukan bukti akurasi live.

Target performa rekayasa tetap analisis 8 item tanpa menunggu eksternal ≤120 detik, daftar/detail ≤2 detik, trace ≤2 detik setelah langkah dicatat. Catat kondisi warm/cold, jumlah run, median dan p95; waktu menunggu manusia/email dilaporkan terpisah dari compute. Target belum tercapai tetap dilaporkan apa adanya.

## 8. Infrastruktur & keamanan — stabil saat dicoba

Sesuaikan deployment dengan layanan VPS yang benar-benar sudah berjalan. Jangan menyalin binding port 5432/80/443 atau memasang Caddy kedua jika sudah dipakai. Periksa resource, pakai service/network terpisah, dan arahkan reverse proxy yang ada. Tidak ada perubahan server dilakukan oleh revisi ini.

Default MVP satu proses API dan satu worker sampai pengukuran RAM membuktikan aman; embedding dimuat dengan cache model. Gunakan heartbeat eksplisit worker setiap 15 detik dan lease job yang diperpanjang; lease stale direbut dengan pemeriksaan atomik. Scheduler tunggal memakai kunci dedupe agar jadwal tidak ganda setelah restart.

Reset demo tidak berjalan saat juri aktif atau ada pekerjaan/pengiriman email berlangsung. Reset otomatis midnight ditunda sampai idle, dengan penanda dan cooldown. Reset berulang tidak boleh mengirim ulang email lama. Untuk MVP shared demo, tampilkan aktivitas sesi lain dan cegah reset selama demo sedang berjalan; sandbox per juri adalah pengembangan berikutnya, bukan perluasan multi-company pada akun.

Semua file, SSE, job, pesan, dan memori tetap dicek company_id. Nonaktifkan token pengguna nonaktif walau JWT belum expired. Batasi CORS, redact token stream dari access log, dan jangan menyimpan prompt/data mentah sensitif di trace publik. Allowlist penerima SMTP tidak dapat diubah melalui akun admin demo publik.

Rate limiter dan heartbeat adalah data operasional; reset demo tidak menghapusnya. Ingest referensi global hanya operator deployment; admin perusahaan tidak dapat mengganti data resmi perusahaan lain.

## 9. Rencana kerja & QA — rilis berdasarkan bukti

Karena tanggal revisi 4 November, jadwal lama 1–3 November tidak dianggap sudah selesai. Lakukan inventory implementasi aktual dahulu, lalu jalankan milestone berikut sampai tenggat sumber 10 November; jadwal resmi perlu dicocokkan dengan guidebook terbaru.

| Urutan | Hasil wajib sebelum berpindah |
|---|---|
| 1 | Kontrak v1.1, migrasi, isolasi perusahaan, readiness, data demo dan fixture perhitungan konsisten |
| 2 | Satu alur PDF → ekstraksi → retrieval → klasifikasi live → hasil → SSE berjalan online |
| 3 | Klarifikasi per item, review, subset otomatis, SMTP/followup dan memori berjalan tanpa duplikasi |
| 4 | Watcher, before/after, frontend demo mandiri, reset aman dan pemulihan kegagalan |
| 5 | Evaluasi final, lima uji demo, proposal/video berdasarkan hasil, freeze dan uji link publik |

P1 hanya mulai setelah urutan 1–4 lolos. Jika waktu menyempit, potong IMAP, vision, PDF export, lalu dekorasi UI. Jangan memotong readiness, sumber, isolasi, trace, dan bukti evaluasi untuk mengejar fitur tambahan.

### Tes penerimaan wajib

| ID | Skenario | Hasil yang harus terlihat |
|---|---|---|
| A01 | Akun perusahaan A menebak ID milik B | Semua resource termasuk file, stream, pesan, dan memori menjawab 404 |
| A02 | Dua barang butuh jawaban, tiga lengkap | Tiga hasil tersedia, permintaan tersimpan/terkirim, run selesai waiting_external |
| A03 | Jawab satu dari dua pertanyaan | Hanya item terkait diproses, pertanyaan kedua tetap terbuka |
| A04 | Upload/answer ganda atau bersamaan | Satu hasil per event/version; tidak ada run paralel kiriman yang sama |
| A05 | Worker mati sesudah tulis hasil sebelum selesai | Recovery melanjutkan tanpa review/job/email ganda |
| A06 | Dokumen wajib pending, review sudah disetujui | Readiness tetap incomplete; mark-submitted 409 |
| A07 | Reviewer reject item terakhir | Tidak pernah ready; permintaan data dan blocker terlihat |
| A08 | HS 8481 cocok izin A; 848180 cocok izin B | Keduanya tampil jika kewajiban berbeda; konflik tidak disembunyikan |
| A09 | Tidak ada baris lartas, coverage unknown | UI “belum diverifikasi”, bukan “bebas lartas”; ready terblokir |
| A10 | Aturan baru mengenai item yang HS-nya approved | Kode tetap, checklist/risiko berubah; submitted tetap submitted |
| A11 | Confidence tinggi tetapi memori tidak cocok | Auto tidak menyetujui; review tersedia |
| A12 | Assist, lalu auto pada data yang memenuhi syarat | Assist menghasilkan draf/review; auto beraksi sesuai aturan; audit membedakan asal |
| A13 | SMTP hasil tidak pasti | Pesan unknown, tidak dikirim ulang otomatis secara membabi buta |
| A14 | Refresh saat run berjalan/selesai, SSE putus | Langkah tidak hilang/ganda; run lanjutan muncul tanpa refresh manual |
| A15 | Kuota habis pada upload/watcher/followup | Semua trigger berhenti terkontrol, bukan hanya tombol analyze |
| A16 | Klik simulasi dua kali dan reset saat run aktif | Tidak ada dampak ganda; reset ditolak/ditunda |
| A17 | Lima gagal login lalu percobaan berikutnya | 429 + Retry-After, pulih setelah cooldown; IP shared di bawah batas tetap dapat login akun lain |
| A18 | Dokumen/email mengandung instruksi palsu | Tidak mengubah penerima, role, readiness, atau izin wajib |

Perjelas test_duty: angka contoh per item di API konsisten jika urutan pembulatannya dikunci. CIF Rp78.940.712,50 × 5% dibulatkan ke atas ribuan menghasilkan BM Rp3.948.000. Jika nilai impor memakai BM yang sudah dibulatkan, nilainya Rp82.888.712,50; 11% dibulatkan ke atas ribuan menjadi Rp9.118.000; 2,5% menjadi Rp2.073.000. Total ketiganya **Rp15.139.000**. Jadikan fixture lengkap sebagai sumber perhitungan, jangan menguji total kiriman Rp60.290.000 tanpa seluruh baris pembentuknya. Kebijakan pembulatan tersebut tetap diberi label kebijakan estimasi demo yang perlu diverifikasi; tidak diklaim aturan kepabeanan resmi oleh revisi ini.

Pisahkan ketidaklengkapan nilai dari angka nol: insurance_value NULL adalah belum diketahui, bukan otomatis bukti asuransi nol. Jika ditampilkan sebagai estimasi sementara, beri asumsi eksplisit dan blocker sampai dikonfirmasi. Rumus/angka pajak sumber memerlukan verifikasi resmi tersendiri sebelum rilis.

## 10. Model bisnis — sesuai kemampuan MVP

Penawaran MVP: satu workspace untuk satu perusahaan importir, dipakai staf, reviewer yang ditugaskan, dan admin. Pilot PPJK dapat dilakukan untuk satu klien terlebih dahulu dengan workspace/akun terpisah. Tidak ada janji multi-klien dalam satu akun di MVP.

Roadmap: membership multi-perusahaan, konsol PPJK, billing, onboarding katalog massal, dan API komersial setelah pilot. Harga adalah hipotesis sampai divalidasi wawancara. Metrik manfaat: waktu total staf, jumlah koreksi, kelengkapan sebelum ETA, biaya model per kiriman, serta proporsi pekerjaan yang diselesaikan tanpa intervensi. Jumlah intervensi manusia dicatat jujur, termasuk upload datasheet dan review.

Klaim utama untuk juri: “Mengubah invoice menjadi hasil pemeriksaan yang dapat ditelusuri, menindaklanjuti kekurangan, dan memperingatkan dampak perubahan aturan.” Jangan menjanjikan barang pasti lolos, penghematan yang belum diukur, atau pengajuan otomatis.

## 11. Audit rubrik & demo — bukti yang dapat dicoba

Bobot rubrik pada artifact menjadi acuan sementara dari dokumen pengguna, belum diverifikasi ulang terhadap guidebook asli. Fokus demo mengikuti bukti otonomi, penalaran, tools, rekayasa, dan manfaat yang memang dapat ditunjukkan.

### Alur demo 5–7 menit untuk juri

| Waktu | Aksi juri/presenter | Bukti sistem |
|---|---|---|
| 0:00–0:40 | Masuk staf, buka kiriman demo dan unggah invoice | Analisis dimulai otomatis, rencana dan langkah nyata muncul |
| 0:40–2:00 | Buka hasil barang yang lengkap dan satu alasan HS | Sumber valid, alternatif, angka dari fungsi; item lain tetap berjalan |
| 2:00–3:00 | Jawab pertanyaan staf dan unggah datasheet contoh | Email permintaan terlihat; hanya barang terkait dianalisis lagi otomatis |
| 3:00–4:00 | Login reviewer, selesaikan keputusan yang diperlukan | Audit manusia, memori, pungutan/checklist/readiness diperbarui |
| 4:00–4:45 | Buka draf dan daftar syarat siap | Ready hanya setelah bukti lengkap; hasil draf berlabel jelas |
| 4:45–6:00 | Login admin dan simulasikan aturan | 007/008 terdampak, 003 diabaikan, beda sebelum/sesudah, tugas dan followup |
| 6:00–7:00 | Buka hasil evaluasi dan biaya | Angka aktual, baseline, keterbatasan, dan jejak yang bisa diperiksa |

Video tetap 3–5 menit sesuai ketentuan yang tertulis pada sumber; alur juri interaktif boleh lebih lama. Waktu tunggu yang dipercepat dalam video diberi label. IMAP tidak ditampilkan sebagai sudah berjalan jika jalur yang dipakai unggah manual. Jangan menjanjikan “satu klik sampai siap” ketika memang ada review wajib.

Skenario untuk juri mencoba sendiri harus mempunyai petunjuk pendek, file contoh, hasil yang diharapkan, dan cara pulih. Sertakan tautan hasil run tersimpan yang berlabel rekaman sebagai cadangan; live LLM tidak boleh diam-diam diganti fake.

Gerbang rilis: A01–A18 lolos, angka eval final tersedia, lima demo live selesai, semua link dapat dibuka sesuai akses juri, biaya/sumber data tercatat, dan tidak ada blocker kritis tersembunyi. Jika target akurasi belum tercapai, laporkan hasil aktual dan perbesar cakupan review; jangan mengubah denominator atau menurunkan target diam-diam.

### Matriks bukti proposal

| Klaim | Bukti minimum |
|---|---|
| Agent proaktif | Run upload-triggered + email SMTP + job followup + perubahan aturan |
| Agent bernalar | Kandidat/sumber, pertanyaan relevan, kritik pemeriksa, hasil eval dibanding baseline |
| Human control | Assist/auto, review dengan alasan, readiness yang menolak data belum lengkap |
| Sistem tahan gagal | Rekaman tes retry/fallback/checkpoint/idempotensi dan UI hasil parsial |
| Manfaat bisnis | Uji waktu terkontrol dengan jumlah sampel dan intervensi yang dicatat |
| Transparansi | Label data demo/simulasi, versi sumber, keterbatasan, biaya dan hasil sebenarnya |

Peluang kompetitif diperkuat oleh alur yang selesai, dapat dicoba ulang, dan mempunyai bukti. Tidak ada klaim bahwa revisi spesifikasi ini sendiri menjamin peringkat lomba.
