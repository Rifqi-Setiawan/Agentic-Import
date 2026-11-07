import { useEffect, useRef, useState } from "react";
import { Row, request, post, list, rupiah, label } from "../api";
import { Badge, Card, Empty, Field } from "./Common";
import { Trace } from "./Trace";

export function Shipment({
  id,
  user,
  onBack,
  notify,
}: {
  id: string;
  user: Row;
  onBack: () => void;
  notify: (message: string) => void;
}) {
  const [detail, setDetail] = useState<Row>();
  const latestRun = useRef("");
  const [docs, setDocs] = useState<Row[]>([]);
  const [checklist, setChecklist] = useState<Row[]>([]);
  const [messages, setMessages] = useState<Row[]>([]);
  const [pib, setPib] = useState<Row>();
  const [runs, setRuns] = useState<Row[]>([]);
  const [tab, setTab] = useState("ringkasan");
  const [runId, setRunId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [docType, setDocType] = useState("invoice");
  const [file, setFile] = useState<File>();
  const canEdit = user.role !== "ppjk_reviewer";
  async function refresh() {
    try {
      const [d, analysisResult] = await Promise.all([
        request(`/shipments/${id}`),
        request(`/shipments/${id}/analysis`).catch(() => null),
      ]);
      const data = d.data || d;
      const evidence = analysisResult?.classifications || {};
      setDetail({
        ...data,
        items: (data.items || []).map((item: Row) => ({
          ...item,
          ...evidence[String(item.id)],
          hs_code: item.hs_code_accepted || item.hs_code || evidence[String(item.id)]?.hs_code,
        })),
      });
      setError("");
      if (analysisResult) {
        const rr = analysisResult.runs || [];
        setRuns(rr);
        const newest = String(rr[0]?.id || "");
        if (newest && newest !== latestRun.current) {
          latestRun.current = newest;
          setRunId(newest);
        }
        if (analysisResult.totals)
          setPib((old) => ({ ...old, ...analysisResult.totals }));
      }
      if (tab === "dokumen") {
        const [docData, checklistData] = await Promise.all([
          request(`/shipments/${id}/documents`),
          request(`/shipments/${id}/checklist`),
        ]);
        setDocs(list(docData, "documents"));
        setChecklist(list(checklistData, "checklist"));
      }
      if (tab === "komunikasi")
        setMessages(
          list(await request(`/shipments/${id}/messages`), "messages"),
        );
      if (tab === "pib") {
        const result = await request(`/shipments/${id}/pib-draft`);
        setPib({
          ...(result.pib_draft || result.data),
          ...analysisResult?.totals,
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Data gagal dimuat");
    }
  }
  useEffect(() => {
    let pending = false;
    refresh();
    const timer = setInterval(async () => {
      if (!pending) {
        pending = true;
        try {
          await refresh();
        } finally {
          pending = false;
        }
      }
    }, 4000);
    return () => clearInterval(timer);
  }, [id, tab]);
  async function action(path: string) {
    setBusy(true);
    try {
      const result = await post(path);
      if (result.run_id) setRunId(String(result.run_id));
      notify(result.message || "Perubahan tersimpan.");
      await refresh();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Aksi gagal");
    } finally {
      setBusy(false);
    }
  }
  async function upload() {
    if (!file) return;
    setBusy(true);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("doc_type", docType);
      const result = await request(`/shipments/${id}/documents`, {
        method: "POST",
        body: form,
      });
      setFile(undefined);
      setTab("jejak");
      notify("Dokumen tersimpan. Analisis akan berjalan sesuai antrean.");
      if (result.auto_run_id) setRunId(String(result.auto_run_id));
      await refresh();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Upload gagal");
    } finally {
      setBusy(false);
    }
  }
  if (!detail)
    return (
      <Card>
        <p>{error || "Memuat kiriman…"}</p>
        <button onClick={onBack}>Kembali</button>
      </Card>
    );
  const items: Row[] = detail.items || [];
  return (
    <>
      <button className="link" onClick={onBack}>
        ← Semua kiriman
      </button>
      <header className="page-title">
        <div>
          <span className="eyebrow">KIRIMAN IMPOR</span>
          <h1>{detail.reference_no || detail.shipment_number}</h1>
          <p>
            {detail.supplier_name} · {detail.currency}
          </p>
        </div>
        <div className="actions">
          <Badge value={detail.status} />
          <Badge value={detail.readiness_status} />
          {canEdit && (
            <button
              disabled={busy}
              onClick={() => {
                action(`/shipments/${id}/analyze`);
                setTab("jejak");
              }}
            >
              Analisis ulang
            </button>
          )}
          {canEdit &&
            detail.is_ready &&
            detail.status !== "submitted" &&
            detail.status !== "arrived" && (
              <button
                disabled={busy}
                onClick={() => action(`/shipments/${id}/mark-submitted`)}
              >
                Tandai sudah diajukan di luar sistem
              </button>
            )}
          {canEdit && detail.status === "submitted" && (
            <button
              disabled={busy}
              onClick={() => action(`/shipments/${id}/mark-arrived`)}
            >
              Tandai barang tiba
            </button>
          )}
        </div>
      </header>
      {error && (
        <p role="alert" className="notice bad">
          {error}
        </p>
      )}
      <nav className="tabs">
        {[
          "ringkasan",
          "barang",
          "pungutan",
          "dokumen",
          "komunikasi",
          "pib",
          "jejak",
        ].map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t === "pib" ? "Draf PIB" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </nav>
      {tab === "ringkasan" && (
        <div className="two-col">
          <Card title="Yang perlu diselesaikan">
            {(detail.blocking_issues || []).length ? (
              <ul className="issues">
                {detail.blocking_issues.map((b: any, i: number) => (
                  <li key={i}>{typeof b === "string" ? b : b.message}</li>
                ))}
              </ul>
            ) : (
              <p>Tidak ada penghalang yang dilaporkan pemeriksaan saat ini.</p>
            )}
            <p className="muted">
              {items.length} barang · {detail.pending_job_count ?? "—"}{" "}
              pekerjaan tertunda
            </p>
          </Card>
          <Card title="Langkah selanjutnya">
            <p>
              Lengkapi dokumen, jawab pertanyaan di menu Klarifikasi, lalu minta
              reviewer memeriksa keputusan yang membutuhkan persetujuan.
            </p>
            <p className="muted">
              Pengajuan PIB dilakukan sendiri oleh PPJK/importir di luar
              aplikasi.
            </p>
          </Card>
        </div>
      )}
      {tab === "barang" && (
        <Card title="Klasifikasi dan bukti per barang">
          {!items.length ? (
            <Empty>Belum ada barang hasil ekstraksi.</Empty>
          ) : (
            items.map((item: Row) => (
              <details className="item" key={item.id}>
                <summary>
                  <span>
                    {item.line_no}. {item.description || item.description_raw}
                  </span>
                  <strong>
                    {item.hs_code ||
                      item.hs_code_accepted ||
                      item.hs_code_proposed ||
                      "Belum diklasifikasi"}
                  </strong>
                  <Badge value={item.status} />
                </summary>
                <p>
                  Jumlah: {item.qty ?? item.quantity ?? "—"}{" "}
                  {item.unit || item.uom || ""} · Skor keyakinan:{" "}
                  {item.confidence_score == null
                    ? "Belum tersedia"
                    : `${Math.round(item.confidence_score * 100)}%`}
                </p>
                <p>
                  {item.justification ||
                    item.rationale ||
                    item.classification?.rationale ||
                    "Alasan belum tersedia."}
                </p>
                {(item.citations || item.classification?.citations || []).map(
                  (c: Row, i: number) => (
                    <blockquote key={i}>
                      {c.quote}
                      <small>{c.ref || c.source}</small>
                    </blockquote>
                  ),
                )}
                {(
                  item.alternatives ||
                  item.classification?.alternatives ||
                  []
                ).map((a: Row, i: number) => (
                  <p key={i}>
                    Alternatif {a.hs_code}: {a.why_not}
                  </p>
                ))}
                <p className="muted">
                  Keputusan:{" "}
                  {item.approval_origin === "auto_rule_gate"
                    ? "Disetujui otomatis oleh agent"
                    : item.is_approved ? "Sudah disetujui" : "Belum disetujui"}.
                  Periksa review sebelum pengajuan.
                </p>
              </details>
            ))
          )}
        </Card>
      )}
      {tab === "pungutan" && (
        <Card title="Perkiraan pungutan dari hasil perhitungan">
          <div className="metrics">
            {[
              ["CIF rupiah", pib?.cif_idr],
              ["Bea masuk", pib?.bm_idr],
              ["PPN", pib?.ppn_idr],
              ["PPh 22", pib?.pph_idr],
              ["Total pungutan", pib?.total_duties_idr],
            ].map(([name, value]) => (
              <div className="metric" key={String(name)}>
                <small>{name}</small>
                <strong>{rupiah(value)}</strong>
              </div>
            ))}
          </div>
          <p className="muted">
            Angka adalah perkiraan prototipe. Nilai kosong belum dihitung;
            verifikasi sumber tarif, kurs, dan kelengkapan sebelum dipakai.
          </p>
        </Card>
      )}
      {tab === "dokumen" && (
        <div className="two-col">
          <Card title="Unggah dokumen">
            {canEdit ? (
              <>
                <Field label="Jenis dokumen">
                  <select
                    value={docType}
                    onChange={(e) => setDocType(e.target.value)}
                  >
                    {[
                      ["invoice", "Invoice"],
                      ["packing_list", "Packing list"],
                      ["spec", "Spesifikasi / datasheet"],
                      ["bill_of_lading", "B/L atau AWB"],
                      ["permit", "Izin"],
                      ["insurance", "Bukti asuransi"],
                    ].map(([value, name]) => (
                      <option key={value} value={value}>
                        {name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="PDF berteks, maksimal 10 MB">
                  <input
                    type="file"
                    accept="application/pdf,.pdf"
                    onChange={(e) => setFile(e.target.files?.[0])}
                  />
                </Field>
                <button
                  className="primary"
                  disabled={busy || !file || file.size > 10 * 1024 * 1024}
                  onClick={upload}
                >
                  {busy ? "Mengunggah…" : "Unggah dan proses"}
                </button>
                {file && file.size > 10 * 1024 * 1024 && (
                  <p className="bad">File melebihi 10 MB.</p>
                )}
              </>
            ) : (
              <p>
                Reviewer dapat membaca dokumen; unggahan dilakukan staf atau
                admin.
              </p>
            )}
            <h3>Dokumen tersimpan</h3>
            {docs.length ? (
              docs.map((d) => (
                <p key={d.id}>
                  {d.file_name || d.original_filename}{" "}
                  <Badge value={d.status} />
                </p>
              ))
            ) : (
              <Empty>Belum ada dokumen.</Empty>
            )}
          </Card>
          <Card title="Checklist persyaratan">
            {checklist.length ? (
              checklist.map((c) => (
                <div className="item" key={c.id}>
                  <strong>{c.title || c.label || c.requirement_code}</strong>{" "}
                  <Badge value={c.status} />
                  <p>{c.reason || c.resolution_reason}</p>
                </div>
              ))
            ) : (
              <Empty>
                Checklist belum dibentuk. Unggah invoice untuk memulai analisis.
              </Empty>
            )}
          </Card>
        </div>
      )}
      {tab === "komunikasi" && (
        <Card title="Permintaan pemasok dan tindak lanjut">
          {messages.length ? (
            messages.map((m) => (
              <article className="item" key={m.id}>
                <Badge value={m.delivery_status || m.status} />
                <h3>{m.subject}</h3>
                <small>Tujuan: {m.recipient || m.to_address}</small>
                <p className="whitespace-pre-wrap">{m.body}</p>
                <small>
                  {m.sent_at
                    ? "Diterima adapter SMTP: " + m.sent_at
                    : "Belum ada bukti pengiriman"}
                </small>
              </article>
            ))
          ) : (
            <Empty>
              Belum ada permintaan ke pemasok. Pesan hanya ditampilkan setelah
              dicatat sistem.
            </Empty>
          )}
        </Card>
      )}
      {tab === "pib" && (
        <Card title="DRAF PIB — bukan dokumen resmi">
          <p className="notice">
            Pengajuan tetap dilakukan importir/PPJK di CEISA. Draf ini merupakan
            hasil prototipe.
          </p>
          {pib ? (
            <dl className="definition">
              {[
                ["Kiriman", pib.shipment_number],
                ["Importir", pib.importer_name],
                ["Pemasok", pib.supplier_name],
                ["Negara asal", pib.origin_country],
                ["Mata uang", pib.currency],
                ["CIF rupiah", rupiah(pib.cif_idr)],
                ["Total pungutan", rupiah(pib.total_duties_idr)],
              ].map(([key, value]) => (
                <div key={String(key)}>
                  <dt>{key}</dt>
                  <dd>{value || "Belum tersedia"}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <Empty>Draf belum tersedia.</Empty>
          )}
        </Card>
      )}
      {tab === "jejak" && (
        <Card title="Jejak kerja agent">
          <Field label="Riwayat analisis">
            <select value={runId} onChange={(e) => setRunId(e.target.value)}>
              <option value="">Pilih run</option>
              {runs.map((r) => (
                <option key={r.id || r.run_id} value={r.id || r.run_id}>
                  #{r.id || r.run_id} · {label(r.status)} · {r.created_at}
                </option>
              ))}
            </select>
          </Field>
          <Trace runId={runId} />
        </Card>
      )}
    </>
  );
}
