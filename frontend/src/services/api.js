import axios from "axios"

const BASE = "http://localhost:8000/api/v1"

const http = axios.create({
  baseURL: BASE,
  timeout: 90_000,
  headers: { "Content-Type": "application/json" },
})

// ── Response interceptor: unwrap data ─────────────────────────────────────────
http.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg =
      err.response?.data?.error ||
      err.response?.data?.detail ||
      err.message ||
      "Unknown error"
    return Promise.reject(new Error(msg))
  }
)

// ── Upload ────────────────────────────────────────────────────────────────────
export const api = {
  // Upload
  uploadCSV:        (file)   => { const f = new FormData(); f.append("file",file); return http.post("/upload/csv", f, { headers:{"Content-Type":"multipart/form-data"} }) },
  generateSample:   ()       => http.post("/upload/generate-sample"),
  uploadStatus:     ()       => http.get("/upload/status"),
  clearData:        ()       => http.delete("/upload/clear"),

  // Dashboard
  dashboardSummary: ()       => http.get("/dashboard/summary"),
  historical:       (device="ALL", res="hourly", limit=500, from_=null, to_=null) => {
    const p = new URLSearchParams({ device_id:device, resolution:res, limit })
    if (from_) p.append("date_from", from_)
    if (to_)   p.append("date_to", to_)
    return http.get(`/dashboard/historical?${p}`)
  },
  deviceBreakdown:  ()       => http.get("/dashboard/device-breakdown"),
  hourlyPattern:    (dev="ALL") => http.get(`/dashboard/hourly-pattern?device_id=${dev}`),
  weeklyPattern:    (dev="ALL") => http.get(`/dashboard/weekly-pattern?device_id=${dev}`),
  monthlyTrend:     (dev="ALL") => http.get(`/dashboard/monthly-trend?device_id=${dev}`),
  costAnalysis:     ()       => http.get("/dashboard/cost-analysis"),
  statistics:       (dev="ALL") => http.get(`/dashboard/statistics?device_id=${dev}`),

  // Forecast
  runForecast:      (body)   => http.post("/forecast/run", body),
  batchForecast:    (body)   => http.post("/forecast/batch", body),
  quickForecast:    (h)      => http.get(`/forecast/quick/${h}`),
  forecastDevices:  ()       => http.get("/forecast/devices"),

  // Anomaly
  runAnomaly:       (body)   => http.post("/anomaly/run", body),
  quickAnomaly:     ()       => http.get("/anomaly/quick"),
  anomalySummary:   ()       => http.get("/anomaly/summary"),

  // Optimization
  recommendations:  (dev="ALL") => http.get(`/optimization/recommendations?device_id=${dev}`),
  peakAnalysis:     (dev="ALL") => http.get(`/optimization/peak-analysis?device_id=${dev}`),
  savingsSummary:   ()       => http.get("/optimization/savings-summary"),
  deviceStats:      ()       => http.get("/optimization/device-stats"),

  // Simulation
  runSimulation:    (body)   => http.post("/simulation/run", body),
  scenarios:        ()       => http.get("/simulation/scenarios"),
  simulationHistory:()       => http.get("/simulation/history"),

  // Alerts
  listAlerts:       (params={}) => http.get("/alerts/", { params }),
  createAlert:      (body)   => http.post("/alerts/", body),
  alertCounts:      ()       => http.get("/alerts/counts"),
  markRead:         (id)     => http.patch(`/alerts/${id}/read`),
  resolveAlert:     (id)     => http.patch(`/alerts/${id}/resolve`),
  markAllRead:      ()       => http.post("/alerts/mark-all-read"),
  deleteAlert:      (id)     => http.delete(`/alerts/${id}`),

  // Devices
  listDevices:      ()       => http.get("/devices/"),
  deviceDetail:     (id)     => http.get(`/devices/${id}`),
  deviceForecast:   (id, h="24h") => http.get(`/devices/${id}/forecast?horizon=${h}`),
  deviceAnomalies:  (id)     => http.get(`/devices/${id}/anomalies`),
  deviceHistory:    (id, res="hourly") => http.get(`/devices/${id}/history?resolution=${res}`),

  // Reports & Export
  reportSummary:    ()       => http.get("/reports/summary"),
  exportCSV:        (dev="ALL") => `${BASE}/reports/export/csv?device_id=${dev}`,
  exportReportCSV:  ()       => `${BASE}/reports/export/report-csv`,
  exportJSON:       ()       => `${BASE}/reports/export/json`,

  // Models
  compareModels:    (dev="ALL", h="24h") => http.get(`/models/compare?device_id=${dev}&horizon=${h}`),
  accuracyHistory:  ()       => http.get("/models/accuracy-history"),

  // Health
  health:           ()       => http.get("/health/"),
  healthDetailed:   ()       => http.get("/health/detailed"),
  metrics:          ()       => http.get("/health/metrics"),
}

export default api
