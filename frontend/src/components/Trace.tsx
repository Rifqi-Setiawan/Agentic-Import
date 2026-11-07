import { useEffect, useState } from "react";
import { API_BASE, Row, token, label } from "../api";
import { Empty } from "./Common";

const wib = new Intl.DateTimeFormat("id-ID", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Asia/Jakarta",
});

export function Trace({ runId }: { runId?: string }) {
  const [steps, setSteps] = useState<Row[]>([]);
  const [state, setState] = useState("");
  const [run, setRun] = useState<Row>();
  useEffect(() => {
    setSteps([]);
    setState("");
    setRun(undefined);
    if (!runId) return;
    const abort = new AbortController();
    async function connect() {
      try {
        setState("Menghubungkan jejak…");
        const response = await fetch(`${API_BASE}/sse/runs/${runId}`, {
          headers: { Authorization: `Bearer ${token()}` },
          signal: abort.signal,
        });
        if (!response.ok || !response.body)
          throw new Error(`Jejak tidak dapat dimuat (${response.status}).`);
        setState("Terhubung");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (!abort.signal.aborted) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder
            .decode(value, { stream: true })
            .replace(/\r\n/g, "\n");
          let boundary: number;
          while ((boundary = buffer.indexOf("\n\n")) >= 0) {
            const event = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const kind = event
              .split("\n")
              .find((l) => l.startsWith("event:"))
              ?.slice(6)
              .trim();
            const text = event
              .split("\n")
              .filter((l) => l.startsWith("data:"))
              .map((l) => l.slice(5).trim())
              .join("\n");
            if (!text) continue;
            let data: Row;
            try {
              data = JSON.parse(text);
            } catch {
              continue;
            }
            if (kind === "step")
              setSteps((old) =>
                old.some((s) => s.seq === data.seq)
                  ? old
                  : [...old, data].sort((a, b) => a.seq - b.seq),
              );
            if (kind === "end") {
              setRun(data);
              setState(`${label(data.status)} · ${label(data.outcome)}`);
            }
          }
        }
      } catch (error) {
        if (!abort.signal.aborted)
          setState(
            error instanceof Error ? error.message : "Koneksi jejak terputus.",
          );
      }
    }
    connect();
    return () => abort.abort();
  }, [runId]);
  if (!runId)
    return (
      <Empty>
        Run belum tersedia. Unggah invoice untuk memulai, atau pilih analisis
        dari riwayat.
      </Empty>
    );
  const plan = steps.find((step) => step.step_name === "plan_shipment");
  const visible = steps.filter((step) => !["llm", "plan_shipment"].includes(step.step_name));
  return (
    <div>
      <p className="muted">
        Run #{runId} · {state}
        {run?.total_tokens != null && ` · ${Number(run.total_tokens).toLocaleString("id-ID")} token tercatat`}
        {run?.duration_seconds != null && ` · ${Math.round(run.duration_seconds)} detik`}
      </p>
      {plan && <p><strong>Rencana klasifikasi</strong> · {plan.outcome}</p>}
      {visible.length === 0 ? (
        <Empty>Belum ada langkah yang dicatat worker.</Empty>
      ) : (
        <ol className="trace">
          {visible.map((s) => (
            <li key={s.seq}>
              <span className="dot">{s.seq}</span>
              <div>
                <strong>{s.title || s.step_name || s.node}</strong>
                <p>{s.outcome || s.step_outcome || s.detail}</p>
                {s.time && <small>{wib.format(new Date(s.time))} WIB </small>}
                {s.tool_name && <small>Alat: {s.tool_name}</small>}
                {s.output && (
                  <details>
                    <summary>Lihat bukti langkah</summary>
                    <pre>
                      {typeof s.output === "string"
                        ? s.output
                        : JSON.stringify(s.output, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
