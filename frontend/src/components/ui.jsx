import React from "react"
import { AlertCircle, CheckCircle, Info, AlertTriangle, TrendingUp, TrendingDown, Minus } from "lucide-react"

/* ── Spinner ─────────────────────────────────────────────────────────────── */
export function Spinner({ size = 32, style = {} }) {
  return <div className="spinner" style={{ width: size, height: size, ...style }} />
}

/* ── Alert banners ───────────────────────────────────────────────────────── */
const ALERT_ICON = { error: AlertCircle, success: CheckCircle, info: Info, warning: AlertTriangle }
export function Alert({ type = "info", children, style = {} }) {
  const Icon = ALERT_ICON[type] || Info
  return (
    <div className={`alert alert-${type}`} style={style}>
      <Icon size={15} style={{ flexShrink: 0, marginTop: 1 }} />
      <span>{children}</span>
    </div>
  )
}

/* ── KPI Card ────────────────────────────────────────────────────────────── */
export function KpiCard({ label, value, sub, icon: Icon, color = "var(--accent)", trend, style = {} }) {
  const trendPos = typeof trend === "number" && trend > 0
  const trendNeg = typeof trend === "number" && trend < 0
  const TrendIcon = trendPos ? TrendingUp : trendNeg ? TrendingDown : Minus
  const trendColor = trendPos ? "var(--danger)" : trendNeg ? "var(--success)" : "var(--text3)"

  return (
    <div className="kpi-card" style={style}>
      <div className="kpi-row">
        <span className="kpi-label">{label}</span>
        {Icon && (
          <div className="kpi-icon-wrap" style={{ background: `${color}18` }}>
            <Icon size={15} color={color} />
          </div>
        )}
      </div>
      <div className="kpi-value" style={{ color }}>{value}</div>
      {sub && <div className="kpi-sub">{sub}</div>}
      {typeof trend === "number" && (
        <div className="kpi-trend" style={{ color: trendColor }}>
          <TrendIcon size={11} />
          <span>{Math.abs(trend).toFixed(1)}% vs last week</span>
        </div>
      )}
    </div>
  )
}

/* ── Section header ──────────────────────────────────────────────────────── */
export function SectionHeader({ title, subtitle, children }) {
  return (
    <div className="card-header">
      <div>
        <div className="card-title">{title}</div>
        {subtitle && <div className="card-subtitle">{subtitle}</div>}
      </div>
      {children && <div style={{ display: "flex", gap: 8 }}>{children}</div>}
    </div>
  )
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
export function Tabs({ tabs, active, onChange }) {
  return (
    <div className="tabs">
      {tabs.map(t => (
        <button key={t.key} className={`tab ${active === t.key ? "active" : ""}`}
          onClick={() => onChange(t.key)}>
          {t.label}
        </button>
      ))}
    </div>
  )
}

/* ── Badge ───────────────────────────────────────────────────────────────── */
export function Badge({ children, variant = "info" }) {
  return <span className={`badge badge-${variant}`}>{children}</span>
}

/* ── Progress bar ────────────────────────────────────────────────────────── */
export function ProgressBar({ value, max = 100, color = "var(--accent)", height = 6 }) {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div className="progress-bar" style={{ height }}>
      <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

/* ── Empty state ─────────────────────────────────────────────────────────── */
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div style={{ textAlign: "center", padding: "48px 24px", color: "var(--text2)" }}>
      {Icon && <Icon size={40} style={{ margin: "0 auto 16px", opacity: .4 }} />}
      <div style={{ fontWeight: 600, fontSize: 15, color: "var(--text)", marginBottom: 6 }}>{title}</div>
      {description && <div style={{ fontSize: 13, marginBottom: 16 }}>{description}</div>}
      {action}
    </div>
  )
}

/* ── Tooltip wrapper for recharts ────────────────────────────────────────── */
export function ChartTooltip({ active, payload, label, unit = "kWh" }) {
  if (!active || !payload?.length) return null
  return (
    <div className="custom-tooltip" style={{ padding: "10px 14px", minWidth: 140 }}>
      <div style={{ color: "var(--text2)", fontSize: 11, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", gap: 12, color: p.color, fontSize: 12 }}>
          <span>{p.name}</span>
          <strong>{typeof p.value === "number" ? p.value.toFixed(3) : p.value} {unit}</strong>
        </div>
      ))}
    </div>
  )
}

/* ── Data table ──────────────────────────────────────────────────────────── */
export function DataTable({ columns, rows, maxRows = 100 }) {
  if (!rows?.length) return <div style={{ color: "var(--text2)", padding: 16, fontSize: 13 }}>No data to display.</div>
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, maxRows).map((row, i) => (
            <tr key={i}>
              {columns.map(c => (
                <td key={c.key} style={c.style}>
                  {c.render ? c.render(row[c.key], row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ── Select dropdown ─────────────────────────────────────────────────────── */
export function Select({ label: lbl, value, onChange, options, style = {} }) {
  return (
    <div className="form-group" style={style}>
      {lbl && <label>{lbl}</label>}
      <select value={value} onChange={e => onChange(e.target.value)}>
        {options.map(o => (
          <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
        ))}
      </select>
    </div>
  )
}

/* ── Slider input ────────────────────────────────────────────────────────── */
export function Slider({ label: lbl, value, onChange, min, max, step, format }) {
  return (
    <div className="form-group">
      <label>{lbl}: <strong style={{ color: "var(--accent)" }}>{format ? format(value) : value}</strong></label>
      <input type="range" min={min} max={max} step={step ?? (max - min) / 40}
        value={value} onChange={e => onChange(+e.target.value)} />
    </div>
  )
}
