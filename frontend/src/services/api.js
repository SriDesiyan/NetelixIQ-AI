import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2min for model training
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor ───────────────────────────────────────────
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'API error'
    return Promise.reject(new Error(message))
  }
)

// ── API Methods ────────────────────────────────────────────────────

export const healthApi = {
  check: () => api.get('/health'),
}

export const ingestApi = {
  upload: (file, channel) => {
    const form = new FormData()
    form.append('file', file)
    form.append('channel', channel)
    return api.post('/ingest/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  uploadMulti: (files, channels) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    form.append('channels', channels.join(','))
    return api.post('/ingest/upload-multi', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  loadDemo: () => api.post('/ingest/demo'),

  getSessionSummary: (sessionId) => api.get(`/ingest/sessions/${sessionId}/summary`),
}

export const forecastApi = {
  generate: (sessionId, horizon = 30, metric = 'revenue', retrain = false) =>
    api.post(`/forecast/${sessionId}?horizon=${horizon}&metric=${metric}&retrain=${retrain}`),

  getChannelContribution: (sessionId, horizon = 30) =>
    api.get(`/forecast/${sessionId}/channel-contribution?horizon=${horizon}`),

  getHistory: (sessionId) => api.get(`/forecast/${sessionId}/history`),
}

export const simulateApi = {
  runBudget: (payload) => api.post('/simulate/budget', payload),
  getOptimal: (sessionId, totalBudget = 25000, horizonDays = 30) =>
    api.get(`/simulate/${sessionId}/optimal?total_budget=${totalBudget}&horizon_days=${horizonDays}`),
}

export const analystApi = {
  getForecastExplanation: (sessionId, horizon = 30) =>
    api.get(`/analyst/${sessionId}/forecast-explanation?horizon=${horizon}`),
  getRecommendations: (sessionId) => api.get(`/analyst/${sessionId}/recommendations`),
  getRisk: (sessionId, horizon = 30) =>
    api.get(`/analyst/${sessionId}/risk?horizon=${horizon}`),
  getExecutiveSummary: (sessionId, horizon = 30) =>
    api.get(`/analyst/${sessionId}/executive-summary?horizon=${horizon}`),
}

export const copilotApi = {
  chat: (payload) => api.post('/copilot/chat', payload),
  getHistory: (chatId) => api.get(`/copilot/${chatId}/history`),
  clearHistory: (chatId) => api.delete(`/copilot/${chatId}`),
}

export const reportsApi = {
  downloadPdf: async (sessionId, horizon = 30) => {
    const response = await axios.get(`${BASE_URL}/reports/${sessionId}/pdf?horizon=${horizon}`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `netelixiq_report_${sessionId.slice(0, 8)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  },

  downloadCsv: async (sessionId, horizon = 30) => {
    const response = await axios.get(`${BASE_URL}/reports/${sessionId}/csv?horizon=${horizon}`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `forecast_${sessionId.slice(0, 8)}_${horizon}d.csv`
    a.click()
    URL.revokeObjectURL(url)
  },
}

export default api
