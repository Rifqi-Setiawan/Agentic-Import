# Model bisnis

## Ringkasan

Pembeli pertama yang dituju adalah PPJK (pengusaha pengurusan jasa kepabeanan). Importir menengah dengan staf impor sendiri menyusul, lalu platform logistik lewat API. Pendapatan berasal dari langganan per pengguna ditambah kuota kiriman, dengan biaya tambahan per kiriman di atas kuota. Yang dijual bukan pencarian kode HS, tetapi waktu kerja: agent menyiapkan satu kiriman dari invoice sampai siap diajukan, termasuk mengejar dokumen yang kurang ke pemasok.

Rubrik menilai bagian ini di kriteria "Dampak Masalah dan Nilai Bisnis" (10%): urgensi masalah, target pengguna yang spesifik, metrik terukur seperti penghematan waktu atau biaya, dan potensi skalabilitas sebagai produk komersial.

## Masalah dalam angka

| Fakta | Angka | Sumber | Catatan |
| --- | --- | --- | --- |
| Ukuran BTKI 2022 | 99 bab, 11.552 pos tarif | DDTCNews | Alasan klasifikasi manual lambat dan rawan salah |
| Denda kekurangan bea masuk | Berjenjang 100% sampai 1.000% dari kekurangan pembayaran, sesuai besarnya kekurangan | PP 39/2019, dirangkum Pajakku | Artikel membahas salah nilai pabean. Aturannya berlaku untuk kekurangan bayar secara umum, jadi salah kode yang membuat bea masuk kurang bayar bisa terkena. Cek pasal aslinya sebelum dikutip di proposal |
| Lama pemeriksaan | Jalur kuning 3 sampai 5 hari kerja, jalur merah 5 sampai 14 hari kerja | ARMOCargo | Artikel penyedia jasa yang menyebut salah kode HS sebagai penyebab utama jalur merah. Ini klaim penyedia jasa, bukan statistik resmi |
| Biaya jasa pengurusan PIB | Sekitar Rp500.000 sampai Rp2.000.000 per PIB | ARMOCargo | Perkiraan penyedia jasa |
| Biaya PPJK per kontainer | Jasa Rp2 sampai 7 juta, dokumentasi Rp0,5 sampai 1,5 juta, storage atau demurrage Rp200.000 sampai Rp500.000 per hari per kontainer | M2B (penyedia jasa) | Perkiraan, angka di badan artikel dan tabelnya sedikit berbeda |
| Siapa yang mengurus | Importir yang tidak menguasai ketentuan kepabeanan dapat menguasakan ke PPJK. PPJK wajib terdaftar di DJBC dan memiliki ahli kepabeanan | DDTCNews | Dasar memilih PPJK sebagai pembeli pertama |

Yang belum ditemukan sumber resminya: jumlah PPJK terdaftar dan jumlah importir aktif per tahun. Cari di laporan tahunan DJBC atau BPS sebelum menyebut ukuran pasar. Jangan menulis angka ukuran pasar tanpa sumber.

## Segmen pelanggan

| Tahap | Segmen | Masalah utama | Alasan mau membayar |
| --- | --- | --- | --- |
| 1 (utama) | PPJK kecil dan menengah | Banyak kiriman dari banyak klien, ahli kepabeanan terbatas, salah kode merusak reputasi di mata klien | Satu ahli bisa menangani lebih banyak PIB tanpa menambah orang. Kekurangan dokumen dikejar agent, bukan staf |
| 2 | Importir menengah dengan staf impor sendiri (manufaktur, distributor) | Staf bukan ahli tarif, aturan lartas berubah, barang tertahan karena izin belum siap | Dokumen siap sebelum barang tiba, peringatan saat aturan baru berdampak, perkiraan pungutan untuk perencanaan kas |
| 3 | Freight forwarder, platform logistik, marketplace lintas negara | Banyak SKU yang perlu kode HS dan cek izin dengan cepat | API klasifikasi dan cek lartas per panggilan |

## Aliran pendapatan

| Paket | Untuk | Isi | Cara menagih |
| --- | --- | --- | --- |
| Uji coba | Semua | 14 hari atau 10 kiriman, mana yang lebih dulu | Gratis |
| PPJK | Segmen 1 | Semua fitur, banyak klien (perusahaan) dalam satu akun, tingkat otonomi bisa diatur per klien | Per pengguna per bulan, termasuk kuota kiriman. Kelebihan kiriman ditagih per kiriman |
| Importir | Segmen 2 | Satu perusahaan, pemantau aturan, inbox agent | Langganan bulanan dengan kuota kiriman lebih kecil |
| API | Segmen 3 | Endpoint klasifikasi dan cek lartas | Per panggilan, paket volume |
| Onboarding | Segmen 1 dan 2 | Memasukkan katalog barang yang pernah diklasifikasi ke memori perusahaan | Biaya sekali di awal |

Angka harga sengaja tidak diisi karena belum ada data. Prinsip penetapannya: harga per kiriman harus jauh di bawah biaya jasa pengurusan satu PIB (Rp500.000 sampai Rp2.000.000 menurut sumber penyedia jasa) agar mudah diterima, dan di atas biaya LLM plus server per kiriman agar untung. Validasi lewat wawancara singkat dengan 3 sampai 5 PPJK bila sempat. Bila belum sempat, tulis di proposal sebagai rencana validasi, bukan sebagai fakta.

## Struktur biaya

| Biaya | Dari mana dihitung |
| --- | --- |
| LLM per kiriman | Kolom `prompt_tokens` dan `completion_tokens` di `agent_runs` dikali harga model. Laporkan rata-rata per kiriman dari hasil uji, bukan perkiraan |
| Server | VPS dan database. Embedding berjalan lokal sehingga tidak ada biaya API embedding |
| Email | Gmail cukup untuk prototipe. Saat produksi pakai layanan email transaksional |
| Kurasi data | Pembaruan BTKI, lartas, dan tarif butuh orang yang paham kepabeanan. Ini biaya non-teknis terbesar dan harus disebut jujur |
| Penjualan | Demo langsung ke PPJK, kemitraan dengan asosiasi PPJK |

## Cara mengukur dampak untuk proposal

Rubrik meminta metrik terukur. Lakukan uji waktu kecil sebelum 8 November:

1. Ambil kiriman `MKN-IMP-2611-011` (5 barang).
2. Minta 3 orang (idealnya staf impor atau PPJK, minimal teman yang belum pernah melihat jawabannya) menentukan kode HS, mengecek izin di INSW, dan menghitung pungutan secara manual memakai BTKI. Catat waktu dan jumlah kesalahan.
3. Jalankan agent untuk kiriman yang sama. Catat durasi dari `agent_runs` ditambah waktu staf menjawab pertanyaan dan menyetujui hasil.
4. Laporkan median waktu manual dan median waktu dengan agent, jumlah kesalahan, akurasi set uji, dan biaya LLM per kiriman.

Rumus penghematan yang boleh dipakai di proposal, dengan angka dari uji di atas: penghematan per bulan = jumlah kiriman per bulan × (waktu manual per kiriman − waktu dengan agent per kiriman) × biaya staf per jam. Sebutkan bahwa angkanya berasal dari uji kecil dengan sampel terbatas.

## Keunggulan dan risiko bisnis

- **Memori per perusahaan**: setiap keputusan reviewer menambah memori, jadi agent makin cocok dengan barang perusahaan itu seiring pemakaian. Data ini milik pelanggan dan sulit ditiru pesaing.
- **Proaktif**: pemantau aturan dan tindak lanjut ke pemasok bekerja tanpa diminta. Alat pencarian kode HS biasa tidak melakukan ini.
- **Jejak audit**: setiap kode punya alasan, kutipan sumber, dan nama pemutus. Ini penting untuk PPJK saat ada pemeriksaan.
- **Sebelum pitching**, cari dan catat alat yang sudah ada (layanan pencarian kode HS, modul di software kepabeanan atau ERP, fitur INSW). Jangan mengklaim "pertama di Indonesia" tanpa bukti.
- **Risiko**: data regulasi harus selalu terkini, tanggung jawab hukum tetap di PPJK atau importir (agent tidak pernah mengajukan PIB), dan kepercayaan pengguna dibangun lewat tingkat otonomi yang bisa diatur.

## Skalabilitas

- **Teknis**: worker bisa ditambah tanpa mengubah kode karena antrean memakai `FOR UPDATE SKIP LOCKED`. Menambah bab hanya menambah data seed, bukan kode.
- **Produk**: semua bab BTKI, integrasi resmi bila API pemerintah tersedia dan diizinkan, tarif preferensi perjanjian dagang (FTA) yang nilainya tinggi bagi importir, bea masuk tambahan.

## Jawaban singkat untuk pertanyaan juri

| Pertanyaan | Jawaban |
| --- | --- |
| Siapa yang membayar? | PPJK dulu, karena mereka menangani volume besar dan sudah terbiasa membayar alat kerja. Importir menengah menyusul |
| Kalau agent salah lalu kena denda? | Agent tidak pernah mengajukan PIB. Barang berkeyakinan rendah wajib ditinjau ahli, semua keputusan punya jejak, dan tingkat otonomi bisa diturunkan ke assist |
| Apa bedanya dengan mencari kode HS di INSW? | INSW adalah sumber data. Agent ini memakai data itu untuk menyelesaikan pekerjaan: membaca invoice, memilih kode dengan alasan, menghitung pungutan, menyiapkan dokumen, mengejar pemasok, dan memantau aturan baru |
| Siapa yang memperbarui data regulasi? | Kurasi oleh tim yang paham kepabeanan, dibantu agent pemantau. Di prototipe ini feed aturan masih simulasi dan diberi label jelas |
| Berapa biaya per kiriman? | Sebutkan angka biaya LLM per kiriman dari hasil uji tim, bukan perkiraan |

## Sumber

- [DDTCNews: BTKI 2022 resmi diperbarui](https://news.ddtc.co.id/berita/nasional/38059/berlaku-1-april-2022-buku-tarif-kepabeanan-indonesia-resmi-diperbarui)
- [Pajakku: tarif sanksi denda bea masuk menurut PP 39/2019](https://pajakku.com/artikel/tarif-sanksi-denda-bea-masuk-akibat-kesalahan-pelaporan-nilai-barang-impor-beserta-contohnya)
- [Teks PP 39/2019 di JDIH Kemenkeu](https://jdih.kemenkeu.go.id/fullText/2019/39TAHUN2019PP.pdf)
- [ARMOCargo: panduan customs clearance 2026](https://armocargo.com/blog/panduan-customs-clearance-indonesia-2026-proses-jalur-biaya-dan-cara-mempercepatnya/)
- [M2B: biaya PPJK impor via Tanjung Priok 2026](https://m2b.co.id/blog/panduan-lengkap-cek-7-biaya-ppjk-impor-tanjung-priok-2026)
- [DDTCNews: importir dapat memakai jasa PPJK](https://news.ddtc.co.id/berita/nasional/1802468/tak-paham-ketentuan-impor-importir-bisa-manfaatkan-jasa-ppjk)
