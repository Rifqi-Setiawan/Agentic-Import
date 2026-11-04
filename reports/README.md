# Status laporan evaluasi

Laporan eval_report_agent.json dan retrieval_only lama dipertahankan sebagai artefak historis audit, BUKAN bukti benchmark valid. Summary lama menyebut HS8 100% tetapi prediksi exact-match hanya57/60; asal eksekusinya belum dapat direproduksi. Jangan gunakan angka itu untuk proposal atau klaim produk. scripts/eval_hs.py menghitung metrik dari prediksi, tetapi benchmark live final memerlukan run baru, dataset/prompt/model version, serta bukti gateway. tests/live_pipeline_smoke.py menguji operasional dua invoice baru, bukan akurasi dataset60barang.
