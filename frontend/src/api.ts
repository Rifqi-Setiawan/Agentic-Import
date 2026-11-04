export type Row = Record<string, any>;
export const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";
export const token = () => localStorage.getItem("imporjaga_token");
export function setAuthToken(value: string) {
  localStorage.setItem("imporjaga_token", value);
}
export function logout() {
  localStorage.removeItem("imporjaga_token");
}
export async function request(
  path: string,
  options: RequestInit = {},
): Promise<Row> {
  const headers = new Headers(options.headers);
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body.error || body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.message || `Permintaan gagal (${response.status})`;
    throw new Error(message);
  }
  return body;
}
export const post = (path: string, body?: Row) =>
  request(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
export function list(body: Row, key: string): Row[] {
  const value = body?.[key] ?? body?.data ?? body;
  return Array.isArray(value) ? value : [];
}
export function rupiah(value: unknown) {
  if (value === null || value === undefined || value === "")
    return "Belum tersedia";
  const number = Number(value);
  return Number.isFinite(number)
    ? new Intl.NumberFormat("id-ID", {
        style: "currency",
        currency: "IDR",
        maximumFractionDigits: 0,
      }).format(number)
    : "Belum tersedia";
}
export const label = (value?: string) =>
  ({
    draft: "Draf",
    analyzing: "Sedang dianalisis",
    needs_clarification: "Perlu jawaban",
    needs_documents: "Perlu dokumen",
    needs_review: "Perlu review",
    ready: "Siap menurut pemeriksaan",
    submitted: "Sudah diajukan di luar sistem",
    arrived: "Barang tiba",
    incomplete: "Belum lengkap",
    blocked: "Terhalang",
    failed: "Gagal",
    queued: "Antre",
    running: "Berjalan",
    processing: "Berjalan",
    succeeded: "Selesai",
    completed: "Selesai",
    waiting_external: "Menunggu jawaban / dokumen",
    classified: "Terklasifikasi",
    approved: "Disetujui",
    open: "Terbuka",
    pending: "Menunggu",
    provided: "Tersedia",
    missing: "Belum tersedia",
  })[value || ""] ||
  value ||
  "Belum tersedia";
