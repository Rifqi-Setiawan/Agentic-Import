# Audit rubrik dan ketentuan

Pemeriksaan seluruh dokumen terhadap guidebook GTNIC 2026 kategori AI Agent, dilakukan 1 November 2026.

## Kesimpulan

Sebelum revisi, desain sudah memenuhi syarat minimum: bukan sekadar chat, ada tool calling, ada RAG, dan bisa diakses publik. Tetapi desain itu lemah di kriteria dengan bobot terbesar, yaitu otonomi (25%). Ada tiga kelemahan:

- Agent hanya bekerja setelah tombol ditekan.
- Agent berhenti di daftar kekurangan, jadi staf yang harus mengejar dokumen.
- Graph pemantau aturan sama sekali tidak memakai LLM. Juri bisa menyebutnya workflow biasa, bukan agent.

Nilai bisnis juga belum dibahas, padahal ada di rubrik (10%).

Revisi hari ini menambahkan:

- pemicu otomatis saat invoice masuk,
- rencana kerja yang diperbarui,
- pemeriksaan diri dengan model berbeda,
- tindak lanjut ke pemasok lewat email dengan pengecekan ulang terjadwal,
- respons pemantau aturan yang diputuskan LLM,
- tingkat otonomi per perusahaan,
- tab Model bisnis.

Dengan revisi ini, alur utama yang bisa ditunjukkan ke juri adalah satu kiriman yang berjalan dari invoice sampai siap diajukan, dengan manusia hanya menjawab satu pertanyaan.

## Penilaian per kriteria

| Kriteria | Bobot | Bukti di desain sekarang | Celah atau risiko yang tersisa | Yang wajib terlihat di demo dan proposal |
| --- | --- | --- | --- | --- |
| Kapabilitas dan otonomi agen | 25% | Mulai sendiri saat invoice masuk, rencana kerja, email ke pemasok dan pengingat terjadwal, lanjut sendiri saat balasan atau dokumen masuk, pemantau aturan bertindak sendiri, persetujuan otomatis di tingkat auto | Review manusia dan pertanyaan klarifikasi bisa dibaca sebagai "kurang otonom". Jelaskan sebagai keputusan desain karena risiko hukum, dan tunjukkan bahwa tingkatnya bisa diatur | Satu kiriman dari unggah invoice sampai siap tanpa klik selain menjawab satu pertanyaan. Panel jejak terlihat terus |
| Penalaran, perencanaan, keputusan | 15% | `plan_shipment` dan revisinya, loop ReAct dengan KUMHS, wajib mencari di dokumen sebelum bertanya, memilih bertanya ke staf atau pemasok, `verify_consistency` dengan buka ulang, retry, fallback, checkpoint | Klaim penalaran harus dibuktikan angka, bukan hanya diagram | Grafik eval agent penuh dibanding retrieval saja. Satu contoh kritik pemeriksa yang memperbaiki kode. `PlanCard` di video |
| Penggunaan alat dan eksekusi tindakan | 15% | 8 tools ReAct, 4 tools tindak lanjut, tools sistem, skema Pydantic, error dikembalikan sebagai data, email nyata lewat SMTP, inbox IMAP (P1) | Layanan eksternal masih terbatas (LLM dan email). Jangan mengklaim integrasi INSW atau CEISA | Langkah tool di jejak dengan argumen dan hasilnya. Email yang benar-benar masuk ke inbox pemasok demo |
| Arsitektur dan rekayasa sistem | 15% | 25 tabel dengan constraint, worker dan antrean `SKIP LOCKED`, checkpoint, guardrail, masking, rate limit, tes, CI | Dinilai dari proposal, jadi harus tertulis jelas | Tiga diagram (arsitektur, graph agent, relasi tabel), tabel skenario kegagalan, tabel guardrail |
| Inovasi dan kreativitas | 10% | Pemantau aturan proaktif, memori per perusahaan dari keputusan manusia, validasi kutipan, agent yang mengejar pemasok | Belum ada riset pesaing | Cari alat yang sudah ada sebelum menulis klaim kebaruan |
| Dampak masalah dan nilai bisnis | 10% | Tab Model bisnis dengan sumber denda, lama pemeriksaan, dan biaya jasa | Metrik waktu belum diukur. Jumlah PPJK dan importir belum bersumber | Uji waktu kecil sebelum 8 November (caranya di tab Model bisnis) |
| Pengalaman dan kemudahan pengguna | 5% | Konvensi status, label agent dan manusia, pesan error, keadaan kosong, tombol cepat login | Belum diuji ke orang awam | Minta 1 sampai 2 orang mencoba tanpa dipandu, catat di mana mereka bingung |
| Demonstrasi dan dokumentasi | 5% | README, naskah video, uji asap, rencana cadangan | Rekaman yang terlalu banyak dipotong bisa terlihat tidak live | Rekam satu alur utuh, bagian menunggu boleh dipercepat dengan label |

## Kepatuhan terhadap ketentuan

| Ketentuan guidebook | Status | Catatan |
| --- | --- | --- |
| Sesuai sub-tema Enterprise Productivity, fokus Enterprise & Industry | Sesuai | Otomatisasi dokumen dan kepatuhan impor, dekat dengan contoh AI Document Processing Agent |
| Bukan ChatGPT wrapper; ada reasoning, tool calling, atau RAG | Sesuai | Ketiganya ada |
| Antarmuka dan repo publik sampai kompetisi berakhir | Direncanakan | Server, domain, dan kuota LLM aktif sampai minimal 15 November |
| Karya 100% orisinal, tidak menyalin arsitektur atau kode repo publik tanpa modifikasi berarti | Aman bila dikerjakan sesuai rencana | Library boleh. Jangan menyalin template agent utuh dari repo lain |
| Keluaran tidak memuat SARA, pornografi, kekerasan, provokatif, atau melanggar hukum | Ada guardrail | Daftar kata terlarang pada alasan dan ringkasan |
| Mematuhi ketentuan dan lisensi layanan pihak ketiga | **Risiko** | Lihat poin 9Router di bawah |
| Privasi data menjadi tanggung jawab peserta | Sesuai | Data perusahaan fiktif, masking sebelum LLM, email hanya ke inbox tim |
| Proposal PDF maks 15 halaman, A4, TNR 12, spasi 1,5, margin kiri 4 cm dan lainnya 3 cm, logo GTNIC di sampul | Direncanakan | Kerangka di tab Rencana kerja & QA |
| Video 3 sampai 5 menit, akses publik, memuat perkenalan, masalah, demo live, arsitektur | Direncanakan | Naskah di tab Rencana kerja & QA |
| Formulir: tautan live, repo, proposal, video, surat pernyataan keaslian, nama tim | Direncanakan | Checklist pengumpulan |

## Risiko yang perlu diputuskan tim

1. **9Router dan ketentuan layanan.** Repo 9Router menyebut login OAuth untuk Claude Code, Codex, dan Gemini CLI, yaitu memakai akun langganan. Memakai langganan pribadi sebagai mesin aplikasi publik kemungkinan besar bertentangan dengan ketentuan layanan penyedia. Guidebook juga meminta peserta mematuhi ketentuan dan lisensi pihak ketiga. Rekomendasi: untuk server demo, pakai provider dengan API key resmi. Ini bisa tetap lewat 9Router dalam mode API key, atau langsung ke provider. Kode tidak berubah karena formatnya kompatibel OpenAI; cukup ganti `LLM_BASE_URL` dan `LLM_API_KEY`. Pantau biayanya terhadap batas di tab PRD.
2. **Beban kerja.** Revisi otonomi menambah sekitar 1,5 hari kerja. Jadwal dan urutan potong sudah diperbarui. Inbox IMAP adalah fitur pertama yang dipotong; email keluar ke pemasok tetap wajib.
3. **Kebenaran data.** Kode HS, tarif, lartas, dan PPh 22 di data demo dan set uji wajib diverifikasi dari sumber resmi. Yang belum diverifikasi diberi label `BELUM DIVERIFIKASI`.
4. **Email ke pihak luar.** Selama lomba, agent hanya boleh mengirim ke inbox milik tim (`AGENT_EMAIL_ALLOWED_DOMAINS`).
5. **Klaim di proposal.** Setiap angka wajib bersumber atau berasal dari uji tim. Lebih aman menulis "pada uji 60 barang, akurasi 8 digit 72%" daripada angka besar tanpa bukti.

## Cara menjelaskan peran manusia di dalam alur

Juri mungkin bertanya kenapa masih ada review manusia kalau agent-nya otonom. Jawaban yang disarankan: agent menyelesaikan pekerjaan sendiri dari awal sampai akhir, termasuk mengejar pemasok dan bereaksi pada aturan baru. Manusia hanya dilibatkan di dua titik yang berisiko hukum: barang yang keyakinannya rendah, dan pengajuan PIB yang memang wewenang PPJK atau importir. Batas itu bisa diatur lewat tingkat otonomi, dan pada tingkat auto barang yang jelas langsung disetujui agent.

## Perubahan dokumen pada revisi ini

| Tab | Perubahan |
| --- | --- |
| PRD | Dua fitur P0 baru (mulai sendiri, rencana dan pemeriksaan diri, tindak lanjut ke pemasok), dua P1 (tingkat otonomi, inbox email), US-15 sampai US-18, alur utama tanpa tombol |
| Arsitektur & tech stack | Komponen server email di diagram, env SMTP, IMAP, batas email, jeda tindak lanjut, domain yang diizinkan |
| Database | Tabel `messages` (total 25 tabel), `companies.autonomy_level`, `shipments.supplier_email`, `clarifications.channel`, pemicu run dan jenis job baru |
| API | Endpoint rencana, pesan, pengaturan otonomi, dan aturan pemicu otomatis saat unggah |
| Agent & AI | Diagram graph 14 node, node `plan_shipment`, `verify_consistency`, `resolve_gaps`, `plan_response`, tools baru, prompt, tingkat otonomi, tindak lanjut, email masuk, kegagalan dan guardrail baru |
| Frontend | Tab Komunikasi, `PlanCard`, `MessageList`, `AutonomySwitch`, wizard yang memulai agent sendiri, label baru |
| Data & seed | Inbox demo, datasheet balasan, kiriman 011 tanpa dokumen untuk demo pemicu otomatis |
| Infrastruktur & keamanan | Aturan keamanan email dan prompt injection dari email |
| Rencana kerja & QA | Jadwal, urutan potong, tes baru, alur Playwright, naskah video, uji asap |
| Model bisnis | Tab baru |
