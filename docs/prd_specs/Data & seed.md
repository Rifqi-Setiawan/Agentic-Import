# Data dan seed

## Sumber data

Semua data referensi diambil dari sumber resmi lalu disimpan sebagai CSV di repo (`data/seed/`). Database selalu dibangun ulang dari CSV ini, jadi CSV adalah sumber kebenaran. Setiap baris menyimpan sumber dan tanggal ambil supaya bisa ditunjukkan ke juri.

| Data | Sumber resmi | Cara ambil | Tabel tujuan |
| --- | --- | --- | --- |
| Kode HS 8 digit, uraian, tarif BM MFN | BTKI 2022, lampiran PMK 26/PMK.010/2022, PDF dari jdih.kemenkeu.go.id | Ekstrak tabel per bab dengan `scripts/extract_btki.py` (pdfplumber), lalu periksa manual. Tidak ada file Excel resmi | `hs_codes` |
| Catatan bagian, bab, dan pos; Ketentuan Umum Menginterpretasi HS (KUMHS) | BTKI 2022, bagian awal tiap bab | Salin teks catatan bab 33, 61, 62, 84, 85 dan bagian XI, XVI. KUMHS 1 sampai 6 disimpan sebagai `level = 'section'`, `ref = 'KUMHS'` | `hs_notes` |
| Larangan dan pembatasan per kode | Indonesia National Trade Repository (INSW), menu pencarian kode HS | Cari manual per kode yang dipakai di demo dan set uji, catat izin, instansi, tahap, nomor aturan, dan tanggal ambil | `regulations`, `lartas_rules` |
| Tarif PPh Pasal 22 impor | PMK 51/2025 beserta lampirannya | Salin kode yang tercantum di lampiran untuk 5 bab cakupan. Kode yang tidak tercantum memakai tarif umum (2,5% dengan API, 7,5% tanpa API) yang dihitung di kode, bukan disimpan per baris | `pph22_rates` |
| Kurs | Kurs Menteri Keuangan mingguan (kurs pajak), situs fiskal.kemenkeu.go.id | Salin USD, CNY, JPY, EUR, SGD untuk minggu berjalan dan 4 minggu sebelumnya | `exchange_rates` |
| Tarif PPN | PMK 131/2024 | Tidak disimpan di tabel. Konstanta di `app/services/duty.py`: 12% × 11/12 untuk barang bukan mewah | - |

Aturan penting:

- BTKI 2022 sudah beberapa kali mengalami perubahan tarif lewat PMK lain sejak terbit. Untuk setiap kode yang dipakai di demo, cek tarif BM terakhir di INSW dan catat di kolom `note` bila berbeda dari lampiran awal.
- Data lartas tidak di-scrape otomatis. INSW tidak menyediakan API publik untuk ini, dan scraping berisiko melanggar ketentuan situs. Input manual cukup untuk cakupan MVP dan lebih mudah dipertanggungjawabkan.
- Kalau ada kode yang belum diverifikasi, isi `note = 'BELUM DIVERIFIKASI'`. Agent akan menurunkan keyakinan dan menambah alasan risiko `DATA_UNVERIFIED` untuk kode seperti ini.

## Cakupan bab

| Bab | Isi | Alasan dipilih | Dipakai di |
| --- | --- | --- | --- |
| 33 | Minyak atsiri, kosmetik, wangi-wangian | Banyak terkena izin dan pengawasan obat dan makanan, cocok untuk menunjukkan cek lartas | Kiriman CV Ayu Kosmetika, set uji |
| 61 | Pakaian rajutan | Klasifikasi bergantung pada bahan dan cara pembuatan (rajut atau tidak), cocok untuk pertanyaan klarifikasi | Set uji |
| 62 | Pakaian bukan rajutan | Pasangan bab 61, jebakan klasik salah bab | Set uji |
| 84 | Mesin dan peralatan mekanis | Barang industri PT Mitra Kemas Nusantara, termasuk katup pos 8481 untuk skenario pemantau | Kiriman demo, set uji |
| 85 | Mesin dan peralatan listrik | Sering tertukar dengan bab 84 (misalnya motor, panel kontrol) | Kiriman demo, set uji |

Yang dimuat:

- **`hs_codes` dan `hs_notes`**: seluruh kode 8 digit di 5 bab ini, bukan hanya kode demo. Retrieval perlu melihat semua pesaing supaya hasilnya jujur.
- **`lartas_rules` dan `pph22_rates`**: wajib lengkap untuk kode yang muncul di data demo dan set uji. Kode lain boleh kosong. Bila lartas sebuah kode belum diisi, agent menulis "Data lartas untuk kode ini belum tersedia di sistem, cek manual di INSW" dan menaikkan risiko ke sedang, bukan menyatakan bebas lartas.

Barang di luar 5 bab diberi status `out_of_scope`. Agent tetap menyebut perkiraan bab dari hasil pencarian, tetapi tidak menghitung pungutan dan langsung membuat tugas review.

## Format CSV dan skrip ingest

Semua CSV memakai UTF-8, pemisah koma, header di baris pertama, desimal dengan titik, tanggal `YYYY-MM-DD`. Teks yang mengandung koma dibungkus tanda kutip ganda.

### hs\_codes.csv

```csv
code,chapter,heading,subheading,description_raw,description_en,unit,bm_rate,is_luxury,note
84818099,84,8481,848180,"- - - Lain-lain","- - - Other",u,5.000,false,
```

Catatan: uraian 8 digit di BTKI sering hanya "Lain-lain". Karena itu skrip ingest menyusun teks embedding dari rantai induknya:

```
passage: 8481.80.99 | Bab 84: Reaktor nuklir, ketel, mesin ... | Pos 8481: Keran, kran, katup ... | Subpos 8481.80: Peralatan lainnya | Lain-lain
```

Kolom `description_raw` di CSV adalah uraian persis seperti di BTKI dan disimpan ke kolom `description_raw`. Rantai lengkap di atas (tanpa prefiks ` passage:  `) disimpan ke `description_id`, sehingga FTS dan tampilan UI tidak hanya menampilkan "Lain-lain". Kolom `note` dipakai untuk `BELUM DIVERIFIKASI` atau catatan perubahan tarif. `bm_rate` dalam persen, `unit` sesuai satuan BTKI.

### hs\_notes.csv

```csv
level,ref,title,body,source
section,KUMHS,"KUMHS 1","Judul dari Bagian, Bab dan Sub-bab dimaksudkan hanya untuk mempermudah referensi saja ...","BTKI 2022"
chapter,84,"Catatan Bab 84 nomor 2","(teks catatan)","BTKI 2022"
```

Satu catatan bernomor menjadi satu baris supaya kutipan agent tepat sasaran.

### regulations.csv

```csv
number,title,issuer,summary,effective_date,source_url
"(nomor aturan)","(judul)","(instansi)","(ringkasan satu kalimat)",2024-05-17,"https://..."
```

### lartas\_rules.csv

```csv
hs_prefix,regulation_number,permit_name,permit_code,issuing_agency,stage,requires_surveyor,effective_from,effective_to,source_url,retrieved_at,note
330499,"(nomor aturan)","(nama izin sesuai INSW)",,"(instansi)",border,false,2024-05-17,,"https://...",2026-11-02,
```

`regulation_number` harus ada di `regulations.csv`. `hs_prefix` 4 sampai 8 digit; aturan dengan prefiks terpanjang yang menang (lihat query di tab Database).

### pph22\_lampiran.csv

```csv
hs_code,lampiran,rate,regulation
33041000,A,10.000,"PMK 51/2025"
```

Baris di atas hanya contoh format. Lampiran dan tarif setiap kode wajib disalin dari PMK 51/2025.

### exchange\_rates.csv

```csv
currency,rate_idr,valid_from,valid_to,source
USD,16250.0000,2026-11-04,2026-11-10,"Kurs Menteri Keuangan"
```

Angka kurs di atas hanya contoh. Isi dengan kurs resmi minggu berjalan.

### Skrip

| Perintah | Fungsi |
| --- | --- |
| `python -m app.scripts.extract_btki --pdf data/raw/btki2022.pdf --chapters 33,61,62,84,85 --out data/seed/hs_codes.csv` | Ekstrak tabel BTKI ke CSV. Hasilnya diperiksa manual |
| `python -m app.scripts.validate_seed --dir data/seed` | Cek semua CSV tanpa menyentuh database |
| `python -m app.scripts.ingest --dir data/seed` | Muat CSV ke database dan hitung embedding |
| `python -m app.scripts.seed_demo` | Hapus data transaksi lalu buat ulang data demo |
| `python -m app.scripts.make_sample_invoices --out data/demo/invoices` | Buat PDF dan JPG invoice contoh |

Aturan `validate_seed` (gagal bila satu saja dilanggar):

- `code` tepat 8 digit dan unik; `chapter`, `heading`, `subheading` sama dengan potongan `code`.
- `bm_rate` antara 0 dan 150.
- Setiap `hs_code` di `pph22_lampiran.csv` ada di `hs_codes.csv`, dan `lampiran` hanya A, B, atau C.
- Setiap `hs_prefix` di `lartas_rules.csv` cocok dengan minimal satu kode di `hs_codes.csv`.
- Tidak ada dua periode kurs yang tumpang tindih untuk mata uang yang sama.

Aturan `ingest`:

- Idempoten: aman dijalankan berkali-kali (`INSERT ... ON CONFLICT DO UPDATE`).
- Embedding hanya dihitung ulang bila teksnya berubah (bandingkan hash teks).
- Embedding dihitung dalam batch 32 dengan prefiks ` passage:  `. Query pencarian memakai prefiks ` query:  `.
- Di akhir mencetak ringkasan jumlah baris per tabel, dan menolak selesai bila ada kode tanpa embedding.

## Data demo

Data demo dibuat oleh `seed_demo` dan dibuat ulang setiap reset. Semua tanggal dihitung relatif terhadap hari reset (`H`), supaya ETA tidak pernah kedaluwarsa saat juri mencoba.

### Perusahaan dan akun

| Perusahaan | API | Keterangan |
| --- | --- | --- |
| PT Mitra Kemas Nusantara | Ya | Importir mesin dan peralatan pengemasan, pemilik hampir semua kiriman demo |
| CV Ayu Kosmetika | Tidak | Importir kosmetik, untuk menunjukkan PPh 22 tanpa API dan lartas bab 33 |

| Email | Password | Peran | Perusahaan |
| --- | --- | --- | --- |
| `staf@demo.imporjaga.id` | `Demo2026!` | `importer_staff` | PT Mitra Kemas Nusantara |
| `ppjk@demo.imporjaga.id` | `Demo2026!` | `ppjk_reviewer` | PT Mitra Kemas Nusantara |
| `admin@demo.imporjaga.id` | `Demo2026!` | `admin` | PT Mitra Kemas Nusantara |
| `ayu@demo.imporjaga.id` | `Demo2026!` | `importer_staff` | CV Ayu Kosmetika |

Karena semua data dibatasi per perusahaan, akun keempat dibutuhkan untuk melihat kiriman CV Ayu. Tombol cepat di halaman login cukup untuk tiga akun pertama; akun keempat diketik manual. Password sama untuk semua akun dan dicantumkan di proposal serta deskripsi video.

### Kiriman

| Ref | Perusahaan | Status awal | ETA | Isi | Gunanya |
| --- | --- | --- | --- | --- | --- |
| `MKN-IMP-2611-011` | MKN | `draft` tanpa dokumen; `INV-MKN-011.pdf` diunggah saat demo | H+12 | 5 barang: mesin sealing, motor listrik, panel kontrol, katup dengan bahan badan tidak disebut, sabuk konveyor | Demo utama: agent mulai sendiri setelah invoice terunggah, bertanya ke staf apakah panel kontrol dikirim terpisah atau terpasang di mesin sealing, mengirim email ke pemasok meminta datasheet katup (bahan badan tidak disebut), lalu melanjutkan sendiri saat datasheet masuk |
| `MKN-IMP-2611-009` | MKN | `needs_review` | H+10 | 3 barang, satu dengan keyakinan di bawah 0,70 | Demo reviewer |
| `MKN-IMP-2611-007` | MKN | `ready` | H+5 | 3 jenis katup | Skenario pemantau, harus berubah ke `needs_review` |
| `MKN-IMP-2611-008` | MKN | `submitted` | H+14 | 2 jenis katup | Skenario pemantau, harus ditandai terdampak |
| `MKN-IMP-2610-003` | MKN | `arrived` | H-10 | 2 jenis katup | Skenario pemantau, harus diabaikan |
| `MKN-IMP-2611-012` | MKN | `draft`, invoice berupa foto JPG | H+15 | 3 barang | Menunjukkan ekstraksi dengan model vision |
| `AYU-IMP-2611-002` | CV Ayu | `draft`, invoice PDF sudah diunggah | H+9 | 4 produk kosmetik (serum wajah, lipstik, sampo, parfum) | PPh 22 tanpa API dan lartas bab 33 |

Alamat email untuk demo:

- Inbox agent: satu akun Gmail baru khusus agent (misalnya `agent.imporjaga.<namatim>@gmail.com`) dengan verifikasi dua langkah dan app password untuk SMTP dan IMAP.
- Pemasok: satu akun Gmail lain milik tim (misalnya `pemasok.demo.<namatim>@gmail.com`) dipakai sebagai `supplier_email` di semua kiriman demo. Saat demo, anggota tim membuka inbox ini, membalas email agent, dan melampirkan `DS-VALVE-011.pdf`.
- `AGENT_EMAIL_ALLOWED_DOMAINS=gmail.com` dan alamat pemasok sungguhan tidak pernah dipakai.

Kedua perusahaan demo memakai tingkat otonomi `auto`. Untuk menunjukkan kontrol manusia, admin bisa mengubahnya ke `assist` lalu menjalankan ulang analisis: email agent berubah menjadi draf yang menunggu tombol Kirim.

Kiriman `007`, `008`, `009`, dan `003` dibuat lengkap dengan hasil analisis (klasifikasi, lartas, pungutan, checklist, draf PIB, dan jejak agent hasil seed yang ditandai `trigger = 'schedule'`) agar langsung bisa dibuka tanpa menunggu agent. Kiriman `011`, `012`, dan `AYU-002` sengaja dibiarkan `draft` agar juri bisa menjalankan agent sendiri. Kiriman 011 sengaja tanpa dokumen: juri atau presenter mengunggah INV-MKN-011.pdf (tautannya ada di README) dan melihat agent mulai bekerja sendiri tanpa tombol.

### Memori awal (10 entri, PT Mitra Kemas Nusantara)

Dibuat dari keputusan reviewer fiktif di masa lalu supaya `find_similar_approved` punya bahan saat demo. Kode HS tiap entri diambil dari BTKI dan diverifikasi tim, bukan dikarang.

1. Gate valve DN80 PN16, badan besi cor, flens
2. Ball valve 2 inci, badan baja tahan karat, ulir
3. Check valve DN50, badan besi cor
4. Motor induksi 3 fase 5,5 kW
5. Motor induksi 3 fase 11 kW
6. Panel kontrol PLC untuk mesin pengemas, tegangan 380 V
7. Mesin sealing kantong plastik otomatis
8. Sabuk konveyor karet lebar 600 mm
9. Sensor proximity induktif 24 V DC
10. Pompa sentrifugal air 2,2 kW

Entri sengaja dibuat mirip tetapi tidak sama dengan barang di `MKN-IMP-2611-011`, sehingga demo menunjukkan memori membantu tanpa menggantikan penalaran. Katup tanpa keterangan bahan di kiriman `011` tidak boleh langsung cocok dengan entri 1 atau 2 (kemiripan harus di bawah 0,92), supaya agent tetap bertanya.

### Invoice contoh

`make_sample_invoices` membuat invoice dengan reportlab memakai data kiriman di atas: nama pemasok fiktif, nomor invoice, tanggal, incoterm, tabel barang (uraian, jumlah, satuan, harga satuan, total), ongkos kirim, dan total. Variasi yang dibuat:

- `INV-MKN-011.pdf`: PDF berteks, rapi.
- `INV-MKN-012.jpg`: invoice yang sama gayanya, dirender ke gambar lalu diputar 2 derajat dan diberi noise ringan supaya mirip hasil foto.
- `INV-AYU-002.pdf`: PDF berteks dengan uraian produk dalam bahasa Inggris.
- `PL-MKN-011.pdf`: packing list untuk kiriman `011`.

Tambahan untuk alur tindak lanjut: `DS-VALVE-011.pdf`, datasheet fiktif dari pemasok yang menyebut bahan badan katup secara jelas. File ini tidak diunggah oleh `seed_demo`. File ini dikirim sebagai lampiran balasan email saat demo, atau diunggah manual di tab Dokumen bila inbox agent (P1) belum jadi.

Semua dokumen memuat tulisan kecil "Dokumen contoh untuk demo, fiktif" di footer.

## Set uji klasifikasi HS

Set uji adalah bukti terkuat untuk kriteria penalaran. Angkanya masuk proposal dan video, apa pun hasilnya. Lebih baik melaporkan angka jujur 70% beserta analisis kesalahan daripada angka 95% yang tidak bisa dibuktikan.

### Komposisi

60 barang, 12 per bab (33, 61, 62, 84, 85). Per bab: 4 mudah, 5 sedang, 3 sulit.

- **Mudah**: uraian jelas dan langsung cocok dengan satu pos.
- **Sedang**: perlu catatan bab atau membedakan subpos yang mirip.
- **Sulit**: atribut penting tidak disebut (bahan, rajut atau tidak, fungsi utama), sehingga jawaban yang benar adalah bertanya dulu.

Uraian ditulis seperti di invoice nyata (bahasa Inggris campur singkatan), bukan menyalin uraian BTKI, supaya tes tidak terlalu mudah.

### Format eval\_hs.csv

```csv
id,chapter,difficulty,description,attributes_json,expected_hs8,acceptable_hs8,clarification_answer,labeled_by,note
E001,84,easy,"GATE VALVE DN100 PN16 CAST IRON FLANGED","{}",(8 digit),,,"A;B",
E045,61,hard,"MEN T-SHIRT 100% COTTON","{}",(8 digit),,"Rajutan","A;B","Perlu tanya rajut atau tenun"
```

- `expected_hs8`: kode yang benar menurut tim, dari BTKI.
- `acceptable_hs8`: kode lain yang juga bisa dibenarkan, dipisah `|`. Dipakai hanya untuk analisis, tidak menambah skor top-1.
- `clarification_answer`: jawaban yang diberikan otomatis bila agent bertanya.
- `labeled_by`: dua anggota tim memberi label secara terpisah. Bila berbeda, didiskusikan dan dicatat di `note`. Bila sempat, minta satu PPJK atau dosen yang paham kepabeanan memeriksa 15 barang sulit.

### Cara menjalankan

```bash
python -m app.eval.eval_hs --file data/eval/eval_hs.csv --out reports/eval_$(date +%Y%m%d).json
python -m app.eval.eval_hs --file data/eval/eval_hs.csv --mode retrieval_only --out reports/eval_retrieval.json
```

Harness memanggil graph klasifikasi yang sama dengan produksi, tetapi interrupt klarifikasi dijawab otomatis dari kolom `clarification_answer`. Memori dimatikan selama eval supaya tidak bocor dari set uji.

### Metrik

| Metrik | Definisi | Target awal |
| --- | --- | --- |
| Top-1 6 digit | Kode final cocok dengan `expected_hs8` di 6 digit pertama | 85% |
| Top-1 8 digit | Kode final sama persis | 70% |
| Top-3 8 digit | `expected_hs8` ada di 3 kandidat teratas agent | 85% |
| Recall@10 retrieval | `expected_hs8` muncul di hasil `search_hs_candidates` | 90% |
| Ketepatan bertanya | Dari barang sulit, berapa persen yang memicu klarifikasi | 80% |
| Bertanya tanpa perlu | Dari barang mudah, berapa persen yang memicu klarifikasi | di bawah 10% |
| Kalibrasi | Akurasi top-1 pada barang dengan keyakinan di atas 0,85 dibanding di bawah 0,70 | Kelompok tinggi jelas lebih akurat |
| Rata-rata tool call, durasi, token per barang | Dari `agent_steps` dan `agent_runs` | Dilaporkan |

Target di atas adalah titik awal, bukan janji. Bandingkan juga mode `retrieval_only` (ambil kandidat teratas tanpa agent) dengan mode agent penuh. Selisih keduanya adalah bukti bahwa loop penalaran agent memberi nilai tambah, dan grafik perbandingan ini sebaiknya masuk proposal.

Laporan JSON memuat daftar barang yang salah beserta kode yang dipilih, alasan agent, dan kategori kesalahan (salah bab, salah pos, salah subpos, data kurang). Kategori kesalahan ini dibahas di proposal bagian keterbatasan.
