# Frontend

## Peta halaman dan hak akses

Frontend memakai Next.js App Router. Semua halaman kecuali `/login` dilindungi: bila token tidak ada atau kedaluwarsa, pengguna diarahkan ke `/login`. Menu samping hanya menampilkan halaman yang boleh dibuka peran tersebut.

| Path | Nama di menu | Staf | Reviewer | Admin | Endpoint utama |
| --- | --- | --- | --- | --- | --- |
| `/login` | - | Ya | Ya | Ya | `POST /auth/login` |
| `/dashboard` | Dashboard | Ya | Ya | Ya | `GET /dashboard/summary` |
| `/shipments` | Kiriman | Ya | Ya | Ya | `GET /shipments` |
| `/shipments/new` | Kiriman baru | Ya | Tidak | Ya | `POST /shipments`, `POST /shipments/{id}/documents` |
| `/shipments/[id]` | (detail) | Ya | Ya | Ya | Lihat tabel tab di bawah |
| `/clarifications` | Pertanyaan agent | Ya | Tidak | Ya | `GET /clarifications`, `POST /clarifications/{id}/answer` |
| `/reviews` | Antrean review | Tidak | Ya | Ya | `GET /reviews` |
| `/reviews/[id]` | (detail) | Tidak | Ya | Ya | `GET /reviews/{id}`, `POST /reviews/{id}/decision` |
| `/regulations` | Aturan | Ya | Ya | Ya | `GET /regulations`, `POST /regulations`, `POST /regulations/simulate-demo` |
| `/regulations/[id]` | (detail dampak) | Ya | Ya | Ya | `GET /regulations/{id}/impacts` |
| `/hs-search` | Cari kode HS | Ya | Ya | Ya | `GET /hs-codes/search`, `GET /hs-codes/{code}` |
| `/admin` | Admin | Tidak | Tidak | Ya | `GET /admin/users`, `POST /admin/demo/reset` |

Halaman detail kiriman `/shipments/[id]` memakai tab supaya juri tidak tersesat:

| Tab | Isi | Endpoint |
| --- | --- | --- |
| Ringkasan | Data kiriman, status, risiko, ringkasan terakhir agent, tombol aksi | `GET /shipments/{id}` |
| Barang & kode HS | Tabel barang dengan kode HS, keyakinan, risiko, dan panel alasan | `GET /shipments/{id}/items` |
| Izin & lartas | Izin per barang beserta instansi, tahap, dan dasar hukum | sama dengan di atas |
| Pungutan | Rincian BM, PPN, PPh 22 per barang dan total, kurs yang dipakai | `GET /shipments/{id}/duties` |
| Dokumen & checklist | Dokumen terunggah dan checklist kekurangan | `GET /shipments/{id}/documents`, `GET /shipments/{id}/checklist` |
| Draf PIB | Pratinjau draf, masalah yang menghalangi, tombol unduh PDF | `GET /shipments/{id}/pib-draft` |
| Komunikasi | Email yang dikirim agent ke pemasok, balasan yang masuk beserta lampirannya, tugas staf yang dibuat agent, dan draf yang menunggu persetujuan (tingkat assist) | `GET /shipments/{id}/messages, POST /messages/{id}/send` |
| Jejak agent | Panel langkah agent secara langsung dan riwayat run | `GET /runs/{id}/steps`, SSE `GET /runs/{id}/stream` |

Panel jejak agent juga muncul sebagai panel samping yang bisa dibuka dari tab mana pun saat analisis berjalan. Panel ini adalah tampilan terpenting untuk juri.

Topbar di semua halaman memuat lonceng notifikasi. Lonceng memanggil `GET /notifications` setiap 30 detik (TanStack Query `refetchInterval`), menampilkan jumlah belum dibaca, dan menyediakan tombol "Tandai semua dibaca" (`POST /notifications/read-all`). Klik satu notifikasi memanggil `POST /notifications/{id}/read` lalu membuka halaman terkait. Tidak perlu halaman `/notifications` terpisah.

## Detail halaman dan komponen

### Struktur folder

```
frontend/src/
  app/
    (auth)/login/page.tsx
    (app)/layout.tsx              # sidebar, topbar + lonceng notifikasi, guard peran
    (app)/dashboard/page.tsx
    (app)/shipments/page.tsx
    (app)/shipments/new/page.tsx
    (app)/shipments/[id]/page.tsx  # tab via ?tab=summary|items|lartas|duties|docs|messages|pib|trace
    (app)/clarifications/page.tsx
    (app)/reviews/page.tsx
    (app)/reviews/[id]/page.tsx
    (app)/regulations/page.tsx
    (app)/regulations/[id]/page.tsx
    (app)/hs-search/page.tsx
    (app)/admin/page.tsx
  components/
    ui/                           # hasil generate shadcn, jangan diedit manual
    shipment/  agent/  review/  common/
  lib/
    api.ts          # fetch wrapper, sisip token, ubah error envelope jadi ApiError
    auth.ts         # simpan token, decode peran, logout
    sse.ts          # hook useRunStream
    format.ts       # rupiah, tanggal WIB, kode HS bertitik
    schemas.ts      # zod untuk form, mengikuti skema Pydantic
  types/api.ts      # di-generate dari OpenAPI (openapi-typescript)
```

Tipe TypeScript di-generate dari `/openapi.json` FastAPI dengan `npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts`. Jangan menulis tipe respons secara manual supaya frontend dan backend tidak berbeda.

### /login

Form email dan password (react-hook-form + zod). Di bawah form ada tiga tombol "Masuk sebagai staf / reviewer / admin" yang mengisi akun demo, supaya juri tidak perlu mengetik. Token disimpan di memori dan `localStorage` (dibungkus try/catch). Setelah login, arahkan ke `/dashboard`.

### /dashboard

- Empat kartu angka: kiriman aktif, menunggu jawaban staf, menunggu review, terdampak aturan baru.
- Daftar "Perlu tindakan Anda" sesuai peran: staf melihat pertanyaan agent dan kiriman `needs_clarification`, reviewer melihat antrean review.
- Daftar 5 run agent terakhir dengan status dan durasi.
- Banner kuning bila ada aturan baru yang berdampak dan belum dibaca, dengan tautan ke `/regulations/[id]`.

### /shipments

Tabel dengan kolom: nomor referensi, perusahaan, pemasok, negara asal, ETA, jumlah barang, status, risiko, diperbarui. Filter status, risiko, dan pencarian teks. Paginasi server (`page`, `page_size=20`). Klik baris membuka detail.

### /shipments/new

Wizard tiga langkah:

1. **Data kiriman**: perusahaan (dropdown), pemasok, email pemasok (opsional, dibutuhkan agar agent bisa meminta dokumen sendiri), negara asal, pelabuhan tujuan, ETA, incoterm, mata uang.
2. **Unggah dokumen**: drag and drop invoice dan packing list (PDF, JPG, PNG, maks 10 MB per file). Setiap file menampilkan progres unggah dan jenis dokumen yang bisa diubah. Begitu invoice selesai terunggah, agent langsung mulai bekerja tanpa tombol, dan panel jejak kecil muncul di sisi kanan wizard.
3. **Selesai**: ringkasan kiriman dan tombol "Lihat agent bekerja" ke `/shipments/[id]?tab=trace`.

Kiriman disimpan sebagai `draft` sejak langkah 1, jadi kalau halaman tertutup data tidak hilang.

### /shipments/\[id\]

Header berisi nomor referensi, `StatusBadge`, `RiskBadge`, dan tombol aksi yang muncul sesuai status:

| Status | Tombol yang muncul |
| --- | --- |
| `draft` | Analisis dengan agent |
| `analyzing` | Lihat jejak agent (tombol lain dinonaktifkan) |
| `needs_clarification` | Jawab pertanyaan agent |
| `needs_review` | (staf) Menunggu reviewer; (reviewer) Buka review |
| `ready` | Unduh draf PIB, Tandai sudah diajukan |
| `submitted` | Tandai barang tiba |
| `failed` | Coba analisis ulang, Lihat error |

Tab **Barang & kode HS** berisi tabel barang. Setiap baris bisa dibuka (accordion) untuk menampilkan `RationaleCard`. Tab **Jejak agent** berisi `AgentTracePanel` dalam ukuran penuh.

### /clarifications

Daftar pertanyaan terbuka dari agent, dikelompokkan per kiriman. Klik membuka `ClarificationDialog`.

### /reviews dan /reviews/\[id\]

Antrean berisi barang dengan keyakinan rendah atau risiko tinggi. Halaman detail memakai dua kolom: kiri berisi data barang dan kutipan dokumen asli, kanan berisi kandidat kode dari agent beserta skor dan alasan. Reviewer memilih salah satu dari tiga keputusan:

- **Setujui** (`action: approve`): kode agent diterima, catatan opsional.
- **Ubah kode** (`action: modify`): reviewer memilih kode lain lewat `HsCodePicker` dan wajib mengisi catatan alasan.
- **Tolak** (`action: reject`): barang butuh data tambahan, catatan wajib (misalnya "Minta datasheet ke pemasok"). Staf mendapat notifikasi berisi catatan ini, melengkapi data barang lewat `PATCH /items/{id}`, lalu menjalankan `POST /items/{id}/reanalyze`.

Keputusan setujui dan ubah kode masuk ke `classification_memory`.

### /regulations dan /regulations/\[id\]

Daftar aturan yang sudah dimuat, dengan label **SIMULASI** berwarna ungu untuk feed demo. Tombol "Jalankan simulasi aturan baru" (hanya admin, sesuai hak akses API) memanggil `POST /regulations/simulate-demo`. Detail aturan menampilkan ringkasan perubahan, daftar kiriman terdampak, dan perbandingan sebelum dan sesudah (izin, pungutan).

### /hs-search

Kolom pencarian bebas yang memanggil pencarian hybrid yang sama dengan agent. Hasil menampilkan kode bertitik, uraian, skor, dan tombol lihat detail (catatan bab, BM, lartas). Halaman ini berguna saat demo untuk menunjukkan bahwa retrieval nyata, bukan karangan model.

### /admin

Daftar pengguna, tombol reset data demo dengan dialog konfirmasi, pilihan tingkat otonomi agent (AutonomySwitch), dan status layanan dari GET /health (database dan heartbeat worker).

### Komponen inti

| Komponen | Props utama | Perilaku |
| --- | --- | --- |
| `AgentTracePanel` | `runId`, `compact?` | Memakai `useRunStream(runId)`. Setiap langkah tampil sebagai kartu: ikon jenis (node, tool, llm, interrupt), nama, durasi, ringkasan input dan output. Kartu tool bisa dibuka untuk melihat argumen JSON dan hasil. Otomatis scroll ke bawah kecuali pengguna sedang scroll ke atas. Saat `run_status` menjadi `paused`, tampil tombol "Jawab sekarang". |
| `StatusBadge` | `status` | Warna dan label sesuai tabel konvensi di bawah. |
| `RiskBadge` | `level` | Rendah hijau, sedang kuning, tinggi merah. |
| `ConfidenceMeter` | `value`, `threshold=0.70` | Bar 0 sampai 100%. Di bawah ambang diberi garis merah dan teks "Perlu review". |
| `RationaleCard` | `classification` | Menampilkan kode final, 3 kandidat teratas beserta skor, alasan dalam bahasa Indonesia, kutipan sumber (catatan bab atau uraian BTKI) dengan tautan ke `/hs-search`, dan asal keputusan (agent, memori, reviewer). |
| `ClarificationDialog` | `clarification` | Menampilkan pertanyaan, konteks barang, dan pilihan jawaban bila agent menyediakan opsi, ditambah kolom teks bebas. Submit memanggil `POST /clarifications/{id}/answer`, lalu run agent dilanjutkan otomatis. |
| `DutyTable` | `duties` | Kolom CIF, BM, PPN, PPh 22, total per barang, plus baris total. Hover pada angka menampilkan rumus dan tarif yang dipakai. |
| `HsCodePicker` | `onSelect` | Combobox dengan pencarian ke `/hs-codes/search`, debounce 300 ms. |
| `DocumentDropzone` | `shipmentId` | Validasi tipe dan ukuran di klien sebelum unggah. |
| `EmptyState` | `title`, `action?` | Dipakai di semua daftar kosong. |
| `PlanCard` | `runId` | Kartu di atas AgentTracePanel berisi rencana terbaru dari plan\_shipment: ringkasan, grup barang, barang yang ambigu, dokumen yang kurang. Bila ada revisi, tampil label "Rencana diperbarui" beserta alasannya dan tombol untuk melihat versi sebelumnya |
| `MessageList` | `shipmentId` | Daftar email per kiriman dengan arah (keluar atau masuk), status, waktu, dan lampiran. Draf bisa diubah dan dikirim. Email buatan agent diberi label "Dikirim agent" |
| `AutonomySwitch` | `value, onChange` | Pilihan assist atau auto di halaman admin, dengan penjelasan singkat apa yang berubah di tiap tingkat. Menyimpan lewat PATCH /admin/company-settings |

### Hook useRunStream

```ts
export function useRunStream(runId: string) {
  // 1. GET /runs/{runId}/steps -> isi daftar langkah lama, lastSeq = seq terakhir
  // 2. POST /runs/{runId}/stream-token -> { token } (berlaku 10 menit)
  // 3. new EventSource(`${API}/runs/${runId}/stream?token=${token}&after_seq=${lastSeq}`)
  // 4. event "step"       -> tambahkan ke daftar bila seq > lastSeq, simpan lastSeq
  //    event "run_status" -> set status (queued, running, paused, succeeded, failed,
  //                          cancelled), invalidate query shipment dan items
  //    event "heartbeat"  -> abaikan
  //    event "end"        -> tutup koneksi, jangan sambung ulang
  // 5. onerror: tutup, minta token baru, sambung ulang dengan after_seq = lastSeq
  //    (jeda 1 s, 2 s, 4 s, maks 10 s)
  return { steps, status, connected };
}
```

Token stream dipakai karena `EventSource` tidak bisa mengirim header `Authorization`.

## Konvensi UI

### Status kiriman

| Status | Label di UI | Warna badge |
| --- | --- | --- |
| `draft` | Draf | Abu-abu |
| `analyzing` | Sedang dianalisis | Biru, dengan animasi titik |
| `needs_clarification` | Perlu jawaban | Oranye |
| `needs_review` | Perlu review | Kuning |
| `ready` | Siap diajukan | Hijau |
| `submitted` | Sudah diajukan | Teal |
| `arrived` | Barang tiba | Hijau tua |
| `failed` | Gagal | Merah |

### Status barang

| Status | Label di UI | Warna badge |
| --- | --- | --- |
| `extracted` | Terbaca dari dokumen | Abu-abu |
| `classifying` | Sedang diklasifikasi | Biru |
| `needs_clarification` | Perlu jawaban | Oranye |
| `classified` | Terklasifikasi | Hijau muda |
| `needs_review` | Perlu review | Kuning |
| `approved` | Disetujui (reviewer atau otomatis) | Hijau |
| `out_of_scope` | Di luar cakupan | Ungu |

Status run agent (`queued`, `running`, `paused`, `succeeded`, `failed`, `cancelled`) hanya tampil di panel jejak dan riwayat run, dengan label Antre, Berjalan, Menunggu jawaban, Selesai, Gagal, Dibatalkan.

### Format angka dan teks

- Rupiah: `Rp 15.139.000` memakai `Intl.NumberFormat('id-ID')`, tanpa desimal.
- Mata uang asing: `USD 4,857.89` dengan dua desimal.
- Kode HS selalu tampil bertitik: `3304.99.30`. Di API dan database disimpan tanpa titik (`33049930`).
- Tanggal dan jam dalam WIB: `1 Nov 2026, 14.30 WIB`.
- Persen keyakinan dibulatkan tanpa desimal: `82%`.
- Seluruh teks UI dalam bahasa Indonesia. Istilah kepabeanan memakai istilah resmi (BM, PPN, PPh Pasal 22, lartas, PIB).

### Loading, error, kosong

- Loading pertama memakai skeleton, bukan spinner di tengah layar.
- Tombol yang sedang memproses dinonaktifkan dan menampilkan spinner kecil, supaya tidak terjadi klik ganda.
- Error API ditampilkan sebagai toast dengan `message` dari envelope error, plus `request_id` kecil di bawahnya untuk debugging.
- Error `401` menghapus token dan mengarahkan ke `/login`. Error `403` menampilkan halaman "Anda tidak punya akses".
- Error validasi form (`422`) dipetakan ke field yang bersangkutan dari `details`.
- Setiap daftar kosong memakai `EmptyState` dengan ajakan tindakan, misalnya "Belum ada kiriman. Buat kiriman pertama".

### Penanda wajib

- Setiap hasil dari agent diberi label kecil "Dibuat agent" dan setiap keputusan manusia diberi label "Diputuskan oleh {nama}".
- Draf PIB selalu memuat tulisan "DRAF, bukan dokumen resmi. Pengajuan dilakukan oleh PPJK atau importir di CEISA".
- Data aturan simulasi selalu memuat label **SIMULASI**.
- Footer setiap halaman: "Prototipe GTNIC 2026. Data perusahaan fiktif."

Barang yang disetujui otomatis pada tingkat `auto` diberi label "Disetujui otomatis oleh agent", berbeda dari "Diputuskan oleh {nama}". Email yang dikirim agent diberi label "Dikirim agent", sedangkan draf yang dikirim staf diberi label "Dikirim oleh {nama}".

### Aksesibilitas dan tampilan

- Warna badge selalu disertai teks, bukan warna saja.
- Semua aksi bisa dilakukan dengan keyboard; dialog memakai komponen shadcn yang sudah menangani fokus.
- Target layar demo: laptop 1366×768 dan 1920×1080. Tampilan HP cukup bisa dibaca (tabel bisa di-scroll horizontal), tidak perlu dioptimalkan.
