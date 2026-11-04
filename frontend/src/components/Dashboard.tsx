import {
  ArrowDownToLine,
  ArrowRight,
  CheckCheck,
  ClipboardCheck,
  FileText,
  Package,
  Plus,
  Sparkles,
} from "lucide-react";
import { Row } from "../api";
import { Badge, Card, Empty } from "./Common";

export function Dashboard({
  ships,
  user,
  onOpen,
  onCreate,
  onViewShipments,
}: {
  ships: Row[];
  user: Row;
  onOpen: (id: string) => void;
  onCreate?: () => void;
  onViewShipments: () => void;
}) {
  const ready = ships.filter(
    (s) => s.readiness_status === "ready" && s.status === "ready",
  ).length;
  const waiting = ships.filter(
    (s) => s.status === "needs_clarification",
  ).length;
  const reviews = ships.filter((s) => s.status === "needs_review").length;
  const other = ships.length - ready;
  const percent = ships.length ? Math.round((ready / ships.length) * 100) : 0;
  const latest = [...ships].sort(
    (a, b) =>
      (Date.parse(b.created_at) || 0) - (Date.parse(a.created_at) || 0) ||
      Number(b.id) - Number(a.id),
  );
  const attention = latest.filter(
    (s) =>
      !["submitted", "arrived"].includes(s.status) &&
      (s.status !== "ready" || s.readiness_status !== "ready"),
  );
  const stats = [
    {
      title: "Total kiriman",
      value: ships.length,
      Icon: Package,
      note: "Dalam workspace perusahaan",
    },
    {
      title: "Menunggu klarifikasi",
      value: waiting,
      Icon: FileText,
      note: "Perlu informasi tambahan",
    },
    {
      title: "Perlu review ahli",
      value: reviews,
      Icon: ClipboardCheck,
      note: "Keputusan ada di tangan Anda",
    },
    {
      title: "Siap diajukan",
      value: ready,
      Icon: CheckCheck,
      note: "Lolos pemeriksaan aplikasi",
    },
  ];
  return (
    <>
      <header className="page-title dashboard-title">
        <div>
          <span className="eyebrow">YOUR IMPORT CONTROL CENTER</span>
          <h1>
            Selamat datang,{" "}
            {String(user.full_name || "tim impor").split(" ")[0]}{" "}
            <span className="hello-dot">✳</span>
          </h1>
          <p>Semua kiriman, dokumen, dan keputusan. Dalam satu pandangan.</p>
        </div>
        {onCreate && (
          <button className="primary" onClick={onCreate}>
            <Plus size={16} /> Kiriman baru
          </button>
        )}
      </header>
      <div className="overview-stats">
        {stats.map(({ title, value, Icon, note }) => (
          <div className="overview-stat" key={title}>
            <span className="stat-icon">
              <Icon size={19} />
            </span>
            <div>
              <div className="stat-number">
                {value}
                <span>{title}</span>
              </div>
              <small>{note}</small>
            </div>
          </div>
        ))}
      </div>
      <div className="dashboard-grid">
        <div className="dashboard-primary">
          <div className="dashboard-feature-row">
            <Card title="Kesiapan kiriman">
              <div className="readiness-chart">
                <div
                  className="donut"
                  role="img"
                  aria-label={`${ready} dari ${ships.length} kiriman siap diajukan`}
                  style={{
                    background: `conic-gradient(var(--green) 0% ${percent}%, var(--mint) ${percent}% 100%)`,
                  }}
                >
                  <div>
                    <strong>{percent}%</strong>
                    <small>Siap diajukan</small>
                  </div>
                </div>
                <div className="chart-legend">
                  <div>
                    <i className="legend-dot emerald" />
                    Siap diajukan <b>{ready}</b>
                  </div>
                  <div>
                    <i className="legend-dot mint" />
                    Lainnya <b>{other}</b>
                  </div>
                  <p>Seluruh kiriman, termasuk yang sudah diajukan dan tiba.</p>
                </div>
              </div>
            </Card>
            <section className="agent-feature">
              <span className="feature-pill">
                <Sparkles size={13} /> AI-assisted workspace
              </span>
              <h2>
                Lebih jelas di
                <br />
                setiap langkah.
              </h2>
              <p>
                Telusuri dokumen, bukti klasifikasi, dan keputusan reviewer
                dalam satu alur.
              </p>
              <button onClick={onViewShipments}>
                Lihat kiriman <ArrowRight size={14} />
              </button>
              <svg
                className="parcel-art"
                viewBox="0 0 200 140"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M16 117C50 70 100 144 185 65"
                  stroke="#9ce9bc"
                  strokeWidth="2"
                  strokeDasharray="4 5"
                />
                <path d="m67 54 50-24 51 25-50 25z" fill="#d1f8e1" />
                <path d="m67 54 51 26v56l-51-28z" fill="#78d7a4" />
                <path d="m118 80 50-25v54l-50 27z" fill="#0a9960" />
                <path d="m89 44 51 25 16-8-50-25z" fill="#f0fff5" />
                <path d="m140 69 16-8v23l-16 8z" fill="#c1f4d6" />
                <rect
                  x="78"
                  y="80"
                  width="21"
                  height="14"
                  rx="3"
                  transform="rotate(28 78 80)"
                  fill="#ecfff4"
                />
                <circle cx="43" cy="52" r="19" fill="white" />
                <path
                  d="m35 52 6 6 10-12"
                  stroke="#0fa96b"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </section>
          </div>
          <Card title="Progres operasional">
            <div className="pipeline-bars">
              {[
                [
                  "Dokumen / persiapan",
                  ships.filter((s) =>
                    ["draft", "needs_documents"].includes(s.status),
                  ).length,
                ],
                [
                  "Analisis AI",
                  ships.filter((s) => s.status === "analyzing").length,
                ],
                ["Klarifikasi", waiting],
                ["Review ahli", reviews],
                ["Siap diajukan", ready],
              ].map(([title, count]) => (
                <div className="pipeline-stage" key={title}>
                  <div>
                    <span>{title}</span>
                    <b>{count}</b>
                  </div>
                  <div className="bar-track">
                    <i
                      style={{
                        width: `${ships.length ? (Number(count) / ships.length) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
        <Card title="Perlu perhatian">
          <div className="attention-heading">
            <span className="live-indicator" />
            {attention.length} kiriman belum siap
          </div>
          <div className="attention-list">
            {attention.length ? (
              attention.slice(0, 4).map((s) => (
                <button key={s.id} onClick={() => onOpen(String(s.id))}>
                  <span className="attention-icon">
                    <Package size={15} />
                  </span>
                  <div>
                    <strong>{s.reference_no || s.shipment_number}</strong>
                    <small>{s.supplier_name}</small>
                    <Badge value={s.status} />
                  </div>
                  <ArrowRight size={14} />
                </button>
              ))
            ) : (
              <Empty>
                Semua kiriman sudah dituntaskan. Kiriman baru akan muncul di
                sini.
              </Empty>
            )}
          </div>
          <button className="full attention-all" onClick={onViewShipments}>
            Lihat semua kiriman <ArrowRight size={14} />
          </button>
        </Card>
      </div>
      <Card title="Ringkasan kiriman">
        {ships.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Referensi kiriman</th>
                  <th>Pemasok</th>
                  <th>Barang</th>
                  <th>Status</th>
                  <th>Kesiapan</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {latest.slice(0, 6).map((s) => (
                  <tr key={s.id}>
                    <td>
                      <span className="table-reference">
                        <span className="parcel-icon">
                          <Package size={16} />
                        </span>
                        <strong>{s.reference_no || s.shipment_number}</strong>
                      </span>
                    </td>
                    <td>{s.supplier_name}</td>
                    <td>{s.item_count ?? "—"}</td>
                    <td>
                      <Badge value={s.status} />
                    </td>
                    <td>
                      <Badge value={s.readiness_status} />
                    </td>
                    <td>
                      <button
                        className="icon-button"
                        aria-label={`Buka ${s.reference_no || s.shipment_number}`}
                        onClick={() => onOpen(String(s.id))}
                      >
                        <ArrowRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>
            Belum ada kiriman. Mulai dengan membuat kiriman pertama Anda.
          </Empty>
        )}
      </Card>
      <section className="starter-strip">
        <div className="starter-icon">
          <FileText size={22} />
        </div>
        <div>
          <strong>Pertama kali mencoba Artha?</strong>
          <p>
            Mulai dengan invoice contoh, lalu ikuti jejak analisis dan review.
          </p>
        </div>
        <a href="/data/demo/invoices/INV-MKN-011.pdf" download>
          <ArrowDownToLine size={15} /> Unduh invoice contoh
        </a>
      </section>
    </>
  );
}
