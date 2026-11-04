import { useEffect, useState } from "react";
import { Row, request, post, list } from "../api";
import { Badge, Card, Empty, Field } from "./Common";
export function WorkQueue({
  kind,
  notify,
}: {
  kind: "reviews" | "clarifications";
  notify: (message: string) => void;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [codes, setCodes] = useState<Record<string, string>>({});
  async function load() {
    try {
      setRows(list(await request(`/${kind}?status_filter=open`), kind));
      setError("");
    } catch (e) {
      setError(String(e));
    }
  }
  useEffect(() => {
    load();
    const timer = setInterval(load, 6000);
    return () => clearInterval(timer);
  }, [kind]);
  async function submit(id: string, action?: string) {
    if (!notes[id]?.trim()) {
      notify("Isi jawaban atau catatan terlebih dahulu.");
      return;
    }
    if (action === "modify" && !/^\d{8}$/.test(codes[id] || "")) {
      notify("Kode pengganti harus terdiri dari 8 digit.");
      return;
    }
    setBusy(id);
    try {
      await post(
        `/${kind}/${id}/${kind === "reviews" ? "decision" : "answer"}`,
        kind === "reviews"
          ? {
              decision: action,
              notes: notes[id],
              modified_hs_code: action === "modify" ? codes[id] : undefined,
            }
          : { answer: notes[id], answer_source: "staff_form" },
      );
      notify("Tersimpan. Pemrosesan lanjutan mengikuti antrean.");
      await load();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Gagal menyimpan");
    } finally {
      setBusy("");
    }
  }
  return (
    <Card
      title={
        kind === "reviews"
          ? "Keputusan reviewer PPJK"
          : "Pertanyaan yang membutuhkan jawaban"
      }
    >
      {error && (
        <p role="alert" className="bad">
          {error}
        </p>
      )}
      {rows.length ? (
        rows.map((row) => (
          <article className="item" key={row.id}>
            <div className="flex justify-between gap-3">
              <h3>
                {row.question ||
                  row.question_text ||
                  row.item_description ||
                  `Barang #${row.item_id}`}
              </h3>
              <Badge value={row.status} />
            </div>
            <p className="muted">
              Kiriman #{row.shipment_id} ·{" "}
              {row.reason || row.review_type || row.attribute}
            </p>
            {row.suggested_hs_code && (
              <p>
                Kode usulan: <strong>{row.suggested_hs_code}</strong>
              </p>
            )}
            <Field
              label={
                kind === "reviews" ? "Catatan keputusan" : "Jawaban spesifikasi"
              }
            >
              <textarea
                value={notes[row.id] || ""}
                onChange={(e) =>
                  setNotes({ ...notes, [row.id]: e.target.value })
                }
              />
            </Field>
            {kind === "reviews" && (
              <Field label="Kode pengganti (khusus Ubah kode)">
                <input
                  inputMode="numeric"
                  maxLength={8}
                  value={codes[row.id] || ""}
                  onChange={(e) =>
                    setCodes({
                      ...codes,
                      [row.id]: e.target.value.replace(/\D/g, ""),
                    })
                  }
                />
              </Field>
            )}
            <div className="actions">
              {kind === "reviews" ? (
                ["approve", "modify", "reject"].map((action, i) => (
                  <button
                    key={action}
                    disabled={busy === row.id}
                    onClick={() => submit(row.id, action)}
                  >
                    {["Setujui", "Ubah kode", "Minta data / tolak"][i]}
                  </button>
                ))
              ) : (
                <button
                  className="primary"
                  disabled={busy === row.id}
                  onClick={() => submit(row.id)}
                >
                  Kirim jawaban
                </button>
              )}
            </div>
          </article>
        ))
      ) : (
        <Empty>Tidak ada pekerjaan terbuka pada antrean ini.</Empty>
      )}
    </Card>
  );
}

export function Reference({
  kind,
  user,
  notify,
}: {
  kind: "hs" | "regulations";
  user: Row;
  notify: (message: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function search() {
    setBusy(true);
    try {
      const result = await request(
        kind === "hs"
          ? `/hs-codes/search?q=${encodeURIComponent(query)}`
          : "/regulations",
      );
      setRows(list(result, kind === "hs" ? "results" : "regulations"));
      setError("");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    setRows([]);
    setError("");
    if (kind === "regulations") search();
  }, [kind]);
  async function simulate() {
    if (
      !confirm(
        "Terbitkan aturan SIMULASI untuk perusahaan ini dan periksa kiriman yang terdampak?",
      )
    )
      return;
    setBusy(true);
    try {
      const result = await post("/regulations/simulate-demo", {
        hs_prefix: "8481",
        requirement_code: "DEMO_VALVE_PERMIT",
        title: "SIMULASI — izin katup industri pos 8481",
      });
      notify(result.impact_summary || "Aturan simulasi tercatat.");
      await search();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Simulasi gagal");
    } finally {
      setBusy(false);
    }
  }
  return (
    <Card
      title={kind === "hs" ? "Cari kode HS" : "Aturan dan dampak perubahan"}
    >
      {kind === "hs" ? (
        <form
          className="actions"
          onSubmit={(e) => {
            e.preventDefault();
            search();
          }}
        >
          <input
            aria-label="Cari HS"
            placeholder="Kode atau deskripsi barang"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button disabled={busy || query.length < 2}>Cari</button>
        </form>
      ) : (
        <>
          <p className="muted">
            Data simulasi diberi label; hasil pencocokan mengikuti kode HS
            kiriman yang aktif.
          </p>
          {user.role === "admin" && (
            <button disabled={busy} onClick={simulate}>
              Simulasikan aturan pos 8481
            </button>
          )}
        </>
      )}
      {error && (
        <p role="alert" className="bad">
          {error}
        </p>
      )}
      {rows.length ? (
        rows.map((r, i) => (
          <article className="item" key={r.id || r.code || i}>
            <h3>
              {r.code || r.hs_code || r.regulation_number}{" "}
              {r.title || r.description_id || r.description}
            </h3>
            <p>{r.description_en || r.summary}</p>
            {r.is_simulated || r.is_simulation ? (
              <Badge value="SIMULASI" />
            ) : null}
            {kind === "hs" && (
              <div className="muted" style={{ marginTop: "4px", fontSize: "0.85em" }}>
                <span>
                  Tarif BM:{" "}
                  {r.bm_rate !== null && r.bm_rate !== undefined
                    ? `${r.bm_rate}%`
                    : "Belum diverifikasi (NULL)"}
                </span>
                {r.rate_status === "demo_unverified" && (
                  <span style={{ marginLeft: "8px", color: "#B45309", fontWeight: 500 }}>
                    [Tarif Demo Belum Diverifikasi]
                  </span>
                )}
                {r.source_page && (
                  <span style={{ marginLeft: "12px" }}>
                    Ref: BTKI 2022 DJBC hal. {r.source_page}
                  </span>
                )}
              </div>
            )}
            {r.lartas_coverage && (
              <p className="muted">
                Cakupan lartas:{" "}
                {r.lartas_coverage === "unknown"
                  ? "Belum diverifikasi"
                  : r.lartas_coverage === "verified_none"
                    ? "Tidak ditemukan kewajiban dalam cakupan pemeriksaan"
                    : r.lartas_coverage}
              </p>
            )}
            {r.source_url && (
              <a href={r.source_url} target="_blank" rel="noreferrer">
                Buka sumber ↗
              </a>
            )}
          </article>
        ))
      ) : (
        <Empty>
          {busy
            ? "Memuat…"
            : kind === "hs"
              ? "Masukkan deskripsi atau kode untuk mencari."
              : "Belum ada aturan."}
        </Empty>
      )}
    </Card>
  );
}
