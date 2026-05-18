import React, { useState, useEffect, createContext, useContext } from "react"
import { BrowserRouter, Routes, Route, NavLink, useNavigate } from "react-router-dom"
import {
  LayoutDashboard, TrendingUp, AlertTriangle, Lightbulb,
  FlaskConical, Upload, Monitor, Bell, FileText, GitCompare,
  Zap, ChevronLeft, ChevronRight, Activity, Settings
} from "lucide-react"
import api from "./services/api.js"

import DashboardPage    from "./pages/DashboardPage.jsx"
import ForecastPage     from "./pages/ForecastPage.jsx"
import AnomalyPage      from "./pages/AnomalyPage.jsx"
import OptimizationPage from "./pages/OptimizationPage.jsx"
import SimulationPage   from "./pages/SimulationPage.jsx"
import UploadPage       from "./pages/UploadPage.jsx"
import DevicesPage      from "./pages/DevicesPage.jsx"
import AlertsPage       from "./pages/AlertsPage.jsx"
import ReportsPage      from "./pages/ReportsPage.jsx"
import ModelsPage       from "./pages/ModelsPage.jsx"

/* ── App context ─────────────────────────────────────────────────────────── */
export const AppCtx = createContext({})
export const useApp = () => useContext(AppCtx)

const NAV_MAIN = [
  { to: "/",            label: "Dashboard",     icon: LayoutDashboard },
  { to: "/forecast",    label: "Forecast",      icon: TrendingUp },
  { to: "/anomaly",     label: "Anomaly",       icon: AlertTriangle },
  { to: "/optimization",label: "Optimization",  icon: Lightbulb },
  { to: "/simulation",  label: "Simulation",    icon: FlaskConical },
]
const NAV_DATA = [
  { to: "/devices",     label: "Devices",       icon: Monitor },
  { to: "/alerts",      label: "Alerts",        icon: Bell,        badge: true },
  { to: "/reports",     label: "Reports",       icon: FileText },
  { to: "/models",      label: "Model Compare", icon: GitCompare },
  { to: "/upload",      label: "Upload Data",   icon: Upload },
]

function Sidebar({ collapsed, onToggle, unreadAlerts }) {
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <Zap size={20} color="#f59e0b" className="logo-icon" />
        {!collapsed && <span>Energy AI</span>}
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {!collapsed && <div className="nav-label">Analytics</div>}
        {NAV_MAIN.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"}>
            {({ isActive }) => (
              <div className={`nav-link ${isActive ? "active" : ""}`}>
                <Icon size={16} className="nav-icon" />
                {!collapsed && <span>{label}</span>}
              </div>
            )}
          </NavLink>
        ))}

        {!collapsed && <div className="nav-label" style={{ marginTop: 16 }}>Management</div>}
        <div style={{ marginTop: collapsed ? 8 : 0 }}>
          {NAV_DATA.map(({ to, label, icon: Icon, badge }) => (
            <NavLink key={to} to={to}>
              {({ isActive }) => (
                <div className={`nav-link ${isActive ? "active" : ""}`}>
                  <Icon size={16} className="nav-icon" />
                  {!collapsed && <span style={{ flex: 1 }}>{label}</span>}
                  {badge && unreadAlerts > 0 && (
                    <span className="nav-badge">{unreadAlerts > 9 ? "9+" : unreadAlerts}</span>
                  )}
                </div>
              )}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <button className="sidebar-toggle" onClick={onToggle} title="Toggle sidebar">
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>
    </aside>
  )
}

function Topbar({ title, subtitle, dataLoaded, recordCount }) {
  return (
    <header className="topbar">
      <div style={{ flex: 1 }}>
        <div className="topbar-title">{title}</div>
        {subtitle && <div className="topbar-sub">{subtitle}</div>}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
          <div className="status-dot" style={{ background: dataLoaded ? "var(--success)" : "var(--text3)" }} />
          <span style={{ color: "var(--text2)" }}>
            {dataLoaded ? `${recordCount?.toLocaleString()} records` : "No data"}
          </span>
        </div>
        <div style={{ width: 1, height: 20, background: "var(--border)" }} />
        <span style={{ fontSize: 11, color: "var(--text3)" }}>v2.0</span>
      </div>
    </header>
  )
}

const PAGE_META = {
  "/":             { title: "Dashboard",          subtitle: "Real-time energy overview and KPIs" },
  "/forecast":     { title: "Energy Forecasting",  subtitle: "24h / 7d / 30d consumption predictions" },
  "/anomaly":      { title: "Anomaly Detection",   subtitle: "ML-powered abnormal pattern detection" },
  "/optimization": { title: "Optimization Engine", subtitle: "AI-generated energy-saving recommendations" },
  "/simulation":   { title: "Scenario Simulation", subtitle: "Model the impact of operational changes" },
  "/devices":      { title: "Device Management",   subtitle: "Per-device analytics and diagnostics" },
  "/alerts":       { title: "Alerts",              subtitle: "Platform alerts and peak notifications" },
  "/reports":      { title: "Reports & Export",    subtitle: "Download data, reports, and summaries" },
  "/models":       { title: "Model Comparison",    subtitle: "Benchmark ARIMA vs Linear Regression" },
  "/upload":       { title: "Upload Data",         subtitle: "Load your CSV or generate sample data" },
}

function Layout() {
  const [collapsed,    setCollapsed]    = useState(false)
  const [dataLoaded,   setDataLoaded]   = useState(false)
  const [recordCount,  setRecordCount]  = useState(0)
  const [unreadAlerts, setUnreadAlerts] = useState(0)
  const [currentPath,  setCurrentPath]  = useState("/")

  const refreshStatus = async () => {
    try {
      const [st, al] = await Promise.all([
        api.uploadStatus(), api.alertCounts(),
      ])
      setDataLoaded(st.data.loaded)
      setRecordCount(st.data.records || 0)
      setUnreadAlerts(al.data.unread || 0)
    } catch { /* backend may not be ready yet */ }
  }

  useEffect(() => {
    refreshStatus()
    const id = setInterval(refreshStatus, 30_000)
    return () => clearInterval(id)
  }, [])

  const meta = PAGE_META[currentPath] || { title: "Energy AI", subtitle: "" }

  return (
    <AppCtx.Provider value={{ dataLoaded, recordCount, unreadAlerts, refreshStatus }}>
      <div className="layout">
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} unreadAlerts={unreadAlerts} />
        <div className="main-content">
          <Topbar title={meta.title} subtitle={meta.subtitle} dataLoaded={dataLoaded} recordCount={recordCount} />

          {!dataLoaded && currentPath !== "/upload" && (
            <div style={{ margin: "12px 24px 0" }}>
              <div className="alert alert-warning">
                <AlertTriangle size={15} style={{ flexShrink: 0 }} />
                <span>
                  No dataset loaded.{" "}
                  <NavLink to="/upload" style={{ color: "var(--accent)", fontWeight: 600 }}>
                    Upload a CSV
                  </NavLink>{" "}
                  or generate sample data to use all features.
                </span>
              </div>
            </div>
          )}

          <div className="page-body">
            <Routes>
              <Route path="/"             element={<DashboardPage    onPathChange={setCurrentPath} />} />
              <Route path="/forecast"     element={<ForecastPage     onPathChange={setCurrentPath} />} />
              <Route path="/anomaly"      element={<AnomalyPage      onPathChange={setCurrentPath} />} />
              <Route path="/optimization" element={<OptimizationPage onPathChange={setCurrentPath} />} />
              <Route path="/simulation"   element={<SimulationPage   onPathChange={setCurrentPath} />} />
              <Route path="/devices"      element={<DevicesPage      onPathChange={setCurrentPath} />} />
              <Route path="/alerts"       element={<AlertsPage       onPathChange={setCurrentPath} />} />
              <Route path="/reports"      element={<ReportsPage      onPathChange={setCurrentPath} />} />
              <Route path="/models"       element={<ModelsPage       onPathChange={setCurrentPath} />} />
              <Route path="/upload"       element={<UploadPage       onPathChange={setCurrentPath} onSuccess={refreshStatus} />} />
            </Routes>
          </div>
        </div>
      </div>
    </AppCtx.Provider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}
