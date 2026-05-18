import React, { useEffect, useState } from "react"
import { Play, Calendar } from "lucide-react"
import { ComposedChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import api from "../services/api.js"
import { Spinner, Alert, KpiCard, ChartTooltip } from "../components/ui.jsx"

const SC_COLORS = { occupancy_change:"#6366f1", temperature_change:"#f59e0b", device_shutdown:"#22c55e", peak_reduction:"#3b82f6" }

export default function SimulationPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/simulation"), [])
  const [scenarios, setScenarios] = useState([])
  const [selected,  setSelected]  = useState(null)
  const [params,    setParams]    = useState({})
  const [result,    setResult]    = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState(null)

  useEffect(() => {
    api.scenarios().then(r=>{
      const sc = r.data.scenarios||[]
      setScenarios(sc)
      if (sc.length) { setSelected(sc[0]); const d={}; sc[0].parameters.forEach(p=>d[p.key]=p.default); setParams(d) }
    }).catch(()=>{})
  }, [])

  const pick = sc => {
    setSelected(sc); setResult(null)
    const d={}; sc.parameters.forEach(p=>d[p.key]=p.default); setParams(d)
  }

  const run = async () => {
    setLoading(true); setError(null)
    try { setResult((await api.runSimulation({ scenario:selected.key, parameters:params, device_id:"ALL" })).data) }
    catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const chartData = result?.hourly_profile?.slice(0,168).map(d=>({
    ts: d.timestamp?.slice(5,16), baseline:+d.baseline_kwh.toFixed(3), simulated:+d.simulated_kwh.toFixed(3),
  })) || []

  return (
    <div>
      <div className="grid-2" style={{marginBottom:20}}>
        {/* Scenario selector */}
        <div className="card">
          <div className="card-title" style={{marginBottom:14}}>Select Scenario</div>
          {scenarios.map(sc=>(
            <button key={sc.key} onClick={()=>pick(sc)} style={{
              width:"100%",padding:"12px 14px",borderRadius:8,textAlign:"left",cursor:"pointer",marginBottom:8,
              border:`1px solid ${selected?.key===sc.key?SC_COLORS[sc.key]:"var(--border)"}`,
              background: selected?.key===sc.key?`${SC_COLORS[sc.key]}12`:"var(--bg3)",
              color: selected?.key===sc.key?SC_COLORS[sc.key]:"var(--text)",
              transition:"all .15s", fontFamily:"inherit",
            }}>
              <div style={{fontWeight:600,fontSize:13}}>{sc.label}</div>
              <div style={{fontSize:12,color:"var(--text2)",marginTop:2}}>{sc.description}</div>
            </button>
          ))}
        </div>

        {/* Parameter controls */}
        <div className="card">
          <div className="card-title" style={{marginBottom:14}}>Configure: {selected?.label||"—"}</div>
          {selected?.parameters?.map(cfg=>{
            const unit = cfg.key.includes("fraction") ? "" : cfg.key.includes("pct") ? "%" : ""
            const val  = params[cfg.key] ?? cfg.default
            return (
            <div key={cfg.key} className="form-group" style={{marginBottom:16}}>
              <label>{cfg.label}: <strong style={{color:"var(--accent)"}}>{val}{unit}</strong></label>
              {cfg.min !== undefined ? (
                <input type="range" min={cfg.min} max={cfg.max} step={(cfg.max - cfg.min) / 40}
                  value={val} onChange={e => setParams({...params, [cfg.key]: +e.target.value})}/>
              ) : (
                <input type="number" value={val} onChange={e => setParams({...params, [cfg.key]: +e.target.value})}/>
              )}
            </div>
            )
          })}
          <button className="btn btn-primary" style={{width:"100%",marginTop:4}} onClick={run} disabled={loading||!selected}>
            <Play size={13}/> {loading?"Simulating…":"Run Simulation"}
          </button>
        </div>
      </div>

      {loading && <Spinner/>}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <>
          <div className="kpi-grid" style={{marginBottom:16}}>
            {[
              ["Baseline (7d)",   `${result.baseline_kwh} kWh`,           "var(--accent)"],
              ["Simulated",       `${result.simulated_kwh} kWh`,          "var(--success)"],
              ["Energy Saved",    `${result.energy_savings_kwh > 0?"-":""}${Math.abs(result.energy_savings_kwh)} kWh`, "var(--success)"],
              ["Cost Savings",    `$${result.cost_savings_usd?.toFixed(2)}`, "var(--warning)"],
            ].map(([l,v,c])=>(
              <div key={l} className="kpi-card"><div className="kpi-label">{l}</div><div className="kpi-value" style={{color:c,marginTop:4}}>{v}</div><div className="kpi-sub">{l==="Energy Saved"?`${result.savings_percent}% reduction`:""}</div></div>
            ))}
          </div>

          <div className="alert alert-info" style={{marginBottom:16}}>
            <Calendar size={14} style={{flexShrink:0}}/>
            <span><strong>Annualised:</strong> {result.annualized_savings_kwh?.toLocaleString()} kWh/year → <strong style={{color:"var(--success)"}}>${result.annualized_savings_usd?.toFixed(0)}/year</strong></span>
          </div>

          <div className="card" style={{marginBottom:16}}>
            <div className="card-title" style={{marginBottom:12}}>Savings Visualisation</div>
            <div style={{display:"flex",gap:8,alignItems:"center",marginBottom:8}}>
              <span style={{fontSize:12,color:"var(--text2)",width:80,flexShrink:0}}>Baseline</span>
              <div style={{flex:1,height:28,background:"var(--bg3)",borderRadius:6,overflow:"hidden",position:"relative"}}>
                <div style={{position:"absolute",inset:0,display:"flex"}}>
                  <div style={{width:`${100-result.savings_percent}%`,background:"#3b82f6",transition:"width .6s"}}/>
                  <div style={{flex:1,background:"var(--success)",display:"flex",alignItems:"center",paddingLeft:8,fontSize:12,color:"#fff",fontWeight:700}}>
                    -{result.savings_percent}%
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="card" style={{marginBottom:16}}>
            <div className="card-title" style={{marginBottom:12}}>Hourly Comparison (7 Days)</div>
            <ResponsiveContainer width="100%" height={260}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
                <XAxis dataKey="ts" tick={{fill:"var(--text2)",fontSize:9}} interval="preserveStartEnd"/>
                <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
                <Tooltip content={<ChartTooltip/>}/>
                <Legend wrapperStyle={{color:"var(--text2)",fontSize:12}}/>
                <Line type="monotone" dataKey="baseline"  stroke="#94a3b8" strokeWidth={1.5} dot={false} name="Baseline kWh" strokeDasharray="4 2"/>
                <Line type="monotone" dataKey="simulated" stroke="#22c55e" strokeWidth={2}   dot={false} name="Simulated kWh"/>
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-title" style={{marginBottom:10}}>🧠 Insights</div>
            <ul style={{paddingLeft:18}}>
              {result.insights?.map((ins,i)=><li key={i} style={{color:"var(--text2)",lineHeight:2.2,fontSize:13}}>{ins}</li>)}
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
