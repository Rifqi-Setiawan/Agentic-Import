# Evaluasi pencarian HS

Uji retrieval 7 November 2026 menjalankan ranking yang dipakai Artha pada katalog lima bab BTKI 2022. Dari 60 label internal, 49 kode acuan ada di katalog. Sebelas lainnya tercatat sebagai pengecualian. [Prediksi, daftar pengecualian, dan checksum](eval_retrieval_20261107.json)

| Metrik pada 49 sampel | Hasil |
| --- | ---: |
| Top-1 HS6 | 40,82% |
| Top-1 HS8 | 30,61% |
| Top-3 HS8 | 38,78% |
| Recall@10 | 51,02% |

Label internal belum diverifikasi PPJK. Hasil ini mengukur kecocokan terhadap label tersebut dan berguna untuk regresi. Laporan lama disimpan untuk riwayat. Asal eksekusi dan angka di laporan lama belum terverifikasi.

Jalankan kembali dari root repo dengan `PYTHONPATH=. python scripts/eval_hs.py --mode retrieval_only --out reports/eval_retrieval.json`. Evaluasi agent memerlukan gateway dan model yang diotorisasi. Gunakan `--mode agent` untuk mengukur usulan model dan frekuensi klarifikasi pada sampel sulit.
