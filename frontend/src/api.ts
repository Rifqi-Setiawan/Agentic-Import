const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export function getAuthToken(): string | null {
  return localStorage.getItem('imporjaga_token');
}

export function setAuthToken(token: string) {
  localStorage.setItem('imporjaga_token', token);
}

export function removeAuthToken() {
  localStorage.removeItem('imporjaga_token');
}

async function request(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    ...(options.headers as Record<string, string> || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const message = errorData?.error?.message || errorData?.detail || `HTTP Error ${res.status}`;
    const err = new Error(message) as any;
    err.status = res.status;
    err.details = errorData?.error?.details || [];
    throw err;
  }

  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    }),

  getMe: () => request('/auth/me'),

  getDashboardSummary: () => request('/dashboard/summary'),

  listShipments: (status?: string) =>
    request(`/shipments${status ? `?status=${status}` : ''}`),

  getShipmentDetail: (id: string) => request(`/shipments/${id}`),

  getShipmentItems: (id: string) => request(`/shipments/${id}/items`),

  getShipmentDocuments: (id: string) => request(`/shipments/${id}/documents`),

  getShipmentChecklist: (id: string) => request(`/shipments/${id}/checklist`),

  getShipmentPib: (id: string) => request(`/shipments/${id}/pib-draft`),

  getShipmentMessages: (id: string) => request(`/shipments/${id}/messages`),

  uploadDocument: (shipmentId: string, file: File, docType = 'invoice') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);
    return request(`/shipments/${shipmentId}/documents`, {
      method: 'POST',
      body: formData
    });
  },

  triggerAnalysis: (shipmentId: string) =>
    request(`/shipments/${shipmentId}/analyze`, { method: 'POST' }),

  markSubmitted: (shipmentId: string) =>
    request(`/shipments/${shipmentId}/mark-submitted`, { method: 'POST' }),

  markArrived: (shipmentId: string) =>
    request(`/shipments/${shipmentId}/mark-arrived`, { method: 'POST' }),

  listClarifications: (status = 'open') =>
    request(`/clarifications?status_filter=${status}`),

  answerClarification: (id: string, answerText: string) =>
    request(`/clarifications/${id}/answer`, {
      method: 'POST',
      body: JSON.stringify({ answer_text: answerText })
    }),

  listReviews: (status = 'open') =>
    request(`/reviews?status_filter=${status}`),

  submitReviewDecision: (id: string, decision: 'approve' | 'modify' | 'reject', notes: string, modifiedHsCode?: string) =>
    request(`/reviews/${id}/decision`, {
      method: 'POST',
      body: JSON.stringify({
        decision,
        notes,
        modified_hs_code: modifiedHsCode
      })
    }),

  listRegulations: () => request('/regulations'),

  simulateDemoRegulation: (title = 'Permendag No. 88/2026 — Pengawasan Katup Industri Pos 8481') =>
    request('/regulations/simulate-demo', {
      method: 'POST',
      body: JSON.stringify({
        hs_prefix: '8481',
        requirement_code: 'LS_VALVE_NEW_2026',
        title
      })
    }),

  resetDemo: () => request('/admin/demo/reset', { method: 'POST' }),

  searchHs: (q: string, chapter?: string) =>
    request(`/hs-codes/search?q=${encodeURIComponent(q)}${chapter ? `&chapter=${chapter}` : ''}`),

  getHsDetail: (code: string) => request(`/hs-codes/${code}`),

  getStreamToken: (runId: string) =>
    request(`/runs/${runId}/stream-token`, { method: 'POST' })
};
