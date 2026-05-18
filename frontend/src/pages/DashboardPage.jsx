import React, { useEffect, useState } from "react"
import { Zap, DollarSign, AlertTriangle, TrendingDown, BarChart2, Clock, Monitor, RefreshCw } from "lucide-react"
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts"
import api from "../services/api.js"
import { KpiCard, Spinner, Alert, ChartTooltip, SectionHeader } from "../components/ui.jsx"

const COLORS = ["#3b82f6","#6366f1","#22c55e","#f59e0b","#ef4444","#8b5cf6","#ec4899"]
const fmtTs  = ts => { if (!ts) return ""; const d = new Date(ts); return `${d.getMonth()+1}/${d.getDate()} ${String(d.getHours()).padStart(2,"0")}h` }

export default function DashboardPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/"), [])
  const [sum,  setSum]  = useState(null)
  const [hist, setHist] = useState([])
  const [devs, setDevs] = useState([])
  const [hourly, setHourly] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const [s,h,d,p] = await Promise.all([
        api.dashboardSummary(), api.historical("ALL","hourly",400),
        api.deviceBreakdown(), api.hourlyPattern(),
      ])
      setSum(s.data); setHist(h.data.data||[]); setDevs(d.data.devices||[]); setHourly(p.data.pattern||[])
    } catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  if (loading) return <Spinner />
  if (error)   return <Alert type="error">{error}</Alert>
  if (!sum)    return null

  const tc = sum.consumption_trend === "increasing" ? "var(--danger)" : sum.consumption_trend === "decreasing" ? "var(--success)" : "var(--text2)"

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"flex-end", marginBottom:16 }}>
        <button className="btn btn-secondary btn-sm" onClick={load}><RefreshCw size={13}/> Refresh</button>
      </div>

      {/* KPIs row 1 */}
      <div className="kpi-grid" style={{ marginBottom:14 }}>
        <KpiCard label="Total Consumption"    value={`${(sum.total_consumption_kwh/1000).toFixed(1)} MWh`} icon={Zap}           color="var(--warning)"  sub={`${sum.data_days} days`}       trend={sum.trend_pct} />
        <KpiCard label="Monthly Cost Est."    value={`$${sum.estimated_monthly_cost_usd?.toFixed(0)}`}     icon={DollarSign}     color="var(--success)"  sub="@ $0.12/kWh" />
        <KpiCard label="Anomalies Detected"   value={sum.anomaly_count}                                    icon={AlertTriangle}  color="var(--danger)"   sub="Run detection for details" />
        <KpiCard label="Savings Potential"    value={`${sum.savings_potential_pct}%`}                      icon={TrendingDown}   color="var(--accent2)"  sub="via optimization" />
      </div>

      {/* KPIs row 2 */}
      <div className="kpi-grid" style={{ marginBottom:20 }}>
        <KpiCard label="Avg Daily Usage"  value={`${sum.avg_daily_kwh?.toFixed(0)} kWh`}  icon={BarChart2} color="var(--accent)" />
        <KpiCard label="Peak Hour"        value={`${sum.peak_hour}:00`}                   icon={Clock}     color="var(--warning)" sub={`${sum.peak_kwh?.toFixed(2)} kWh avg`} />
        <KpiCard label="Active Devices"   value={sum.active_devices}                      icon={Monitor}   color="var(--accent2)" sub={`${sum.active_buildings} building(s)`} />
        <KpiCard label="Next 24h Forecast" value={`${sum.forecast_next_24h_kwh?.toFixed(0)} kWh`} icon={TrendingDown} color="var(--success)" />
      </div>

      {/* Trend pill */}
      <div style={{ marginBottom:20 }}>
        <span style={{ background:"var(--bg3)", border:"1px solid var(--border)", padding:"5px 14px", borderRadius:999, fontSize:12 }}>
          Trend: <strong style={{ color:tc }}>{sum.consumption_trend?.toUpperCase()}</strong>
          {sum.trend_pct !== 0 && <span style={{ color:"var(--text2)", marginLeft:6 }}>({sum.trend_pct > 0?"+":""}{sum.trend_pct}% vs last week)</span>}
        </span>
      </div>

      {/* Historical chart */}
      <div className="card" style={{ marginBottom:16 }}>
        <SectionHeader title="Historical Consumption" />
        <ResponsiveContainer width="100%" height={230}>
          <AreaChart data={hist.map(d=>({...d, ts:fmtTs(d.timestamp)}))}>
            <defs>
              <linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity={.25}/>
                <stop offset="100%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
            <XAxis dataKey="ts" tick={{fill:"var(--text2)",fontSize:10}} interval="preserveStartEnd"/>
            <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
            <Tooltip content={<ChartTooltip/>}/>
            <Area type="monotone" dataKey="energy_kwh" stroke="#3b82f6" fill="url(#ga)" strokeWidth={2} dot={false} name="kWh"/>
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid-2">
        {/* Device breakdown */}
        <div className="card">
          <div className="card-title" style={{marginBottom:16}}>Device Breakdown</div>
          {devs.map((d,i)=>(
            <div key={d.device_id} style={{marginBottom:12}}>
              <div style={{display:"flex",justifyContent:"space-between",fontSize:12,marginBottom:4}}>
                <span>{d.device_id}</span>
                <span style={{color:"var(--text2)"}}>{d.share_pct}%  ·  {d.total_kwh?.toFixed(0)} kWh</span>
              </div>
              <div className="progress-bar"><div className="progress-fill" style={{width:`${d.share_pct}%`,background:COLORS[i%COLORS.length]}}/></div>
            </div>
          ))}
        </div>

        {/* Hourly pattern */}
        <div className="card">
          <div className="card-title" style={{marginBottom:14}}>Average Hourly Pattern</div>
          <ResponsiveContainer width="100%" height={190}>
            <BarChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
              <XAxis dataKey="hour" tick={{fill:"var(--text2)",fontSize:10}} tickFormatter={h=>`${h}h`}/>
              <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
              <Tooltip content={<ChartTooltip/>}/>
              <Bar dataKey="avg_kwh" fill="#6366f1" name="Avg kWh" radius={[2,2,0,0]}/>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
