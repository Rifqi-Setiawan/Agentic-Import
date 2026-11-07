# Panduan Demo Artha — End to End

Disusun: 5 November 2026, berdasarkan aplikasi live dan source commit **44600392a5ecee9fe813476afa856b97b8f38fd3**.

**Aplikasi:** https://artha.rifqisetiawan.my.id

Panduan ini mencakup persiapan, input yang disalin, urutan klik, hasil yang diperiksa, narasi untuk juri, cabang klarifikasi/review, penutupan proses, dan penanganan gangguan. Nama tombol mengikuti UI yang tersedia saat panduan diperiksa. Jumlah transaksi dan ID dapat berubah setelah aplikasi dipakai.

## 1. Hasil demo yang ingin ditunjukkan

Cerita utamanya: **staf mengunggah invoice → agent membaca dan memeriksa barang → sistem meminta informasi yang kurang → reviewer memutuskan → sistem menampilkan penghalang kesiapan dan draf administrasi → staf mencatat pengajuan yang dilakukan di luar aplikasi.**

Ada dua jalur yang ditunjukkan dengan penjelasan terbuka:

| Jalur | Tujuan | Data yang digunakan |
|---|---|---|
| A. Transaksi baru dengan AI live | Membuktikan unggah, ekstraksi, jejak agent, klarifikasi, review manusia, dan pemeriksaan kelengkapan | Kiriman baru berawalan ARTHA-JURI |
| B. Contoh akhir proses yang disiapkan | Menunjukkan tampilan siap, draf PIB, pencatatan pengajuan, dan pemantauan perubahan aturan | MKN-DEMO-001, MKN-DEMO-012, dan fixture lain |

**Jangan menyambungkan kedua jalur seolah-olah transaksi baru langsung menjadi fixture siap.** Pipeline baru dapat tetap belum siap karena tarif dan cakupan lartas belum terverifikasi. Pada versi ini tidak tersedia alur UI lengkap untuk memverifikasi seluruh tarif/lartas tersebut.

Narasi yang tepat:

> “Saya akan memperlihatkan satu proses AI yang berjalan langsung. Untuk memperlihatkan tahap akhir tanpa melewati pemeriksaan yang belum lengkap, saya juga memakai contoh transaksi fiktif yang statusnya sudah disiapkan.”

## 2. Akun dan pembagian peran

| Peran | Tombol masuk cepat | Email manual | Password demo | Digunakan untuk |
|---|---|---|---|---|
| Staf | Staf impor | staf@mitrakemas.example | imporjaga123 | Membuat kiriman, unggah, menjawab klarifikasi, melihat hasil, mencatat pengajuan |
| Reviewer | Reviewer PPJK | reviewer@mitrakemas.example | imporjaga123 | Menyetujui, mengubah kode, atau menolak usulan |
| Admin | Admin | admin@mitrakemas.example | imporjaga123 | Simulasi perubahan aturan dan akses operasional demo |

Ketiga akun berada di **PT Mitra Kemas Nusantara**. Satu pengguna terikat pada satu perusahaan. Kartu perusahaan di sidebar bukan alur pemilihan banyak perusahaan pada MVP ini.

Untuk berganti peran, tekan **Keluar / ganti peran**, lalu pilih tombol akun berikutnya. Gunakan pergantian ini dalam satu jendela. Dua tab dalam profil browser yang sama berbagi sesi; jangan menganggap masing-masing tab dapat mempertahankan peran yang berbeda. Jika memerlukan dua sesi sekaligus, gunakan profil browser terpisah atau jendela privat.

## 3. Persiapan sebelum juri melihat layar

### 3.1 Pemeriksaan 15–30 menit sebelum presentasi

1. Buka aplikasi dan pastikan halaman login tampil.
2. Buka https://artha.rifqisetiawan.my.id/health di tab terpisah. Periksa status **UP**, database **connected**, dan umur heartbeat worker tidak lebih dari 60 detik. Jika DEGRADED, perbaiki layanan sebelum memulai bagian live.
3. Masuk sebagai staf. Pastikan Dashboard, Kiriman impor, Cari kode HS, dan Aturan & dampak bisa dimuat.
4. Cari MKN-DEMO-001. Pastikan detailnya masih siap dan tombol pencatatan pengajuan tersedia jika tahap itu ingin diperagakan.
5. Cari MKN-DEMO-012. Simpan sebagai contoh **sebelum** simulasi aturan, jangan diubah lebih dahulu.
6. Unduh berkas di bagian 3.2 ke satu folder lokal. Buka setiap PDF dan periksa watermark DEMO serta teksnya dapat diseleksi.
7. Jalankan satu latihan terpisah dengan nomor ARTHA-LATIHAN-20261105-01. Untuk penampilan berikutnya gunakan nomor baru; jangan memakai ulang nomor kiriman latihan.
8. Catat durasi AI yang benar-benar terukur saat latihan. Jangan menjanjikan waktu analisis 15 detik: panggilan 9Router pada pengujian sebelumnya bisa memerlukan beberapa menit.
9. Siapkan satu transaksi hasil latihan yang memiliki **run AI nyata**, untuk dibuka jika panggilan live lambat. Catat nomor referensi, uraian barang, dan hasil akhirnya.
10. Pastikan tidak ada latihan lain yang masih memproses saat mulai presentasi.

**Tidak perlu menekan Reset data demo.** Tombol itu mengganti transaksi demo; bukan cara aman untuk mengulang semua skenario pengayaan data ini. Importer aditif juga melewati fixture yang sudah ada, sehingga menjalankannya ulang tidak otomatis membatalkan keputusan atau mengembalikan status fixture.

### 3.2 Berkas utama yang harus diunduh

| Berkas | Tautan unduh | Dipakai sebagai |
|---|---|---|
| INV-DEMO-MKN-001.pdf | [Unduh invoice](https://artha.rifqisetiawan.my.id/data/demo/documents/INV-DEMO-MKN-001.pdf) | Invoice utama dua mesin pengemasan |
| DS-APX-M8422.pdf | [Unduh datasheet](https://artha.rifqisetiawan.my.id/data/demo/documents/DS-APX-M8422.pdf) | Spesifikasi teknis kedua mesin |
| PKL-DEMO-MKN-001.pdf | [Unduh packing list](https://artha.rifqisetiawan.my.id/data/demo/documents/PKL-DEMO-MKN-001.pdf) | Kelengkapan kemasan |
| BL-DEMO-MKN-001.pdf | [Unduh BL](https://artha.rifqisetiawan.my.id/data/demo/documents/BL-DEMO-MKN-001.pdf) | Kelengkapan dokumen pengangkutan |

Berkas alternatif untuk latihan lebih panjang:

| Berkas | Tautan | Catatan |
|---|---|---|
| INV-DEMO-MKN-002.pdf | [Invoice katup](https://artha.rifqisetiawan.my.id/data/demo/documents/INV-DEMO-MKN-002.pdf) | Cocok untuk latihan penjelasan material, aktuator, dan fungsi katup |
| DS-NFC-V8481.pdf | [Datasheet katup](https://artha.rifqisetiawan.my.id/data/demo/documents/DS-NFC-V8481.pdf) | Bahan bodi dan parameter teknis dummy |
| INV-DEMO-MKN-003.pdf | [Invoice motor dan sakelar](https://artha.rifqisetiawan.my.id/data/demo/documents/INV-DEMO-MKN-003.pdf) | Alternatif latihan klarifikasi |
| DS-DGM-MOT.pdf | [Datasheet motor](https://artha.rifqisetiawan.my.id/data/demo/documents/DS-DGM-MOT.pdf) | Informasi motor lebih lengkap |

Semua dokumen ini fiktif. Beberapa dokumen memuat kode HS sebagai referensi fixture. Jangan menyebut pengujian dengan dokumen tersebut sebagai benchmark prediksi HS tanpa petunjuk. Fokus demo adalah proses validasi, bukti, penanganan kekurangan, dan keputusan manusia.

## 4. Susunan presentasi yang disarankan

Untuk slot **10–15 menit**, siapkan hasil latihan sebelum presentasi. Urutan di bawah tetap memperlihatkan input live, sambil memakai waktu tunggu untuk menjelaskan referensi dan kontrol sistem.

| Bagian | Alokasi presentasi | Yang ditunjukkan |
|---|---|---|
| Pembukaan dan dashboard | 1 menit | Masalah pengguna dan ringkasan pekerjaan |
| Buat kiriman dan unggah invoice | 2 menit | Input sungguhan dan antrean analisis |
| Referensi HS dan regulasi saat menunggu | 2 menit | Data resmi dan sumber yang dapat dibuka |
| Jejak, barang, klarifikasi, review | 3–5 menit | Gunakan live jika selesai; jika belum, jelaskan dan buka hasil latihan nyata |
| Kelengkapan dan tahap akhir tersimpan | 2 menit | Penghalang kesiapan, draf PIB, status siap/submitted |
| Simulasi aturan dan penutup | 1–3 menit | Dampak pada contoh katup dan rangkuman manfaat |

Alokasi tersebut **bukan SLA waktu AI**. Untuk latihan semua cabang dan unggah seluruh dokumen satu per satu, sediakan sesi lebih panjang. Jangan menghabiskan slot presentasi dengan menunggu layar kosong.

## 5. Langkah 1 — Masuk dan jelaskan konteks

**Klik:** buka aplikasi → tekan **Staf impor**.

**Lihat:** nama perusahaan di sidebar, nama/peran pengguna, dan menu yang tersedia.

**Jelaskan:**

> “Saya berperan sebagai staf impor pada satu perusahaan. Pekerjaan saya menyiapkan dokumen dan spesifikasi, sedangkan keputusan klasifikasi yang memerlukan penilaian ahli tetap ditinjau reviewer.”

**Berhasil jika:** dashboard termuat tanpa pesan error. Jika login manual diperlukan, isi email staf dan password demo pada tabel akun, lalu tekan **Masuk**.

## 6. Langkah 2 — Baca Dashboard

**Klik:** **Dashboard** jika belum berada di halaman itu.

**Lihat dan tunjuk satu per satu:**

1. Total kiriman: ukuran pekerjaan perusahaan saat ini.
2. Menunggu klarifikasi: transaksi yang memerlukan informasi tambahan.
3. Perlu review ahli: keputusan yang belum selesai ditinjau manusia.
4. Siap diajukan: hasil pemeriksaan aplikasi, bukan bukti sudah dikirim ke CEISA.
5. Panel Perlu perhatian: pintu masuk ke pekerjaan yang harus ditindaklanjuti.
6. Ringkasan kiriman: referensi, pemasok, jumlah barang, status, dan kesiapan.

Pada pemeriksaan awal setelah pengayaan ada 21 kiriman; angkanya akan bertambah setelah demo. Sebut angka di layar, jangan menghafalkan angka snapshot sebagai hasil tetap.

**Narasi:**

> “Dashboard mengarahkan staf ke penghambat pekerjaan. Tujuannya bukan sekadar menampilkan jumlah kiriman, tetapi menunjukkan langkah berikutnya yang perlu diselesaikan.”

## 7. Langkah 3 — Buat kiriman baru

**Klik:** **Kiriman baru** → modal **Buat kiriman**.

Isi data berikut:

| Field di layar | Nilai yang diinput | Penjelasan |
|---|---|---|
| Nomor referensi | ARTHA-JURI-20261105-01 | Ganti akhiran 01 menjadi 02, 03, dan seterusnya untuk percobaan berikutnya |
| Nama pemasok | Apex Automation Machinery Co., Ltd. | Pemasok fiktif yang cocok dengan invoice |
| Email pemasok | export@apex-automation.example | Alamat dummy; jangan mengharapkan email diterima pihak luar |
| Mata uang | USD | Huruf besar, sesuai invoice |
| CIF rupiah jika sudah diketahui (opsional) | Kosongkan | Hindari mengaku mengetahui CIF resmi dari nilai barang saja |
| Kurs rupiah per unit valuta — diisi pengguna untuk demo, bukan kurs resmi otomatis | 16200 | Angka kurs simulasi yang diinput pengguna |

Jika latihan memang memakai asumsi CIF demo sudah lengkap, nilai contoh 246240000 berasal dari 15200 × 16200. Jelaskan asumsi bahwa seluruh unsur CIF sudah termasuk; perkalian nilai barang saja bukan bukti CIF transaksi nyata.

**Klik:** **Simpan kiriman**.

**Lihat:** detail kiriman baru dan pemberitahuan **Kiriman tersimpan. Unggah invoice di tab Dokumen.**

**Narasi:**

> “Perusahaan mengikuti akun yang masuk. Saya membuat satu kiriman dan memberikan kurs demo secara eksplisit, sehingga sistem tidak menyamarkan kurs asumsi sebagai kurs resmi otomatis.”

**Catat:** nomor referensi baru. Semua tindakan berikutnya harus pada kiriman ini, bukan transaksi lain yang kebetulan memiliki barang serupa.

## 8. Langkah 4 — Unggah invoice dan mulai proses live

**Klik:** tab **Dokumen**.

1. Pada **Jenis dokumen**, pilih **Invoice**.
2. Pada **PDF berteks, maksimal 10 MB**, tekan kontrol pilih berkas dari browser.
3. Pilih **INV-DEMO-MKN-001.pdf** yang sudah diunduh.
4. Pastikan file yang dipilih benar.
5. Tekan **Unggah dan proses** satu kali.

**Lihat:** pemberitahuan **Dokumen tersimpan. Analisis akan berjalan sesuai antrean.** Aplikasi berpindah ke tab **Jejak**. Run dapat belum muncul selama job masih menunggu worker.

**Jelaskan:**

> “Unggahan disimpan sebagai dokumen kiriman dan memicu pekerjaan di worker. Agent menggunakan model melalui 9Router, sedangkan hasil dan langkah kerjanya dicatat agar dapat diperiksa.”

**Jangan:** menekan **Analisis ulang** berkali-kali ketika proses masih berlangsung. Mengunggah dokumen lain juga memicu analisis; jangan menumpuk unggahan selama demo utama.

**Berhasil jika:** dokumen tercatat di tab Dokumen dan akhirnya ada run/jejak. Belum muncul hasil barang dalam beberapa detik bukan berarti unggahan gagal.

## 9. Langkah 5 — Baca jejak agent

**Klik:** tab **Jejak** → pada **Riwayat analisis**, pilih run paling baru milik kiriman tersebut.

**Lihat:** nomor run, status koneksi, urutan langkah, ringkasan hasil, nama alat jika tersedia, dan panel **Lihat bukti langkah**.

Langkah yang mungkin terlihat meliputi pemuatan dokumen, pembacaan teks, ekstraksi barang, rencana pemeriksaan, pencarian kandidat, respons model, klasifikasi/klarifikasi, pemeriksaan konsistensi, pemeriksaan kepatuhan, dan finalisasi. Beberapa langkah hanya muncul jika cabangnya dijalankan; jangan menjanjikan urutan/jumlah log yang selalu identik.

**Klik:** buka **Lihat bukti langkah** pada satu pencarian kandidat atau hasil klasifikasi yang memang tersedia.

**Narasi:**

> “Jejak ini memperlihatkan pekerjaan yang benar-benar tercatat untuk kiriman dan run ini. Status proses selesai berarti satu putaran analisis selesai, bukan berarti barang otomatis sah atau kiriman otomatis siap diajukan.”

Jika belum ada run, tunggu sebentar dan periksa lagi. Halaman detail memperbarui data secara berkala; tidak perlu membuat kiriman baru atau unggah ulang. Jika koneksi jejak terputus, kembali ke tab lain lalu Jejak dan pilih run yang sama, atau refresh satu kali setelah mencatat referensi kiriman.

## 10. Langkah 6 — Tunjukkan sumber HS sambil menunggu AI

**Klik:** menu **Cari kode HS**.

| Input pada Cari HS | Klik | Hasil yang diperiksa |
|---|---|---|
| 3301.29.20 | Cari | Satu hasil kanonikal 33012920, uraian cendana / sandalwood |
| 33012960 | Cari | Uraian nilam / patchouli |
| 84224000 | Cari | Referensi mesin pengemas/pembungkus sesuai uraian sumber |
| 33012910 | Cari | Tidak ada hasil referensi yang valid; jangan dijadikan kode pengganti |

Pada hasil cendana, tunjukkan **Tarif BM: Belum diverifikasi**, **Cakupan lartas: Belum diverifikasi**, nomor halaman, dan **Buka sumber ↗**.

**Klik:** **Buka sumber ↗** jika jaringan ke sumber memungkinkan. PDF resmi terbuka di tab baru. Tunjukkan sumber penerbit dan kembali ke aplikasi.

**Narasi:**

> “Katalog memuat 2.614 kode dari lima bab BTKI 2022: 33, 61, 62, 84, dan 85. Uraian punya tautan dan halaman sumber. Keberadaan kode tidak berarti tarif dan semua kewajiban izinnya sudah terverifikasi.”

Jangan menyebut cakupan ini sebagai seluruh BTKI atau konsolidasi semua perubahan terbaru.

## 11. Langkah 7 — Periksa barang hasil ekstraksi

**Klik:** **Kiriman impor** → isi **Cari kiriman** dengan referensi ARTHA-JURI tadi → **Buka** pada baris yang cocok → tab **Barang**.

**Klik:** baris/segitiga pada setiap barang untuk membuka rinciannya.

Bandingkan dengan invoice:

| Barang | Jumlah dan nilai pada fixture | Referensi HS fixture, bukan keputusan otomatis |
|---|---|---|
| APX-M8422-FL — Automatic Liquid Bottle Filling Machine | 2 SET × USD4500 = USD9000 | 84223000 |
| APX-M8422-WR — Heat-Shrink Film Packaging and Wrapping Machine | 1 SET × USD6200 = USD6200 | 84224000 |
| Total invoice | USD15200 | Tidak termasuk klaim tarif/kurs resmi |

Periksa jumlah baris, uraian, jumlah/satuan, usulan atau kode diterima, skor keyakinan bila tersedia, alasan, kutipan sumber, alternatif jika tersedia, dan status persetujuan.

**Narasi:**

> “Yang diperiksa bukan hanya sebuah nomor HS. Saya cocokkan barang yang dibaca, alasan pemilihan, bukti katalog, dan apakah keputusan itu sudah ditinjau. Skor keyakinan bukan persentase akurasi yang sudah dibuktikan.”

Jika agent meminta klarifikasi, ikuti langkah 8. Jika langsung membuat usulan untuk review, lanjut ke langkah 10. Jika out of scope, tunjukkan penghalangnya dan jelaskan bahwa sistem tidak memaksakan kode dari lima bab yang tersedia.

## 12. Langkah 8 — Jawab klarifikasi dengan bukti

Langkah ini **bersyarat**: lakukan jika transaksi live benar-benar memiliki pertanyaan terbuka. Status fixture **MKN-DEMO-003** atau **MKN-DEMO-009** saja tidak membuktikan ada kartu pertanyaan; pada pemeriksaan awal fixture tersebut tidak memiliki antrean klarifikasi nyata.

**Klik:** menu **Klarifikasi**.

**Lihat:** kartu **Pertanyaan yang membutuhkan jawaban**. Cocokkan uraian/atribut dan **Kiriman #...** dengan transaksi yang sedang didemokan. Angka setelah # adalah ID internal, bukan akhiran nomor referensi. Jangan menjawab semua kartu dalam perusahaan.

Jika ada banyak kiriman serupa dan ID belum diketahui, hentikan tindakan pada kartu sampai operator mencocokkan ID melalui daftar GET /api/v1/shipments di dokumentasi API. Jangan menebak berdasarkan nomor urut kartu.

Isi **Jawaban spesifikasi** hanya sesuai pertanyaan. Contoh jawaban berdasarkan DS-APX-M8422:

~~~text
Data ini berasal dari datasheet DEMO DS-APX-M8422 untuk seri APX-M8422-FL / WR.
Mesin filling mengisi cairan ke botol menggunakan dispenser piston volumetrik,
rentang dosis 50–1000 ml, kecepatan 24–48 botol/menit.
Catu daya 380V AC tiga fasa, 50Hz, daya 2,2 kW.
Konstruksi SUS304 dengan bagian kontak produk SUS316L.
Modul wrapping merupakan thermal heat-shrink tunnel dengan pengaturan suhu PID digital.
~~~

Pilih kalimat yang menjawab pertanyaan; jangan mengisi seluruh teks jika yang diminta hanya satu parameter. Jika fungsi barang, material, atau peruntukan yang ditanya tidak tercantum, jawab jujur belum terkonfirmasi dan perlu data pemasok. Jangan membuat spesifikasi baru untuk memaksa lolos klasifikasi.

**Klik:** **Kirim jawaban** satu kali.

**Lihat:** pemberitahuan **Tersimpan. Pemrosesan lanjutan mengikuti antrean.** Kartu yang dijawab hilang dari daftar terbuka. Kembali ke kiriman → Jejak → periksa run lanjutan.

**Narasi:**

> “Agent mengangkat kekurangan menjadi pertanyaan yang dapat ditindaklanjuti. Jawaban manusia dicatat, lalu sistem mengantrekan pemrosesan lanjutan untuk barang terkait.”

Jika pertanyaan baru muncul, itu cabang normal; jawab bila ada bukti. Hilangnya satu pertanyaan tidak otomatis menutup seluruh pertanyaan dalam kiriman.

## 13. Langkah 9 — Unggah dokumen pendukung dan lihat komunikasi

Untuk latihan lengkap, kembali sebagai staf ke transaksi baru → **Dokumen**. Lakukan satu dokumen, tunggu putaran pemrosesan selesai, baru lanjut ke dokumen berikutnya:

| Jenis dokumen yang dipilih | Berkas |
|---|---|
| Spesifikasi / datasheet | DS-APX-M8422.pdf |
| Packing list | PKL-DEMO-MKN-001.pdf |
| B/L atau AWB | BL-DEMO-MKN-001.pdf |

Untuk setiap baris: pilih jenis → pilih PDF → **Unggah dan proses** → periksa **Dokumen tersimpan**, **Checklist persyaratan**, dan run berikutnya.

**Lihat:** status kelengkapan Invoice, Packing list, dan B/L atau AWB. Mengunggah satu dokumen bertipe **Izin** tidak otomatis memenuhi seluruh kewajiban perizinan yang berbeda. Paket ini tidak menyediakan izin pemerintah palsu.

**Klik:** tab **Komunikasi** jika agent memiliki pertanyaan yang memicu pencatatan pesan.

**Lihat:** tujuan, subjek, isi permintaan, status, dan bukti waktu bila tersedia. Dengan alamat pemasok .example, hasil yang wajar adalah draf; mungkin belum ada pesan jika tidak ada pertanyaan.

**Narasi:**

> “Permintaan tambahan bisa tercatat sebagai tindak lanjut. Prototipe memakai SMTP sandbox lokal untuk skenario yang diizinkan. Status draf atau diterima adapter bukan bukti email sudah sampai ke pemasok eksternal. Balasan pada demo ini dimasukkan staf melalui menu Klarifikasi.”

Tidak ada tombol kirim email eksternal atau pembacaan otomatis balasan email yang perlu dijanjikan dalam demo ini.

## 14. Langkah 10 — Berpindah menjadi reviewer

**Klik:** **Keluar / ganti peran** → **Reviewer PPJK** → menu **Review ahli**.

**Lihat:** kartu di **Keputusan reviewer PPJK**, uraian barang, Kiriman #..., jenis review, dan kode usulan. Ambil hanya kartu milik transaksi live yang sudah dicocokkan. Jika tidak ada kartu, jangan berpura-pura fixture MKN-DEMO-002 sudah membuat antrean review: pada pemeriksaan awal fixture itu hanya memiliki status barang review, tanpa task review nyata.

Sebelum memutuskan, buka **Kiriman impor**, cari referensi yang sama, dan periksa tab **Barang** serta bukti yang tersedia. Kembali ke **Review ahli** untuk mengambil keputusan.

### Pilihan A — Setujui usulan yang sesuai

Isi **Catatan keputusan** dengan contoh berikut, sesuaikan barangnya:

~~~text
DEMO — Uraian dan fungsi APX-M8422-FL dicocokkan dengan invoice serta
datasheet DS-APX-M8422. Usulan diperiksa terhadap uraian katalog BTKI 2022.
Persetujuan ini untuk klasifikasi pada demonstrasi; tarif dan cakupan lartas
tetap perlu verifikasi tersendiri.
~~~

**Klik:** **Setujui**. Jangan mengisi kolom kode pengganti untuk tindakan ini.

### Pilihan B — Ubah kode setelah ada alasan yang dapat diperiksa

Hanya jika usulan memang perlu dikoreksi, isi **Kode pengganti (khusus Ubah kode)** dengan **8 digit tanpa titik**, misalnya **84224000** untuk barang wrapping pada contoh yang sesuai. Jangan mengganti kode filling menjadi wrapping hanya untuk memperlihatkan tombol.

Isi **Catatan keputusan**:

~~~text
DEMO — Barang APX-M8422-WR berfungsi membungkus kemasan dengan film
heat-shrink, bukan mesin pengisi botol. Koreksi ke 84224000 dilakukan
setelah mencocokkan fungsi pada datasheet dan uraian sumber katalog.
~~~

**Klik:** **Ubah kode**. Kode harus terdapat dalam katalog; delapan angka acak tidak cukup.

### Pilihan C — Tolak bila bukti belum memadai

Isi catatan alasan yang spesifik, lalu tekan **Minta data / tolak**.

**Penting:** pada implementasi sekarang tombol tersebut menandai penolakan dan memblokir kesiapan. Tombol itu **bukan jaminan otomatis membuat pertanyaan baru kepada pemasok**. Jangan memilihnya pada alur utama hanya untuk mencoba karena ada dampak status yang perlu ditangani setelahnya.

**Setelah Setujui/Ubah kode:** lihat pemberitahuan tersimpan, kartu keluar dari antrean terbuka, dan periksa barang yang bersangkutan pada detail kiriman. Pemrosesan kepatuhan lanjutan mengikuti antrean. Selesaikan semua task yang relevan; satu barang dapat memiliki review klasifikasi dan review kepatuhan terpisah.

**Narasi:**

> “Reviewer mempunyai kendali keputusan. Agent mengusulkan dan memberi bukti, tetapi keputusan akhir, koreksi, dan catatan manusia tetap tercatat. Approval satu barang tidak menghapus penghalang lain.”

## 15. Langkah 11 — Tunjukkan kesiapan dan pungutan secara jujur

**Klik:** kembali sebagai **Staf impor** → buka transaksi live → **Ringkasan**.

**Lihat:** daftar **Yang perlu diselesaikan**. Setelah review, penghalang masih mungkin berupa dokumen kurang, pertanyaan terbuka, review lain, pekerjaan aktif, verifikasi cakupan lartas, atau tarif belum terverifikasi.

**Klik:** **Dokumen**, lalu **Pungutan** untuk menunjukkan hubungannya dengan pemeriksaan.

**Narasi:**

> “Persetujuan HS tidak sama dengan seluruh kepatuhan selesai. Jika tarif atau cakupan izin belum dapat dibuktikan, sistem menahan kesiapan. Saya tidak mengisi angka nol atau menganggap bebas izin hanya agar status menjadi hijau.”

Pada katalog baru, tarif BM/PPN/PPh belum diverifikasi sehingga perhitungan baru dapat belum tersedia. **Versi UI ini tidak menyediakan formulir lengkap untuk memverifikasi tarif dan cakupan lartas sampai semua penghalang tersebut selesai.** Jangan mencari tombol yang tidak ada atau mengubah database untuk membuat demo tampak selesai.

### Catatan penting untuk angka pada Draf PIB

Draf PIB menjumlahkan hasil pungutan yang tersimpan. Kolom tanpa data ditampilkan kosong. Negara asal masih perlu diisi saat menyiapkan pengajuan eksternal.

Karena itu, **angka Draf PIB tidak boleh dipresentasikan sebagai bukti tarif aktual, total resmi seluruh barang, atau hasil AI yang telah terverifikasi**. Tab Pungutan dan Draf PIB bahkan dapat menampilkan angka berbeda karena dasar datanya berbeda. Gunakan bagian draf untuk menjelaskan struktur administrasi, bukan kebenaran tarif transaksi.

Jika juri menanyakan ketidaksamaan tersebut, jelaskan batasannya secara terbuka. Ini temuan pada versi aplikasi yang menjadi dasar panduan; bukan langkah yang harus disembunyikan dengan memilih layar tertentu.

## 16. Langkah 12 — Tunjukkan contoh akhir proses yang sudah disiapkan

Sampaikan perpindahan konteks terlebih dahulu:

> “Transaksi live tadi masih mengikuti pemeriksaan yang nyata. Sekarang saya pindah ke contoh fiktif yang status akhirnya sudah disiapkan untuk memperlihatkan tampilan tahap administrasi.”

**Klik:** **Kiriman impor** → cari **MKN-DEMO-001** → **Buka**.

**Lihat:**

1. Ringkasan: pada kondisi awal contoh ini siap dan tidak ada penghalang.
2. Barang: dua mesin, kode diterima 84223000 dan 84224000, status disetujui.
3. Dokumen: invoice, packing list, BL, dan datasheet tersimpan.
4. Jejak: fixture ini pada pemeriksaan awal memiliki **nol run AI**. Jangan menyebut status seed sebagai hasil eksekusi AI live.
5. Draf PIB: importir, pemasok, mata uang, dan struktur nilai draf. Tegaskan batasan perhitungan pada langkah sebelumnya.

**Narasi:**

> “Ini contoh status akhir yang disiapkan, bukan bukti AI baru saja memproses kiriman tersebut. Draf membantu menyusun informasi sebelum importir atau PPJK bekerja di sistem pengajuan resmi.”

Pada UI saat ini Draf PIB adalah tampilan data. **Tidak tersedia tombol unduh PDF/Excel PIB atau integrasi pengiriman ke CEISA** yang perlu diklik.

### Opsional — Catat pengajuan di luar aplikasi

Hanya lakukan jika bersedia mengubah fixture demo dari ready menjadi submitted.

**Klik:** **Tandai sudah diajukan di luar sistem** pada header MKN-DEMO-001.

**Lihat:** status berubah menjadi **Sudah diajukan di luar sistem** / submitted. Tombol ini muncul hanya ketika detail dianggap siap dan belum submitted/arrived. Jika tidak muncul atau ditolak, periksa penghalang; jangan memaksa melalui API.

**Narasi:**

> “Tombol ini mencatat bahwa pengajuan telah dilakukan di luar aplikasi. Tidak ada pengiriman nyata ke CEISA saat tombol ditekan.”

Untuk presentasi ulang, jangan mengharapkan fixture ini kembali ready otomatis. Jika tidak ingin mengubah data saat latihan, cukup tunjukkan contoh submitted **MKN-DEMO-006** atau **MKN-DEMO-013**.

### Status barang tiba

Tampilkan **MKN-DEMO-014** atau **MKN-DEMO-007** yang sudah berstatus barang tiba sebagai contoh tersimpan.

Untuk kiriman yang sudah diajukan, klik **Tandai barang tiba** saat kedatangan memang sudah dikonfirmasi. Status berubah menjadi arrived.

## 17. Langkah 13 — Peragakan dampak perubahan aturan sebagai admin

Lakukan bagian ini **paling akhir** karena simulasi dapat mengubah kesiapan contoh katup.

### Sebelum simulasi

Sebagai staf atau admin, cari **MKN-DEMO-012**. Tunjukkan dua barang pos 8481 dan status awal siap. Simpan catatan atau screenshot sebelum perubahan.

Untuk membandingkan barang yang sudah tiba, gunakan **MKN-DEMO-007** yang memiliki salah satu barang katup pos 8481. Jangan memilih contoh arrived yang semua barangnya berbeda bab lalu mengklaim sistem mengabaikannya karena status tiba; perbandingan harus relevan.

### Terbitkan simulasi

**Klik:** **Keluar / ganti peran** → **Admin** → **Aturan & dampak**.

1. Tunjukkan aturan yang berlabel **SIMULASI**.
2. Tunjukkan bagian **Referensi regulasi publik** yang memuat lima rujukan JDIH dan tautan **Buka dokumen resmi ↗**.
3. Jelaskan bahwa bibliografi peraturan resmi berbeda dari aturan yang dieksekusi pada skenario simulasi ini.
4. Tekan **Simulasikan aturan pos 8481**.
5. Pada dialog **Terbitkan aturan SIMULASI untuk perusahaan ini dan periksa kiriman yang terdampak?**, pilih **OK** bila memang ingin menjalankan simulasi.

**Lihat:** pemberitahuan hasil. Pemberitahuan menampilkan kiriman aktif yang kodenya cocok. Worker mengantrekan hitung ulang dan mencatat perubahan di jejak.

**Klik:** **Kiriman impor** → cari **MKN-DEMO-012** → **Buka**.

**Lihat:** contoh ready yang memiliki pos 8481 dapat berubah menjadi perlu review/belum lengkap. Kiriman submitted yang cocok tetap submitted dengan penanda dampak pada backend; UI belum memiliki tampilan flag yang lengkap, jadi jangan menjanjikan badge tersebut terlihat. Kiriman arrived yang cocok dikecualikan oleh pencarian dampak.

**Narasi:**

> “Ini perubahan aturan yang sengaja disimulasikan untuk perusahaan demo, bukan klaim aturan baru dari pemerintah. Sistem mencari kiriman yang cocok dengan pos HS dan mempertimbangkan tahap operasionalnya.”

Simulasi pada versi ini terutama menandai dampak/status; jangan menjanjikan seluruh checklist baru, task review baru, notifikasi eksternal, atau rekalkulasi otomatis pasti dibuat oleh klik tersebut. Periksa hasil yang memang terlihat. Jika contoh sudah tidak ready akibat latihan sebelumnya, jangan mengklaim ada transisi status baru.

## 18. Penutup presentasi

Gunakan narasi 30–45 detik berikut, sesuaikan hasil yang benar-benar terlihat:

> “Artha membantu staf mengubah dokumen impor menjadi daftar pekerjaan yang dapat diperiksa. Kita melihat invoice masuk, hasil pembacaan barang, penelusuran referensi, pertanyaan ketika informasi kurang, dan keputusan reviewer. Kesiapan tidak dipaksakan ketika bukti belum lengkap. Untuk tahap akhir, kita melihat contoh draf administrasi dan pemantauan dampak aturan. AI membantu prosesnya; manusia tetap memegang keputusan yang membutuhkan pertanggungjawaban.”

Jangan mengakhiri dengan klaim akurasi, kecepatan, kepatuhan penuh, atau integrasi eksternal yang tidak diuji dalam sesi tersebut.

## 19. Skenario cadangan ketika live demo tidak berjalan mulus

| Gejala | Yang dilakukan | Penjelasan ke juri |
|---|---|---|
| AI belum selesai dalam waktu panggung | Catat referensi/run, tunjukkan referensi HS/regulasi, lalu buka hasil latihan dengan run nyata | “Panggilan model masih berlangsung. Ini hasil latihan sebelumnya dengan jejak yang dapat diperiksa, bukan hasil live yang baru selesai.” |
| Run gagal | Baca langkah/error terakhir. Periksa health. Setelah penyebab diperbaiki dan tidak ada job aktif, Analisis ulang satu kali | Jangan menyebut proses gagal sebagai sukses; jangan klik ulang berkali-kali |
| Barang belum muncul | Periksa PDF berteks, jenis Invoice, run, dan status worker | Ekstraksi perlu dokumen yang dapat dibaca; scan gambar belum menjadi alur utama |
| Kode berbeda dari fixture | Periksa fungsi, bukti sumber, dan kelengkapan. Gunakan reviewer jika perlu | Kode fixture adalah referensi demo, bukan alasan membenarkan hasil tanpa tinjauan |
| Agent bertanya lebih banyak | Jawab sesuai datasheet atau akui belum ada data | Pertanyaan tambahan adalah cabang normal, bukan selalu error |
| Tidak ada kartu Klarifikasi/Review | Pastikan run live sudah membuat task; jangan mengandalkan status fixture | Fixture status tidak menjamin antrean task tersedia |
| Kartu milik transaksi lain | Cocokkan ID dan uraian terlebih dahulu | Jangan mengubah transaksi lain demi mempercepat demo |
| Angka pungutan kosong/berbeda dari Draf PIB | Periksa tarif, kurs, dan hasil tersimpan pada langkah 11 | Jangan mengklaim tarif resmi atau total agregat yang belum terbukti |
| Tombol pengajuan tidak muncul | Periksa Ringkasan, job, pertanyaan, review, dan checklist | Kesiapan memang ditahan bila ada penghalang |
| Email berstatus draf | Tampilkan isi draf bila ada | Bukan bukti terkirim ke pemasok; sandbox dan allowlist membatasi pengiriman |
| Pencarian HS kosong | Periksa ejaan/kode dan cakupan lima bab | Katalog terbatas; jangan mengarang kode atau menganggap seluruh BTKI tersedia |
| Kena rate limit / 429 | Hentikan percobaan berulang, tunggu sesuai respons, gunakan layar hasil latihan | Jangan melakukan spam login/analisis |
| Sesi berganti peran tanpa sengaja | Keluar lalu masuk dengan peran yang diperlukan dalam satu profil | Tab yang berbagi penyimpanan dapat berbagi token |

## 20. Checklist yang dibawa saat presentasi

### Sebelum mulai

- [ ] Health UP dan heartbeat worker segar.
- [ ] Ketiga akun demo dapat masuk.
- [ ] Empat PDF utama tersimpan lokal dan bisa dibaca.
- [ ] Referensi kiriman demo baru sudah ditentukan dan unik.
- [ ] Satu hasil latihan dengan run AI nyata sudah siap dibuka.
- [ ] Kondisi MKN-DEMO-001 dan MKN-DEMO-012 sudah dicatat sebelum tindakan.
- [ ] Presenter tahu perbedaan data live, fixture seed, dan data referensi resmi.
- [ ] Tidak menekan Reset data demo.

### Bukti yang harus terlihat

- [ ] Kiriman baru tercipta dengan perusahaan sesuai akun.
- [ ] Invoice tersimpan dan run/antrean dapat ditelusuri.
- [ ] Jumlah/uraian barang dibandingkan dengan invoice.
- [ ] Sumber HS dan status belum terverifikasi diperlihatkan.
- [ ] Jika ada klarifikasi, jawaban sesuai bukti dicatat pada transaksi yang benar.
- [ ] Jika ada review, keputusan dan catatan manusia diperlihatkan.
- [ ] Penghalang yang tersisa dijelaskan tanpa dipaksa hilang.
- [ ] Perpindahan ke contoh status akhir disebutkan secara terbuka.
- [ ] Draf PIB dan pencatatan submitted dibedakan dari pengajuan resmi.
- [ ] Simulasi aturan ditunjukkan sebagai simulasi, bila dijalankan.

### Setelah selesai

- [ ] Catat referensi, ID/run jika diketahui, keputusan yang diambil, dan dokumen yang diunggah.
- [ ] Catat fixture yang berubah submitted atau terkena simulasi.
- [ ] Simpan screenshot yang merekam hasil sebenarnya.
- [ ] Catat bagian yang gagal/terhambat dan durasi nyata; jangan mengganti catatan itu dengan klaim sukses.
- [ ] Jangan reset database untuk merapikan latihan tanpa rencana pemulihan data.

## 21. Jawaban singkat untuk pertanyaan juri

**“Apa bedanya dengan chatbot?”**

“Artha menyimpan pekerjaan per kiriman dan per barang, dokumen, pertanyaan, keputusan reviewer, serta jejak proses. Hasilnya menjadi tindak lanjut yang terstruktur, bukan hanya jawaban percakapan.”

**“Apakah kode HS ini pasti benar?”**

“Belum ada klaim akurasi menyeluruh. Katalog memakai referensi resmi pada cakupan lima bab, tetapi pemilihan kode tetap memerlukan spesifikasi yang cukup dan tinjauan ahli.”

**“Kenapa tidak langsung siap setelah reviewer menyetujui?”**

“Klasifikasi hanya salah satu pemeriksaan. Dokumen, cakupan izin, tarif, pertanyaan, dan pekerjaan yang belum selesai masih dapat menahan kesiapan.”

**“Apakah sistem sudah mengambil semua aturan terbaru?”**

“Belum. Katalog ini snapshot BTKI 2022, dengan bibliografi beberapa perubahannya. Itu belum merupakan konsolidasi semua tarif dan lartas terkini.”

**“Apakah email dan PIB benar-benar terkirim?”**

“Email demonstrasi dibatasi ke draf/SMTP sandbox sesuai konfigurasi. PIB tidak dikirim dari aplikasi; submitted adalah pencatatan proses yang dilakukan di luar sistem.”

**“Kenapa ada angka pajak di draf ketika tarif belum diverifikasi?”**

“Draf memuat estimasi yang tersimpan dari analisis. Tarif snapshot dan data kiriman tetap perlu diverifikasi sebelum pengajuan.”

**“Apakah aplikasi siap untuk transaksi produksi?”**

“Ini MVP untuk membuktikan alur. Verifikasi tarif/lartas, konsistensi draf dan agregat pungutan, transisi arrived, kedalaman integrasi eksternal, serta performa model masih merupakan pekerjaan sebelum penggunaan produksi.”

## 22. Catatan verifikasi panduan dan pemeliharaan

Panduan diperiksa terhadap label frontend, route API/OpenAPI, manifest fixture, isi datasheet, dan pembacaan API live tanpa menjalankan perubahan transaksi. Pemeriksaan penulisan panduan tidak melakukan upload, review, jawaban klarifikasi, pengajuan, simulasi aturan, atau reset data.

Temuan yang harus diperiksa ulang jika aplikasi diperbarui:

| Temuan pada versi acuan | Dampak pada demo |
|---|---|
| Fixture needs_review / needs_clarification tidak otomatis memiliki task antrean | Gunakan transaksi hasil analisis nyata untuk tombol review/jawaban |
| Simulasi aturan mempunyai teks hasil yang masih menyebut contoh lama dan tampilan flag submitted terbatas | Verifikasi perubahan pada kiriman yang benar; jangan mengklaim badge/checklist yang tidak terlihat |
| Tidak tersedia UI lengkap untuk menyelesaikan verifikasi tarif/lartas pada pipeline baru | Akhiri jalur live pada hasil dan penghalang yang nyata; tahap siap memakai fixture yang dijelaskan |

Kondisi awal fixture yang dibaca ketika panduan dibuat: MKN-DEMO-001 (ID8) siap; MKN-DEMO-012 (ID19) siap; MKN-DEMO-005 (ID12) kekurangan BL; MKN-DEMO-006 (ID13) submitted. ID hanya snapshot, bukan nilai yang harus dihafalkan atau dipakai selamanya.

**Prinsip penyajian:** tunjukkan apa yang benar-benar dilakukan sistem, sebutkan asumsi data demo, dan jelaskan batas kemampuan pada saat itu. Demo yang kuat memperlihatkan manfaat sekaligus penanganan ketidakpastian secara dapat dipertanggungjawabkan.
