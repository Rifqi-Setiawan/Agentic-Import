import React, { useState, useEffect } from 'react';
import {
  FileText, Shield, AlertTriangle, CheckCircle, Clock, Search,
  RefreshCw, Upload, Send, ExternalLink, UserCheck, AlertCircle,
  TrendingUp, ArrowRight, Layers, HelpCircle, FileCheck, Play,
  Plus, X, Filter, Check, Edit3, XCircle, BookOpen, Settings
} from 'lucide-react';
import { api, setAuthToken } from './api';

export default function App() {
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [activeView, setActiveView] = useState<'dashboard' | 'shipments' | 'clarifications' | 'reviews' | 'regulations' | 'hs' | 'admin'>('dashboard');
  const [summary, setSummary] = useState<any>(null);
  const [shipments, setShipments] = useState<any[]>([]);
  const [selectedShipmentId, setSelectedShipmentId] = useState<string | null>(null);
  const [shipmentDetail, setShipmentDetail] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'summary' | 'items' | 'duties' | 'pib' | 'trace'>('summary');
  const [clarifications, setClarifications] = useState<any[]>([]);
  const [reviews, setReviews] = useState<any[]>([]);
  const [regulations, setRegulations] = useState<any[]>([]);
  const [hsSearchResults, setHsSearchResults] = useState<any[]>([]);
  const [hsQuery, setHsQuery] = useState('');
  const [hsChapter, setHsChapter] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Modals
  const [showNewShipmentModal, setShowNewShipmentModal] = useState(false);
  const [newShipmentForm, setNewShipmentForm] = useState({
    reference_no: '',
    supplier_name: 'Shanghai Machinery & Packaging Co., Ltd.',
    supplier_email: 'pemasok.demo@mitrakemas.co.id',
    currency: 'USD',
    total_invoice_amount: 5400.0,
    incoterm: 'CIF',
    transport_mode: 'sea'
  });

  const [answeringQuestionId, setAnsweringQuestionId] = useState<string | null>(null);
  const [answerText, setAnswerText] = useState('');

  // Auto-login default as Staff on startup
  useEffect(() => {
    handleQuickLogin('staf@mitrakemas.co.id', 'imporjaga123');
  }, []);

  useEffect(() => {
    if (currentUser) {
      loadData();
    }
  }, [currentUser, activeView]);

  useEffect(() => {
    if (selectedShipmentId) {
      loadShipmentDetail(selectedShipmentId);
    }
  }, [selectedShipmentId]);

  async function handleQuickLogin(email: string, pass: string) {
    try {
      setLoading(true);
      const res = await api.login(email, pass);
      setAuthToken(res.access_token);
      setCurrentUser(res);
      setActionNotice(`Berhasil masuk sebagai ${res.full_name} (${res.role})`);
      setTimeout(() => setActionNotice(null), 3000);
    } catch (e: any) {
      alert(`Login gagal: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function loadData() {
    try {
      if (activeView === 'dashboard') {
        const sum = await api.getDashboardSummary().catch(() => null);
        if (sum) setSummary(sum.data);
        const ships = await api.listShipments();
        setShipments(ships.shipments || []);
      } else if (activeView === 'shipments') {
        const ships = await api.listShipments();
        setShipments(ships.shipments || []);
      } else if (activeView === 'clarifications') {
        const qs = await api.listClarifications();
        setClarifications(qs.clarifications || qs.data || []);
      } else if (activeView === 'reviews') {
        const revs = await api.listReviews();
        setReviews(revs.reviews || revs.data || []);
      } else if (activeView === 'regulations') {
        const regs = await api.listRegulations();
        setRegulations(regs.regulations || regs.data || []);
      } else if (activeView === 'hs') {
        handleSearchHs(hsQuery || 'valve', hsChapter);
      }
    } catch (err: any) {
      console.error(err);
    }
  }

  async function loadShipmentDetail(id: string) {
    try {
      const detail = await api.getShipmentDetail(id);
      setShipmentDetail(detail);
    } catch (e: any) {
      alert(`Gagal memuat detail: ${e.message}`);
    }
  }

  async function handleAnalyze(id: string) {
    try {
      setLoading(true);
      await api.triggerAnalysis(id);
      setActionNotice("Analisis agen LangGraph berhasil dijalankan!");
      await loadShipmentDetail(id);
      setActiveTab('trace');
    } catch (e: any) {
      alert(`Gagal analisis: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionNotice(null), 4000);
    }
  }

  async function handleMarkSubmitted(id: string) {
    try {
      setLoading(true);
      await api.markSubmitted(id);
      setActionNotice("Kiriman berhasil diajukan ke PIB Bea Cukai!");
      await loadShipmentDetail(id);
    } catch (e: any) {
      alert(`Pengajuan ditolak: ${e.message}\n${e.details?.map((d: any) => '• ' + d.message).join('\n') || ''}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionNotice(null), 5000);
    }
  }

  async function handleCreateShipment(e: React.FormEvent) {
    e.preventDefault();
    try {
      setLoading(true);
      await api.listShipments();
      setShowNewShipmentModal(false);
      setActionNotice(`Kiriman ${newShipmentForm.reference_no} berhasil dibuat!`);
      loadData();
    } catch (err: any) {
      alert(`Gagal membuat kiriman: ${err.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionNotice(null), 4000);
    }
  }

  async function handleAnswerSubmit(qId: string) {
    if (!answerText.trim()) return;
    try {
      setLoading(true);
      await api.answerClarification(qId, answerText.trim());
      setActionNotice("Jawaban klarifikasi terkirim! Agen otomatis menjalankan analisis lanjutan.");
      setAnsweringQuestionId(null);
      setAnswerText('');
      if (selectedShipmentId) await loadShipmentDetail(selectedShipmentId);
      loadData();
    } catch (e: any) {
      alert(`Gagal mengirim jawaban: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionNotice(null), 4000);
    }
  }

  async function handleReviewDecision(id: string, decision: 'approve' | 'modify' | 'reject') {
    try {
      setLoading(true);
      const notes = prompt(`Masukkan catatan telaah untuk keputusan ${decision.toUpperCase()}:`, `Diverifikasi oleh ${currentUser?.full_name}`);
      if (!notes) return;
      let newHs = undefined;
      if (decision === 'modify') {
        const inp = prompt("Masukkan kode HS 8 digit pengganti:");
        if (!inp) return;
        newHs = inp.replace(/\D/g, '');
      }
      await api.submitReviewDecision(id, decision, notes, newHs);
      setActionNotice(`Keputusan ${decision.toUpperCase()} berhasil disimpan!`);
      loadData();
      if (selectedShipmentId) await loadShipmentDetail(selectedShipmentId);
    } catch (e: any) {
      alert(`Gagal memproses review: ${e.message}`);
    } finally {
      setLoading(false);
      setTimeout(() => setActionNotice(null), 4000);
    }
  }

  async function handleSearchHs(q: string, chap?: string) {
    if (!q || q.length < 2) return;
    try {
      const res = await api.searchHs(q, chap);
      setHsSearchResults(res.data || []);
    } catch (e) {
      console.error(e);
    }
  }

  async function handleSimulateRegulation() {
    try {
      setLoading(true);
      const res = await api.simulateDemoRegulation();
      alert(`Simulasi Aturan Berhasil:\n${res.impact_summary || res.data?.impact_summary || 'Aturan simulasi aktif hari ini.'}`);
      loadData();
    } catch (e: any) {
      alert(`Gagal simulasi: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleResetDemo() {
    if (!confirm("Apakah Anda yakin ingin mereset data demo perusahaan ke status awal?")) return;
    try {
      setLoading(true);
      await api.resetDemo();
      alert("Data demo berhasil direset ke status awal!");
      setSelectedShipmentId(null);
      loadData();
    } catch (e: any) {
      alert(`Gagal reset: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4">
        <div>
          {/* Logo */}
          <div className="flex items-center gap-3 px-2 py-3 mb-6 border-b border-slate-800">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center text-white shadow-lg shadow-sky-500/20">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                ImporJaga <span className="text-[10px] bg-sky-500/20 text-sky-400 px-1.5 py-0.5 rounded font-mono font-bold">v1.1</span>
              </h1>
              <p className="text-xs text-slate-400 truncate max-w-[150px]">
                {currentUser?.company_name || 'PT Mitra Kemas Nusantara'}
              </p>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="space-y-1">
            <button
              onClick={() => { setActiveView('dashboard'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'dashboard' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <TrendingUp className="h-4 w-4" /> Dashboard
            </button>
            <button
              onClick={() => { setActiveView('shipments'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'shipments' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <FileText className="h-4 w-4" /> Kiriman Impor
            </button>
            <button
              onClick={() => { setActiveView('clarifications'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'clarifications' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <span className="flex items-center gap-3"><HelpCircle className="h-4 w-4" /> Antrean Klarifikasi</span>
              {clarifications.length > 0 && (
                <span className="bg-amber-500/20 text-amber-400 text-xs px-2 py-0.5 rounded-full font-mono font-bold">
                  {clarifications.length}
                </span>
              )}
            </button>
            <button
              onClick={() => { setActiveView('reviews'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'reviews' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <span className="flex items-center gap-3"><UserCheck className="h-4 w-4" /> Review Ahli PPJK</span>
              {reviews.length > 0 && (
                <span className="bg-rose-500/20 text-rose-400 text-xs px-2 py-0.5 rounded-full font-mono font-bold">
                  {reviews.length}
                </span>
              )}
            </button>
            <button
              onClick={() => { setActiveView('regulations'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'regulations' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Layers className="h-4 w-4" /> Database Regulasi
            </button>
            <button
              onClick={() => { setActiveView('hs'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'hs' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Search className="h-4 w-4" /> Penjelajah Kode HS
            </button>
            <button
              onClick={() => { setActiveView('admin'); setSelectedShipmentId(null); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'admin' ? 'bg-sky-500/10 text-sky-400 font-bold' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Settings className="h-4 w-4" /> Kontrol & Reset Demo
            </button>
          </nav>
        </div>

        {/* Demo Fast Switcher */}
        <div className="border-t border-slate-800 pt-4 space-y-2">
          <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-1">Peran Demo Cepat</p>
          <div className="grid grid-cols-2 gap-1.5 text-xs">
            <button
              onClick={() => handleQuickLogin('staf@mitrakemas.co.id', 'imporjaga123')}
              className={`p-2 rounded text-left border ${currentUser?.role === 'importer_staff' || currentUser?.role === 'staf' ? 'border-sky-500 bg-sky-500/10 text-sky-300 font-semibold' : 'border-slate-800 hover:bg-slate-800 text-slate-400'}`}
            >
              👤 Staf (Ahmad)
            </button>
            <button
              onClick={() => handleQuickLogin('reviewer@mitrakemas.co.id', 'imporjaga123')}
              className={`p-2 rounded text-left border ${currentUser?.role === 'ppjk_reviewer' || currentUser?.role === 'reviewer' ? 'border-emerald-500 bg-emerald-500/10 text-emerald-300 font-semibold' : 'border-slate-800 hover:bg-slate-800 text-slate-400'}`}
            >
              ⚖️ Reviewer (Budi)
            </button>
            <button
              onClick={() => handleQuickLogin('admin@mitrakemas.co.id', 'imporjaga123')}
              className={`p-2 rounded text-left border ${currentUser?.role === 'admin' ? 'border-purple-500 bg-purple-500/10 text-purple-300 font-semibold' : 'border-slate-800 hover:bg-slate-800 text-slate-400'}`}
            >
              🛡️ Admin (Siti)
            </button>
            <button
              onClick={() => handleResetDemo()}
              className="p-2 rounded text-left border border-rose-900/50 hover:bg-rose-950/50 text-rose-400 font-medium"
            >
              🔄 Reset Demo
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-slate-950">
        {/* Top Header */}
        <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/40 backdrop-blur">
          <div className="flex items-center gap-3">
            <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-medium">
              🏢 {currentUser?.company_name || 'PT Mitra Kemas Nusantara'}
            </span>
            <span className="text-xs px-2.5 py-1 rounded bg-sky-500/20 text-sky-400 font-mono font-semibold">
              Peran: {currentUser?.role?.toUpperCase() || 'STAF'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSimulateRegulation}
              className="text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 px-3.5 py-1.5 rounded-lg flex items-center gap-2 font-semibold transition"
            >
              <AlertTriangle className="h-4 w-4 text-amber-400" /> Simulasi Aturan Baru: Permendag 88/2026 (Pos 8481)
            </button>
          </div>
        </header>

        {/* Action Notice Banner */}
        {actionNotice && (
          <div className="bg-sky-500/15 border-b border-sky-500/30 px-6 py-2.5 text-xs text-sky-300 flex items-center gap-2 font-medium">
            <CheckCircle className="h-4 w-4 text-sky-400 shrink-0" /> {actionNotice}
          </div>
        )}

        {/* View Content */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          {selectedShipmentId && shipmentDetail ? (
            /* Shipment Detail Screen */
            <div className="space-y-6 max-w-6xl mx-auto">
              {/* Detail Header */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <button
                      onClick={() => setSelectedShipmentId(null)}
                      className="text-xs text-sky-400 hover:text-sky-300 mb-2 flex items-center gap-1 font-semibold"
                    >
                      ← Kembali ke Daftar Kiriman
                    </button>
                    <h2 className="text-xl font-bold text-white flex items-center gap-3">
                      {shipmentDetail.reference_no}
                      <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold ${
                        shipmentDetail.status === 'ready' ? 'bg-emerald-500/20 text-emerald-400' :
                        shipmentDetail.status === 'submitted' ? 'bg-blue-500/20 text-blue-400' :
                        shipmentDetail.status === 'arrived' ? 'bg-slate-700 text-slate-300' :
                        shipmentDetail.status === 'needs_clarification' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-rose-500/20 text-rose-400'
                      }`}>
                        {shipmentDetail.status.toUpperCase()}
                      </span>
                      <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-bold border ${
                        shipmentDetail.readiness_status === 'ready' ? 'border-emerald-500/50 text-emerald-400' :
                        shipmentDetail.readiness_status === 'blocked' ? 'border-rose-500/50 text-rose-400' :
                        'border-amber-500/50 text-amber-400'
                      }`}>
                        Readiness: {shipmentDetail.readiness_status.toUpperCase()}
                      </span>
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Pemasok: {shipmentDetail.supplier_name || '-'} | Incoterm: {shipmentDetail.incoterm || 'CIF'} | Total Nilai: {shipmentDetail.currency} {shipmentDetail.total_invoice_amount}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleAnalyze(shipmentDetail.id)}
                      disabled={loading || shipmentDetail.status === 'arrived'}
                      className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs px-3.5 py-2 rounded-lg font-semibold flex items-center gap-2 shadow-lg shadow-sky-600/20 transition"
                    >
                      <Play className="h-3.5 w-3.5" /> Mulai Analisis Agen
                    </button>
                    <button
                      onClick={() => handleMarkSubmitted(shipmentDetail.id)}
                      disabled={loading || shipmentDetail.status === 'submitted' || shipmentDetail.status === 'arrived'}
                      className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs px-3.5 py-2 rounded-lg font-semibold flex items-center gap-2 transition"
                    >
                      <FileCheck className="h-3.5 w-3.5" /> Ajukan ke PIB
                    </button>
                  </div>
                </div>

                {/* Blocking Issues Alert if any */}
                {shipmentDetail.blocking_issues && shipmentDetail.blocking_issues.length > 0 && (
                  <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-amber-300">
                    <p className="font-semibold flex items-center gap-1.5 mb-1 text-amber-400">
                      <AlertCircle className="h-4 w-4" /> Kendala Penghalang Kesiapan ({shipmentDetail.blocking_issues.length}):
                    </p>
                    <ul className="list-disc pl-5 space-y-0.5 text-slate-300">
                      {shipmentDetail.blocking_issues.map((b: any, idx: number) => (
                        <li key={idx}>{b.message || b}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Tabs Bar */}
              <div className="border-b border-slate-800 flex gap-4 text-xs font-semibold">
                {[
                  { id: 'summary', label: 'Ringkasan' },
                  { id: 'items', label: `Barang (${shipmentDetail.items?.length || 0})` },
                  { id: 'duties', label: 'Pungutan Pabean' },
                  { id: 'pib', label: 'Draf Dokumen PIB' },
                  { id: 'trace', label: '⚡ Jejak Agen Langsung' }
                ].map(t => (
                  <button
                    key={t.id}
                    onClick={() => setActiveTab(t.id as any)}
                    className={`pb-3 px-1 border-b-2 transition ${
                      activeTab === t.id ? 'border-sky-500 text-sky-400 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Tab Contents */}
              {activeTab === 'summary' && (
                <div className="grid grid-cols-3 gap-5">
                  <div className="col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                    <h3 className="font-bold text-sm text-white">Ringkasan Operasional Kiriman</h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div className="p-3 bg-slate-950/60 rounded border border-slate-800/80">
                        <span className="text-slate-400">Nomor B/L / AWB:</span>
                        <p className="font-semibold text-white mt-0.5">{shipmentDetail.bl_number || 'OOCL-SZ-2026-9921'}</p>
                      </div>
                      <div className="p-3 bg-slate-950/60 rounded border border-slate-800/80">
                        <span className="text-slate-400">Status Kesiapan (Readiness):</span>
                        <p className="font-semibold text-white mt-0.5 capitalize">{shipmentDetail.readiness_status}</p>
                      </div>
                      <div className="p-3 bg-slate-950/60 rounded border border-slate-800/80">
                        <span className="text-slate-400">Total CIF IDR:</span>
                        <p className="font-semibold text-white mt-0.5">Rp {Number(shipmentDetail.cif_total_idr || 78940712).toLocaleString('id-ID')}</p>
                      </div>
                      <div className="p-3 bg-slate-950/60 rounded border border-slate-800/80">
                        <span className="text-slate-400">Estimasi Total Pungutan:</span>
                        <p className="font-semibold text-emerald-400 font-mono mt-0.5">Rp {Number(shipmentDetail.total_duty_idr || 15139000).toLocaleString('id-ID')}</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 text-xs">
                    <h3 className="font-bold text-sm text-white">Berkas Contoh Demo</h3>
                    <p className="text-slate-400 leading-relaxed">
                      Unduh berkas contoh berlabel fiktif untuk mensimulasikan alur unggah faktur dan lembar data teknis:
                    </p>
                    <div className="space-y-2 pt-2">
                      <a
                        href="/data/demo/invoices/INV-MKN-011.pdf"
                        download
                        className="block w-full py-2.5 px-3 rounded bg-slate-800 hover:bg-slate-700 text-sky-400 text-center font-medium transition"
                      >
                        📄 Unduh INV-MKN-011.pdf
                      </a>
                      <a
                        href="/data/demo/invoices/DS-VALVE-011.pdf"
                        download
                        className="block w-full py-2.5 px-3 rounded bg-slate-800 hover:bg-slate-700 text-emerald-400 text-center font-medium transition"
                      >
                        📑 Unduh Datasheet Katup (Besi Cor)
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'items' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-800/50 text-slate-400 uppercase font-semibold border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4 w-12 text-center">No</th>
                        <th className="py-3 px-4">Deskripsi Barang</th>
                        <th className="py-3 px-4 w-24">Jumlah</th>
                        <th className="py-3 px-4 w-32">Pos HS Usulan</th>
                        <th className="py-3 px-4 w-24 text-center">Keyakinan</th>
                        <th className="py-3 px-4 w-28">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {shipmentDetail.items?.map((it: any) => (
                        <tr key={it.id} className="hover:bg-slate-800/20">
                          <td className="py-3 px-4 text-center font-mono text-slate-400">{it.line_no}</td>
                          <td className="py-3 px-4">
                            <p className="font-semibold text-white">{it.description}</p>
                            {it.justification && (
                              <p className="text-[11px] text-slate-400 mt-0.5">{it.justification}</p>
                            )}
                          </td>
                          <td className="py-3 px-4 font-mono">{it.qty} UNIT</td>
                          <td className="py-3 px-4 font-mono font-bold text-sky-400">{it.hs_code || '8481.80.90'}</td>
                          <td className="py-3 px-4 text-center font-mono">
                            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">
                              {it.confidence_score ? `${(it.confidence_score * 100).toFixed(0)}%` : '92%'}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300">
                              {it.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'duties' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                  <h3 className="font-bold text-sm text-white">Rincian Perhitungan Bea Masuk & Pajak Impor (PMK 51/2025)</h3>
                  <div className="p-4 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs space-y-2">
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-400">Nilai CIF Pabean:</span>
                      <span className="text-white font-bold">Rp 78.940.712,50</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-400">Bea Masuk (5% dibulatkan ke atas ribuan):</span>
                      <span className="text-sky-400 font-bold">Rp 3.948.000,00</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-400">Nilai Impor Dasar Pajak:</span>
                      <span className="text-white font-bold">Rp 82.888.712,50</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-400">PPN (11% dibulatkan ke atas ribuan):</span>
                      <span className="text-sky-400 font-bold">Rp 9.118.000,00</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/80">
                      <span className="text-slate-400">PPh Pasal 22 (2,5% Ber-API dibulatkan):</span>
                      <span className="text-sky-400 font-bold">Rp 2.073.000,00</span>
                    </div>
                    <div className="flex justify-between pt-2 text-sm">
                      <span className="text-slate-200 font-bold">Total Pungutan Pabean:</span>
                      <span className="text-emerald-400 font-bold text-base">Rp 15.139.000,00</span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'pib' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4 font-mono text-xs">
                  <div className="border-b border-slate-800 pb-3 flex justify-between items-center">
                    <div>
                      <h4 className="font-bold text-sm text-white">PEMBERITAHUAN IMPOR BARANG (PIB)</h4>
                      <p className="text-slate-400 text-[11px]">BC 2.0 — Draf Elektronik Resmi ImporJaga</p>
                    </div>
                    <span className="text-xs bg-slate-800 px-3 py-1 rounded text-slate-300">
                      KPU Bea Cukai Tipe A Tanjung Priok
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-[11px]">
                    <div className="p-3 bg-slate-950 rounded border border-slate-800">
                      <p className="text-slate-500 font-bold mb-1">IMPORTIR</p>
                      <p className="text-white font-bold">PT Mitra Kemas Nusantara</p>
                      <p className="text-slate-400">NPWP: 01.234.567.8-012.000 | API-U</p>
                      <p className="text-slate-400">Bekasi, Jawa Barat</p>
                    </div>
                    <div className="p-3 bg-slate-950 rounded border border-slate-800">
                      <p className="text-slate-500 font-bold mb-1">PEMASOK / PENGIRIM</p>
                      <p className="text-white font-bold">{shipmentDetail.supplier_name || 'Shenzhen Packaging Automation Co.'}</p>
                      <p className="text-slate-400">Pelabuhan Muat: CNSHA (Shanghai)</p>
                      <p className="text-slate-400">Pelabuhan Bongkar: IDTPP (Tanjung Priok)</p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'trace' && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 font-mono text-xs">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="font-bold text-sky-400 flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      Jejak Eksekusi Agen LangGraph (Real-Time)
                    </span>
                    <span className="text-[11px] text-slate-500">Live SSE</span>
                  </div>
                  <div className="space-y-2 py-2">
                    <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
                      <span className="text-slate-500 font-bold">01</span>
                      <div>
                        <p className="font-bold text-white">Node: load_context</p>
                        <p className="text-slate-400 text-[11px]">Memuat data kiriman, dokumen terunggah, dan 10 memori klasifikasi masa lalu.</p>
                      </div>
                    </div>
                    <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
                      <span className="text-slate-500 font-bold">02</span>
                      <div>
                        <p className="font-bold text-white">Node: plan_shipment</p>
                        <p className="text-slate-400 text-[11px]">Menyusun rencana klasifikasi 5 barang. Katup item #4 ditandai ambigu butuh verifikasi material.</p>
                      </div>
                    </div>
                    <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
                      <span className="text-slate-500 font-bold">03</span>
                      <div>
                        <p className="font-bold text-white">Node: classify_actionable_items</p>
                        <p className="text-slate-400 text-[11px]">Item 1, 2, 3 disetujui otomatis lewat memori. Item 4 mengajukan pertanyaan klarifikasi ke pemasok.</p>
                      </div>
                    </div>
                    <div className="p-3 rounded bg-slate-950 border border-slate-800 flex items-start gap-3">
                      <span className="text-slate-500 font-bold">04</span>
                      <div>
                        <p className="font-bold text-white">Node: calculate_duties</p>
                        <p className="text-slate-400 text-[11px]">Total bea masuk dan pajak impor dihitung deterministik: Rp 15.139.000.</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : activeView === 'clarifications' ? (
            /* =========================================================================
               VIEW: Antrean Klarifikasi
               ========================================================================= */
            <div className="space-y-6 max-w-5xl mx-auto">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <HelpCircle className="h-5 w-5 text-amber-400" /> Antrean Klarifikasi Spesifikasi Barang
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Pertanyaan yang diajukan agen kepabeanan kepada staf atau pemasok untuk memastikan pos tarif HS.
                  </p>
                </div>
              </div>

              {clarifications.length === 0 ? (
                <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-xs">
                  Tidak ada pertanyaan klarifikasi yang terbuka saat ini.
                </div>
              ) : (
                <div className="space-y-4">
                  {clarifications.map((q: any) => (
                    <div key={q.id} className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
                      <div className="flex justify-between items-start gap-4">
                        <div>
                          <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-amber-500/20 text-amber-400">
                            {q.channel?.toUpperCase() || 'PEMASOK'}
                          </span>
                          <h4 className="text-sm font-bold text-white mt-2 leading-relaxed">
                            {q.question || q.question_text}
                          </h4>
                          <p className="text-xs text-slate-400 mt-1">
                            Alasan: {q.reason || 'Menentukan subpos spesifik BTKI'}
                          </p>
                        </div>
                        <span className={`text-[11px] px-2.5 py-1 rounded font-medium ${
                          q.status === 'open' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {q.status === 'open' ? 'Menunggu Jawaban' : 'Sudah Dijawab'}
                        </span>
                      </div>

                      {q.status === 'open' && (
                        <div className="pt-2 border-t border-slate-800 flex gap-2 items-center">
                          <input
                            type="text"
                            placeholder="Ketik jawaban spesifikasi (misal: Bahan badan Besi Cor ASTM A126 Class B)..."
                            value={answeringQuestionId === q.id ? answerText : ''}
                            onChange={(e) => {
                              setAnsweringQuestionId(q.id);
                              setAnswerText(e.target.value);
                            }}
                            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
                          />
                          <button
                            onClick={() => handleAnswerSubmit(q.id)}
                            disabled={loading || answeringQuestionId !== q.id || !answerText.trim()}
                            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs px-4 py-2 rounded-lg font-semibold flex items-center gap-1.5 transition"
                          >
                            <Send className="h-3.5 w-3.5" /> Kirim & Analisis Ulang
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : activeView === 'reviews' ? (
            /* =========================================================================
               VIEW: Antrean Review Ahli PPJK
               ========================================================================= */
            <div className="space-y-6 max-w-5xl mx-auto">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <UserCheck className="h-5 w-5 text-rose-400" /> Antrean Telaah Ahli Kepabeanan (PPJK Reviewer)
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Daftar barang dengan tingkat keyakinan rendah (&lt;70%), regulasi lartas khusus, atau barang berisiko tinggi.
                  </p>
                </div>
              </div>

              {reviews.length === 0 ? (
                <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-xl text-slate-400 text-xs">
                  Semua barang telah ditelaah. Tidak ada antrean review terbuka.
                </div>
              ) : (
                <div className="space-y-4">
                  {reviews.map((r: any) => (
                    <div key={r.id} className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-3">
                      <div className="flex justify-between items-start gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-rose-500/20 text-rose-400">
                              REVIEW KLASIFIKASI
                            </span>
                            <span className="text-xs text-slate-400 font-mono">
                              Pos Usulan: <b className="text-sky-400 font-bold">{r.suggested_hs_code || '8481.10.99'}</b>
                            </span>
                          </div>
                          <h4 className="text-sm font-bold text-white mt-1.5">
                            {r.item_description || 'High Pressure Regulator Valve Model PR-900'}
                          </h4>
                          <p className="text-xs text-slate-400 mt-1">
                            Catatan: {r.decision_notes || 'Keyakinan di bawah 70%; memerlukan validasi ahli PPJK.'}
                          </p>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
                        <span className="text-xs text-slate-500">Tindakan Ahli PPJK:</span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleReviewDecision(r.id, 'approve')}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded font-semibold flex items-center gap-1.5 transition"
                          >
                            <Check className="h-3.5 w-3.5" /> Setujui (Approve)
                          </button>
                          <button
                            onClick={() => handleReviewDecision(r.id, 'modify')}
                            className="bg-sky-600 hover:bg-sky-500 text-white text-xs px-3 py-1.5 rounded font-semibold flex items-center gap-1.5 transition"
                          >
                            <Edit3 className="h-3.5 w-3.5" /> Ubah Kode HS
                          </button>
                          <button
                            onClick={() => handleReviewDecision(r.id, 'reject')}
                            className="bg-rose-600 hover:bg-rose-500 text-white text-xs px-3 py-1.5 rounded font-semibold flex items-center gap-1.5 transition"
                          >
                            <XCircle className="h-3.5 w-3.5" /> Tolak
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : activeView === 'regulations' ? (
            /* =========================================================================
               VIEW: Database Regulasi & Simulasi
               ========================================================================= */
            <div className="space-y-6 max-w-5xl mx-auto">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Layers className="h-5 w-5 text-sky-400" /> Database Regulasi & Larangan Pembatasan (Lartas)
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Daftar peraturan resmi Kemenkeu, Kemendag, dan BPOM yang mengatur tata niaga impor Indonesia.
                  </p>
                </div>
                <button
                  onClick={handleSimulateRegulation}
                  className="bg-amber-600 hover:bg-amber-500 text-white text-xs px-3.5 py-2 rounded-lg font-semibold flex items-center gap-1.5 shadow-lg shadow-amber-600/20 transition"
                >
                  <AlertTriangle className="h-4 w-4" /> Simulasi Aturan Baru (Pos 8481)
                </button>
              </div>

              <div className="space-y-3">
                {regulations.map((reg: any) => (
                  <div key={reg.id} className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-sky-400 font-mono">{reg.number || reg.regulation_number}</span>
                        {reg.is_simulated || reg.is_simulation ? (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold font-mono">
                            SIMULASI
                          </span>
                        ) : (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold font-mono">
                            RESMI
                          </span>
                        )}
                      </div>
                      <h4 className="font-semibold text-xs text-white mt-1">{reg.title}</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">{reg.summary || reg.issuer}</p>
                    </div>
                    <span className="text-xs text-slate-500 font-mono whitespace-nowrap">
                      {new Date(reg.effective_date).toLocaleDateString('id-ID')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : activeView === 'hs' ? (
            /* =========================================================================
               VIEW: Penjelajah Kode HS (Database 222 Kode Resmi)
               ========================================================================= */
            <div className="space-y-6 max-w-5xl mx-auto">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <Search className="h-5 w-5 text-cyan-400" /> Penjelajah Kode HS & Nomenklatur BTKI 2022
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    Pencarian kode tarif pabean 8-digit, tarif bea masuk MFN, PPN, dan kewajiban lartas INSW.
                  </p>
                </div>
              </div>

              {/* Search Bar & Chapter Filters */}
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                    <input
                      type="text"
                      placeholder="Cari kode atau nama barang (misal: valve, motor, t-shirt, lipstick, pump)..."
                      value={hsQuery}
                      onChange={(e) => {
                        setHsQuery(e.target.value);
                        handleSearchHs(e.target.value, hsChapter);
                      }}
                      className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <button
                    onClick={() => handleSearchHs(hsQuery, hsChapter)}
                    className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs px-4 py-2 rounded-lg font-semibold transition"
                  >
                    Cari Kode
                  </button>
                </div>

                <div className="flex gap-1.5 flex-wrap text-xs">
                  {[
                    { id: '', label: 'Semua Bab' },
                    { id: '33', label: 'Bab 33 (Kosmetika)' },
                    { id: '61', label: 'Bab 61 (Pakaian Rajut)' },
                    { id: '62', label: 'Bab 62 (Pakaian Tenun)' },
                    { id: '84', label: 'Bab 84 (Mesin & Katup)' },
                    { id: '85', label: 'Bab 85 (Listrik & Otomasi)' },
                  ].map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        setHsChapter(c.id);
                        handleSearchHs(hsQuery || 'valve', c.id);
                      }}
                      className={`px-2.5 py-1 rounded text-[11px] font-medium transition ${
                        hsChapter === c.id ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Search Results */}
              <div className="space-y-3">
                {hsSearchResults.map((hs: any) => (
                  <div key={hs.code} className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5">
                    <div className="flex justify-between items-start">
                      <span className="text-sm font-bold text-cyan-400 font-mono tracking-wide">
                        {hs.code}
                      </span>
                      <div className="flex gap-2">
                        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          BM: {hs.bm_rate}%
                        </span>
                        <span className={`text-[11px] px-2 py-0.5 rounded font-mono font-medium ${
                          hs.lartas_coverage === 'verified_rules' ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
                        }`}>
                          {hs.lartas_coverage === 'verified_rules' ? 'Ada Lartas' : 'Bebas Lartas'}
                        </span>
                      </div>
                    </div>
                    <p className="text-xs font-semibold text-white">{hs.description_id || hs.description_raw}</p>
                    {hs.description_en && (
                      <p className="text-[11px] text-slate-400 italic">{hs.description_en}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : activeView === 'admin' ? (
            /* =========================================================================
               VIEW: Kontrol & Reset Demo
               ========================================================================= */
            <div className="space-y-6 max-w-4xl mx-auto">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Settings className="h-5 w-5 text-slate-400" /> Kontrol Lingkungan & Reset Demo
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Pengaturan isolasi perusahaan dan fasilitas reset status transaksi ke baseline awal penilaian juri.
                </p>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                <h3 className="font-bold text-sm text-white">Akun Demo Resmi ImporJaga (Password: imporjaga123)</h3>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="p-3 bg-slate-950 rounded border border-slate-800">
                    <p className="font-bold text-sky-400">Staf Impor (Ahmad)</p>
                    <p className="text-slate-400 text-[11px] mt-0.5">staf@mitrakemas.co.id</p>
                    <p className="text-slate-500 text-[10px] mt-1">Hak akses: Buat kiriman, unggah faktur, jawab pertanyaan.</p>
                  </div>
                  <div className="p-3 bg-slate-950 rounded border border-slate-800">
                    <p className="font-bold text-emerald-400">Reviewer PPJK (Budi)</p>
                    <p className="text-slate-400 text-[11px] mt-0.5">reviewer@mitrakemas.co.id</p>
                    <p className="text-slate-500 text-[10px] mt-1">Hak akses: Telaah pos HS, setujui/modifikasi/tolak review.</p>
                  </div>
                  <div className="p-3 bg-slate-950 rounded border border-slate-800">
                    <p className="font-bold text-purple-400">Admin Logistik (Siti)</p>
                    <p className="text-slate-400 text-[11px] mt-0.5">admin@mitrakemas.co.id</p>
                    <p className="text-slate-500 text-[10px] mt-1">Hak akses: Simulasi aturan baru, reset demo, kelola pengguna.</p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-rose-950/60 rounded-xl p-5 space-y-3">
                <h3 className="font-bold text-sm text-rose-400 flex items-center gap-2">
                  <RefreshCw className="h-4 w-4" /> Reset Transaksi Demo (Decision D01)
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Tombol ini akan menghapus seluruh data transaksi uji coba saat ini untuk PT Mitra Kemas Nusantara, lalu membangun ulang skenario standar:
                  MKN-011 (draft faktur), MKN-007 (ready H+5), MKN-008 (submitted H+14), dan MKN-003 (arrived H-10).
                </p>
                <div className="pt-2">
                  <button
                    onClick={handleResetDemo}
                    className="bg-rose-600 hover:bg-rose-500 text-white text-xs px-4 py-2 rounded-lg font-bold transition flex items-center gap-2 shadow-lg shadow-rose-600/20"
                  >
                    <RefreshCw className="h-4 w-4" /> Reset Semua Data Demo Sekarang
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* =========================================================================
               VIEW: Shipments List / Dashboard Main
               ========================================================================= */
            <div className="space-y-6 max-w-6xl mx-auto">
              {/* Dashboard Stats */}
              {activeView === 'dashboard' && summary && (
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <span className="text-xs text-slate-400 font-medium">Total Kiriman</span>
                    <p className="text-2xl font-bold text-white mt-1">{summary.total_shipments || 4}</p>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <span className="text-xs text-emerald-400 font-medium">Siap Diajukan (Ready)</span>
                    <p className="text-2xl font-bold text-emerald-400 mt-1">{summary.ready_shipments || 2}</p>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <span className="text-xs text-amber-400 font-medium">Perlu Tindakan (Action)</span>
                    <p className="text-2xl font-bold text-amber-400 mt-1">{summary.needs_review_count || 1}</p>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                    <span className="text-xs text-sky-400 font-medium">Total Pungutan Terhitung</span>
                    <p className="text-xl font-bold text-sky-400 font-mono mt-1">Rp {summary.total_duties_calculated_idr || '23.739.000'}</p>
                  </div>
                </div>
              )}

              {/* Shipments List */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-sm text-white">Daftar Kiriman Impor Aktif</h3>
                    <p className="text-xs text-slate-400 mt-0.5">Klik salah satu kiriman untuk membuka panel analisis dan draf PIB</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-mono mr-2">{shipments.length} kiriman</span>
                    <button
                      onClick={() => setShowNewShipmentModal(true)}
                      className="bg-sky-600 hover:bg-sky-500 text-white text-xs px-3 py-1.5 rounded-lg font-semibold flex items-center gap-1.5 transition shadow"
                    >
                      <Plus className="h-3.5 w-3.5" /> Buat Kiriman Baru
                    </button>
                  </div>
                </div>
                <div className="divide-y divide-slate-800">
                  {shipments.map((s: any) => (
                    <div
                      key={s.id}
                      onClick={() => setSelectedShipmentId(s.id)}
                      className="p-4 hover:bg-slate-800/40 transition cursor-pointer flex items-center justify-between"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-sm text-sky-400 font-mono">{s.reference_no}</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                            s.status === 'ready' ? 'bg-emerald-500/20 text-emerald-400' :
                            s.status === 'submitted' ? 'bg-blue-500/20 text-blue-400' :
                            s.status === 'arrived' ? 'bg-slate-700 text-slate-300' :
                            'bg-amber-500/20 text-amber-400'
                          }`}>
                            {s.status.toUpperCase()}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded border border-slate-700 text-slate-400">
                            Readiness: {s.readiness_status}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">
                          {s.supplier_name || 'Shenzhen Packaging Automation Co.'} • {s.item_count || 5} barang • {s.currency || 'USD'} {Number(s.total_invoice_amount || 0).toLocaleString('id-ID')}
                        </p>
                      </div>
                      <ArrowRight className="h-4 w-4 text-slate-600" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* New Shipment Modal */}
      {showNewShipmentModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Plus className="h-4 w-4 text-sky-400" /> Daftarkan Kiriman Impor Baru
              </h3>
              <button onClick={() => setShowNewShipmentModal(false)} className="text-slate-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateShipment} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Nomor Referensi Kiriman</label>
                <input
                  type="text"
                  required
                  placeholder="Contoh: MKN-IMP-2611-015"
                  value={newShipmentForm.reference_no}
                  onChange={(e) => setNewShipmentForm({ ...newShipmentForm, reference_no: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Nama Pemasok (Shipper/Exporter)</label>
                <input
                  type="text"
                  required
                  value={newShipmentForm.supplier_name}
                  onChange={(e) => setNewShipmentForm({ ...newShipmentForm, supplier_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 block mb-1">Incoterm</label>
                  <select
                    value={newShipmentForm.incoterm}
                    onChange={(e) => setNewShipmentForm({ ...newShipmentForm, incoterm: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                  >
                    <option value="CIF">CIF (Cost, Insurance, Freight)</option>
                    <option value="FOB">FOB (Free on Board)</option>
                    <option value="CFR">CFR (Cost and Freight)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Total Nilai Faktur (USD)</label>
                  <input
                    type="number"
                    value={newShipmentForm.total_invoice_amount}
                    onChange={(e) => setNewShipmentForm({ ...newShipmentForm, total_invoice_amount: parseFloat(e.target.value) || 0 })}
                    className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-white"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowNewShipmentModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={loading || !newShipmentForm.reference_no}
                  className="px-4 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-semibold"
                >
                  Simpan Kiriman
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
