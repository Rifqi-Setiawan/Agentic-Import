import { useEffect, useState } from "react";
import { API_BASE, Row, token, label } from "../api";
import { Empty } from "./Common";

export function Trace({ runId }: { runId?: string }) {
  const [steps, setSteps] = useState<Row[]>([]);
  const [state, setState] = useState("");
  useEffect(() => {
    setSteps([]);
    setState("");
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
            if (kind === "end")
              setState(`${label(data.status)} · ${label(data.outcome)}`);
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
  return (
    <div>
      <p className="muted">
        Run #{runId} · {state}
      </p>
      {steps.length === 0 ? (
        <Empty>Belum ada langkah yang dicatat worker.</Empty>
      ) : (
        <ol className="trace">
          {steps.map((s) => (
            <li key={s.seq}>
              <span className="dot">{s.seq}</span>
              <div>
                <strong>{s.title || s.step_name || s.node}</strong>
                <p>{s.outcome || s.step_outcome || s.detail}</p>
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
