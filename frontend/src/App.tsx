import { useEffect, useState } from "react";
import {
  ShieldCheck,
  Package,
  MessagesSquare,
  ClipboardCheck,
  BookOpen,
  Search,
  LogOut,
  ArrowRight,
  Plus,
  RefreshCw,
  LayoutDashboard,
  Building2,
  ChevronDown,
} from "lucide-react";
import { Row, request, post, list, setAuthToken, logout, token } from "./api";
import { Badge, Card, Empty, Field } from "./components/Common";
import { Shipment } from "./components/Shipment";
import { WorkQueue, Reference } from "./components/WorkQueue";
import { Dashboard } from "./components/Dashboard";

const DEMO = [
  ["Staf impor", "staf@mitrakemas.co.id"],
  ["Reviewer PPJK", "reviewer@mitrakemas.co.id"],
  ["Admin", "admin@mitrakemas.co.id"],
];
export default function App() {
  const [user, setUser] = useState<Row>();
  const [view, setView] = useState("dashboard");
  const [shipmentSearch, setShipmentSearch] = useState("");
  const [selected, setSelected] = useState("");
  const [ships, setShips] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [form, setForm] = useState({
    shipment_number: "",
    supplier_name: "",
    supplier_email: "tim-impor@mitrakemas.co.id",
    currency: "USD",
    cif_total_idr: "",
    exchange_rate: "",
  });
  const notify = (message: string) => setNotice(message);
  async function login(address: string, secret: string) {
    setBusy(true);
    try {
      const body = await post("/auth/login", {
        email: address,
        password: secret,
      });
      const data = body.data || body;
      setAuthToken(data.access_token);
      setUser(data.user || data);
      setSelected("");
      setView("dashboard");
      setError("");
      setNotice("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Login gagal");
    } finally {
      setBusy(false);
    }
  }
  async function load() {
    try {
      setShips(list(await request("/shipments"), "shipments"));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Data tidak dapat dimuat");
    }
  }
  useEffect(() => {
    if (token())
      request("/auth/me")
        .then((body) => setUser(body.data || body))
        .catch(() => logout());
  }, []);
  useEffect(() => {
    if (!user) return;
    load();
    const timer = setInterval(load, 6000);
    return () => clearInterval(timer);
  }, [user]);
  async function create() {
    setBusy(true);
    try {
      const result = await post("/shipments", {
        ...form,
        cif_total_idr: form.cif_total_idr || "0",
        exchange_rate: form.exchange_rate || null,
      });
      const data = result.data || result;
      setCreating(false);
      setView("shipments");
      setSelected(String(data.id));
      notify("Kiriman tersimpan. Unggah invoice di tab Dokumen.");
      await load();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Kiriman gagal dibuat");
    } finally {
      setBusy(false);
    }
  }
  async function reset() {
    if (
      !confirm(
        "Reset data demo perusahaan ini? Proses ini mengganti data transaksi demo.",
      )
    )
      return;
    setBusy(true);
    try {
      const result = await post("/admin/demo/reset");
      notify(result.message || "Reset selesai.");
      setSelected("");
      await load();
    } catch (e) {
      notify(e instanceof Error ? e.message : "Reset gagal");
    } finally {
      setBusy(false);
    }
  }
  if (!user)
    return (
      <div className="login">
        <section>
          <div className="brand">
            <ShieldCheck />
            <span>
              Artha<small>IMPORT, WITH CONFIDENCE.</small>
            </span>
          </div>
          <span className="eyebrow">DARI INVOICE KE PEMERIKSAAN IMPOR</span>
          <h1>
            Kepatuhan lebih jelas.
            <br />
            Setiap keputusan punya jejak.
          </h1>
          <p className="muted">
            Agent membantu membaca dokumen, mengusulkan klasifikasi dan
            menindaklanjuti kekurangan. Reviewer tetap memegang keputusan yang
            memerlukan penilaian ahli.
          </p>
        </section>
        <Card title="Masuk ke workspace">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              login(email, password);
            }}
          >
            <Field label="Email">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <Field label="Password">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field>
            <button className="primary full" disabled={busy}>
              {busy ? "Memproses…" : "Masuk"}
            </button>
          </form>
          {error && (
            <p role="alert" className="notice bad">
              {error}
            </p>
          )}
          <p className="muted text-center">
            Atau coba dengan akun demo berdata fiktif
          </p>
          <div className="demo-buttons">
            {DEMO.map(([name, address]) => (
              <button
                key={address}
                disabled={busy}
                onClick={() => login(address, "imporjaga123")}
              >
                {name} <ArrowRight size={14} />
              </button>
            ))}
          </div>
        </Card>
        <footer>
          Prototipe. Data perusahaan dan dokumen contoh fiktif. Pengajuan PIB
          tetap di luar aplikasi.
        </footer>
      </div>
    );
  const nav = [
    ["dashboard", "Dashboard", LayoutDashboard],
    ["shipments", "Kiriman impor", Package],
    ...(user.role !== "ppjk_reviewer"
      ? [["clarifications", "Klarifikasi", MessagesSquare]]
      : []),
    ...(["admin", "ppjk_reviewer"].includes(user.role)
      ? [["reviews", "Review ahli", ClipboardCheck]]
      : []),
    ["regulations", "Aturan & dampak", BookOpen],
    ["hs", "Cari kode HS", Search],
    ...(user.role === "admin" ? [["admin", "Kontrol demo", ShieldCheck]] : []),
  ];
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <ShieldCheck />
          <span>
            Artha<small>IMPORT WORKSPACE</small>
          </span>
        </div>
        <div className="company-card">
          <span className="company-icon">
            <Building2 size={17} />
          </span>
          <div>
            <small>Perusahaan</small>
            <strong>
              {user.company_name || user.company?.name || "Perusahaan Anda"}
            </strong>
          </div>
          <ChevronDown size={14} />
        </div>
        <nav>
          {nav.map(([key, title, Icon]: any) => (
            <button
              key={key}
              className={view === key ? "active" : ""}
              onClick={() => {
                setView(key);
                setSelected("");
              }}
            >
              <Icon size={18} />
              {title}
            </button>
          ))}
        </nav>
        <div className="sidebar-shipments">
          <span className="section-label">KIRIMAN TERBARU</span>
          {[...ships]
            .sort(
              (a, b) =>
                (Date.parse(b.created_at) || 0) -
                (Date.parse(a.created_at) || 0),
            )
            .slice(0, 4)
            .map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setView("shipments");
                  setSelected(String(s.id));
                }}
              >
                <Package size={13} />
                <span>{s.reference_no || s.shipment_number}</span>
                <i
                  className={
                    s.readiness_status === "ready" ? "ready-dot" : "pending-dot"
                  }
                />
              </button>
            ))}
        </div>
        <div className="profile">
          <strong>{user.full_name || user.email}</strong>
          <span>
            {user.company_name || user.company?.name || "Perusahaan Anda"}
          </span>
          <small>{user.role}</small>
          <button
            onClick={() => {
              logout();
              setUser(undefined);
              setShips([]);
            }}
          >
            <LogOut size={15} /> Keluar / ganti peran
          </button>
        </div>
      </aside>
      <main>
        <div className="topline">
          <span>
            <span className="status-dot" />
            {user.company_name || "Workspace perusahaan"}{" "}
            <span className="breadcrumb-separator">/</span>{" "}
            {String(nav.find((n) => n[0] === view)?.[1] || "Dashboard")}
          </span>
          <span className="workspace-mode">
            Workspace demo{" "}
            <span className="avatar">
              {(user.full_name || user.email || "A").slice(0, 1).toUpperCase()}
            </span>
          </span>
        </div>
        {notice && (
          <div role="status" className="notice flex justify-between gap-4">
            <span>{notice}</span>
            <button
              aria-label="Tutup pemberitahuan"
              onClick={() => setNotice("")}
            >
              ×
            </button>
          </div>
        )}
        {error && (
          <p role="alert" className="notice bad">
            {error}
          </p>
        )}
        {view === "dashboard" && (
          <Dashboard
            ships={ships}
            user={user}
            onOpen={(id) => {
              setView("shipments");
              setSelected(id);
            }}
            onCreate={
              user.role !== "ppjk_reviewer"
                ? () => setCreating(true)
                : undefined
            }
            onViewShipments={() => {
              setView("shipments");
              setSelected("");
            }}
          />
        )}
        {view === "shipments" &&
          (selected ? (
            <Shipment
              key={selected}
              id={selected}
              user={user}
              onBack={() => {
                setSelected("");
                load();
              }}
              notify={notify}
            />
          ) : (
            <>
              <header className="page-title">
                <div>
                  <span className="eyebrow">OPERASIONAL IMPOR</span>
                  <h1>Kiriman & kesiapan</h1>
                  <p>
                    Mulai dari invoice. Tuntaskan pertanyaan dan review sebelum
                    pengajuan.
                  </p>
                </div>
                <div className="actions">
                  <button onClick={load} aria-label="Muat ulang">
                    <RefreshCw size={16} />
                  </button>
                  {user.role !== "ppjk_reviewer" && (
                    <button
                      className="primary"
                      onClick={() => setCreating(true)}
                    >
                      <Plus size={16} />
                      Kiriman baru
                    </button>
                  )}
                </div>
              </header>
              <div className="metrics">
                <div className="metric">
                  <small>Kiriman</small>
                  <strong>{ships.length}</strong>
                </div>
                <div className="metric">
                  <small>Perlu jawaban</small>
                  <strong>
                    {
                      ships.filter((s) => s.status === "needs_clarification")
                        .length
                    }
                  </strong>
                </div>
                <div className="metric">
                  <small>Perlu review</small>
                  <strong>
                    {ships.filter((s) => s.status === "needs_review").length}
                  </strong>
                </div>
                <div className="metric">
                  <small>Siap diajukan</small>
                  <strong>
                    {
                      ships.filter(
                        (s) =>
                          s.readiness_status === "ready" &&
                          !["submitted", "arrived"].includes(s.status),
                      ).length
                    }
                  </strong>
                </div>
              </div>
              <Card title="Coba alur agent">
                <div className="guide">
                  <div>
                    <b>01 · Unggah invoice</b>
                    <p>
                      Buat atau buka kiriman, lalu unggah PDF berteks di tab
                      Dokumen.
                    </p>
                  </div>
                  <div>
                    <b>02 · Lengkapi dan tinjau</b>
                    <p>
                      Lihat jejak agent, jawab pertanyaan dan tinjau usulan kode
                      HS.
                    </p>
                  </div>
                  <div>
                    <b>03 · Pantau dampak</b>
                    <p>
                      Admin dapat menerbitkan aturan simulasi dan memeriksa
                      kiriman terdampak.
                    </p>
                  </div>
                </div>
                <div className="actions">
                  <a href="/data/demo/invoices/INV-MKN-011.pdf" download>
                    Unduh contoh invoice ↗
                  </a>
                  <a href="/data/demo/invoices/DS-VALVE-011.pdf" download>
                    Unduh datasheet contoh ↗
                  </a>
                </div>
              </Card>
              <Card title="Daftar kiriman">
                <label className="shipment-search">
                  <Search size={17} />
                  <input
                    aria-label="Cari kiriman"
                    placeholder="Cari referensi atau pemasok…"
                    value={shipmentSearch}
                    onChange={(e) => setShipmentSearch(e.target.value)}
                  />
                </label>
                {ships.length ? (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Referensi / pemasok</th>
                          <th>Barang</th>
                          <th>Status operasional</th>
                          <th>Kesiapan</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {ships
                          .filter((s) =>
                            `${s.reference_no || s.shipment_number} ${s.supplier_name}`
                              .toLowerCase()
                              .includes(shipmentSearch.toLowerCase()),
                          )
                          .map((s) => (
                            <tr key={s.id}>
                              <td>
                                <strong>
                                  {s.reference_no || s.shipment_number}
                                </strong>
                                <small>{s.supplier_name}</small>
                              </td>
                              <td>{s.item_count ?? "—"}</td>
                              <td>
                                <Badge value={s.status} />
                              </td>
                              <td>
                                <Badge value={s.readiness_status} />
                              </td>
                              <td>
                                <button
                                  onClick={() => setSelected(String(s.id))}
                                >
                                  Buka <ArrowRight size={14} />
                                </button>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <Empty>
                    Belum ada kiriman. Buat kiriman pertama untuk memulai.
                  </Empty>
                )}
              </Card>
            </>
          ))}
        {view === "clarifications" && (
          <>
            <header className="page-title">
              <h1>Klarifikasi barang</h1>
            </header>
            <WorkQueue kind="clarifications" notify={notify} />
          </>
        )}
        {view === "reviews" && (
          <>
            <header className="page-title">
              <h1>Review ahli</h1>
            </header>
            <WorkQueue kind="reviews" notify={notify} />
          </>
        )}
        {(view === "hs" || view === "regulations") && (
          <>
            <header className="page-title">
              <h1>
                {view === "hs" ? "Penelusuran referensi" : "Pemantauan aturan"}
              </h1>
            </header>
            <Reference key={view} kind={view} user={user} notify={notify} />
          </>
        )}
        {view === "admin" && (
          <Card title="Kontrol demo perusahaan">
            <p>
              Reset mengembalikan data transaksi demo. Pastikan tidak ada
              analisis aktif dan catat hasil yang ingin disimpan terlebih
              dahulu.
            </p>
            <button disabled={busy} onClick={reset}>
              Reset data demo
            </button>
            <p className="muted">
              Pengaturan layanan dan kredensial dikelola operator deployment.
            </p>
          </Card>
        )}
        <footer>
          Artha · Prototipe pemeriksaan impor. Hasil perlu diverifikasi; bukan
          pengajuan resmi.
        </footer>
      </main>
      {creating && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-title"
          >
            <h2 id="create-title">Buat kiriman</h2>
            <p className="muted">Perusahaan mengikuti akun Anda.</p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                create();
              }}
            >
              {[
                ["shipment_number", "Nomor referensi"],
                ["supplier_name", "Nama pemasok"],
                ["supplier_email", "Email pemasok"],
                ["currency", "Mata uang"],
                ["cif_total_idr", "CIF rupiah jika sudah diketahui (opsional)"],
                [
                  "exchange_rate",
                  "Kurs rupiah per unit valuta — diisi pengguna untuk demo, bukan kurs resmi otomatis",
                ],
              ].map(([key, name]) => (
                <Field key={key} label={name}>
                  <input
                    required={!["cif_total_idr", "exchange_rate"].includes(key)}
                    type={
                      key === "supplier_email"
                        ? "email"
                        : ["cif_total_idr", "exchange_rate"].includes(key)
                          ? "number"
                          : "text"
                    }
                    min={key === "cif_total_idr" ? 0 : undefined}
                    value={(form as Row)[key]}
                    onChange={(e) =>
                      setForm({ ...form, [key]: e.target.value })
                    }
                  />
                </Field>
              ))}
              <div className="actions">
                <button className="primary" disabled={busy}>
                  {busy ? "Menyimpan…" : "Simpan kiriman"}
                </button>
                <button type="button" onClick={() => setCreating(false)}>
                  Batal
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
