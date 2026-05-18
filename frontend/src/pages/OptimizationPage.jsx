import React, { useEffect, useState } from "react"
import { Play, ChevronDown, ChevronRight } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"
import api from "../services/api.js"
import { Spinner, Alert, KpiCard, SectionHeader, Badge, ChartTooltip } from "../components/ui.jsx"

const PRI_COLOR = { high:"var(--danger)", medium:"var(--warning)", low:"var(--success)" }
const CAT_ICON  = { "Load Balancing":"⚖️","Scheduling":"📅","Device Optimisation":"🔧","HVAC":"❄️","Fault Detection":"⚠️","Sustainability":"🌱","Lighting":"💡" }
const COLORS    = ["#22c55e","#3b82f6","#f59e0b","#8b5cf6","#ef4444","#ec4899","#06b6d4"]

function RecCard({ rec }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rec-card" style={{ borderLeft:`3px solid ${PRI_COLOR[rec.priority]||"var(--border)"}` }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12 }}>
        <div style={{ flex:1 }}>
          <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginBottom:8 }}>
            <span style={{ fontSize:15 }}>{CAT_ICON[rec.category]||"💡"}</span>
            <Badge variant={rec.priority}>{rec.priority.toUpperCase()}</Badge>
            <Badge variant="info">{rec.category}</Badge>
            {rec.device_id && <Badge variant="purple">{rec.device_id}</Badge>}
          </div>
          <div style={{ fontWeight:600, fontSize:13, marginBottom: open?8:0 }}>{rec.title}</div>
          {open && <div style={{ color:"var(--text2)", fontSize:12, lineHeight:1.7 }}>{rec.description}</div>}
        </div>
        <div style={{ textAlign:"right", flexShrink:0 }}>
          <div style={{ color:"var(--success)", fontWeight:700, fontSize:17 }}>{rec.estimated_savings_kwh?.toFixed(0)} kWh</div>
          <div style={{ color:"var(--text2)", fontSize:11 }}>${rec.estimated_cost_savings_usd?.toFixed(0)} saved</div>
        </div>
      </div>
      <button onClick={()=>setOpen(o=>!o)} style={{ background:"none",border:"none",color:"var(--accent)",cursor:"pointer",fontSize:12,padding:"4px 0",display:"flex",alignItems:"center",gap:4,marginTop:6 }}>
        {open?<ChevronDown size={12}/>:<ChevronRight size={12}/>} {open?"Less":"More details"}
      </button>
    </div>
  )
}

export default function OptimizationPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/optimization"), [])
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)
  const [filter,  setFilter]  = useState("all")

  const run = async () => {
    setLoading(true); setError(null)
    try { setResult((await api.recommendations()).data) }
    catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }
  useEffect(() => { run() }, [])

  const filtered = result?.recommendations?.filter(r => filter==="all" || r.priority===filter) || []
  const chartData = result?.recommendations?.map(r=>({ name:r.category, savings:+r.estimated_savings_kwh.toFixed(0) })) || []

  return (
    <div>
      <div style={{ display:"flex", gap:10, marginBottom:20, flexWrap:"wrap" }}>
        <button className="btn btn-primary" onClick={run} disabled={loading}><Play size={13}/> {loading?"Analysing…":"Refresh Recommendations"}</button>
      </div>

      {loading && <Spinner/>}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <>
          <div className="kpi-grid" style={{ marginBottom:16 }}>
            {[
              ["Total Savings Potential", `${result.total_potential_savings_kwh?.toFixed(0)} kWh`, "var(--success)"],
              ["Cost Savings",            `$${result.total_potential_savings_usd?.toFixed(0)}`,    "var(--accent)"],
              ["Reduction Potential",     `${result.savings_potential_pct?.toFixed(1)}%`,          "var(--warning)"],
              ["Recommendations",         result.recommendations?.length,                           "var(--accent2)"],
            ].map(([l,v,c])=>(
              <div key={l} className="kpi-card"><div className="kpi-label">{l}</div><div className="kpi-value" style={{color:c,marginTop:4}}>{v}</div></div>
            ))}
          </div>

          {result.alerts?.map((a,i)=>(
            <div key={i} className={`alert alert-${a.severity==="high"?"error":"warning"}`} style={{marginBottom:10}}>⚡ {a.message}</div>
          ))}

          <div className="grid-2" style={{ marginBottom:16 }}>
            {/* Savings chart */}
            <div className="card">
              <div className="card-title" style={{marginBottom:12}}>Savings by Category (kWh)</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false}/>
                  <XAxis type="number" tick={{fill:"var(--text2)",fontSize:10}}/>
                  <YAxis type="category" dataKey="name" tick={{fill:"var(--text2)",fontSize:10}} width={130}/>
                  <Tooltip content={<ChartTooltip unit="kWh"/>}/>
                  <Bar dataKey="savings" name="kWh Savings" radius={[0,4,4,0]}>
                    {chartData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Peak analysis */}
            {result.peak_analysis && (
              <div className="card">
                <div className="card-title" style={{marginBottom:12}}>Peak Load Analysis</div>
                {[
                  ["Peak Hour",     `${result.peak_analysis.peak_hour}:00`, "var(--danger)"],
                  ["Off-Peak Hour", `${result.peak_analysis.off_peak_hour}:00`, "var(--success)"],
                  ["Load Factor",   result.peak_analysis.load_factor?.toFixed(3), result.peak_analysis.load_factor<0.6?"var(--danger)":"var(--success)"],
                  ["Peak kWh",      `${result.peak_analysis.peak_kwh?.toFixed(2)} kWh`, "var(--warning)"],
                ].map(([l,v,c])=>(
                  <div key={l} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px solid var(--border)",fontSize:13}}>
                    <span style={{color:"var(--text2)"}}>{l}</span>
                    <strong style={{color:c}}>{v}</strong>
                  </div>
                ))}
                <div style={{marginTop:10,fontSize:12,color:"var(--text2)"}}>
                  Peak hours: {result.peak_analysis.peak_hours?.map(h=>`${h}:00`).join(", ")}
                </div>
              </div>
            )}
          </div>

          {/* Recommendation list */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Recommendations ({filtered.length})</div>
              <div style={{display:"flex",gap:6}}>
                {["all","high","medium","low"].map(p=>(
                  <button key={p} className={`btn btn-sm ${filter===p?"btn-primary":"btn-secondary"}`} onClick={()=>setFilter(p)}>
                    {p==="all"?"All":p.charAt(0).toUpperCase()+p.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            {filtered.map((r,i)=><RecCard key={i} rec={r}/>)}
          </div>
        </>
      )}
    </div>
  )
}
