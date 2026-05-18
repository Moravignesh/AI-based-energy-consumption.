import React, { useEffect, useState } from "react"
import { Play } from "lucide-react"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import api from "../services/api.js"
import { Spinner, Alert, Select, Slider, Tabs, KpiCard, DataTable, ProgressBar, Badge } from "../components/ui.jsx"

const TYPE_COLOR = { consumption_spike:"#ef4444", sudden_drop:"#f59e0b", night_spike:"#8b5cf6", extreme_deviation:"#ec4899", statistical_anomaly:"#3b82f6" }
const TYPE_LABEL = { consumption_spike:"Consumption Spike", sudden_drop:"Sudden Drop", night_spike:"Night Spike", extreme_deviation:"Extreme Deviation", statistical_anomaly:"Statistical Anomaly" }

export default function AnomalyPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/anomaly"), [])
  const [form,   setForm]   = useState({ device_id:"ALL", method:"ensemble", sensitivity:0.05 })
  const [result, setResult] = useState(null)
  const [loading,setLoading]= useState(false)
  const [error,  setError]  = useState(null)
  const [tab,    setTab]    = useState("chart")

  const run = async () => {
    setLoading(true); setError(null)
    try { setResult((await api.runAnomaly(form)).data) }
    catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <div className="card" style={{maxWidth:700,marginBottom:20}}>
        <div className="grid-3" style={{gap:14,alignItems:"end"}}>
          <Select label="Device" value={form.device_id} onChange={v=>setForm({...form,device_id:v})}
            options={[{value:"ALL",label:"ALL Devices"}]}/>
          <Select label="Method" value={form.method} onChange={v=>setForm({...form,method:v})}
            options={[{value:"ensemble",label:"Ensemble (Recommended)"},{value:"isolation_forest",label:"Isolation Forest"},{value:"zscore",label:"Z-Score Statistical"}]}/>
          <Slider label="Sensitivity" value={form.sensitivity*100} onChange={v=>setForm({...form,sensitivity:v/100})}
            min={1} max={25} step={1} format={v=>`${v.toFixed(0)}%`}/>
        </div>
        <button className="btn btn-primary" style={{marginTop:14}} onClick={run} disabled={loading}>
          <Play size={13}/> {loading?"Detecting…":"Run Anomaly Detection"}
        </button>
      </div>

      {loading && <Spinner/>}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <>
          <div className="kpi-grid" style={{marginBottom:16}}>
            {[
              ["Total Records",   result.total_records?.toLocaleString(),                                "var(--text)"],
              ["Anomalies Found", result.anomaly_count,                                                  result.anomaly_count>0?"var(--danger)":"var(--success)"],
              ["Anomaly Rate",    `${result.anomaly_rate_pct}%`,                                         result.anomaly_rate_pct>5?"var(--danger)":"var(--success)"],
              ["Method",          result.method,                                                          "var(--accent)"],
            ].map(([l,v,c])=>(
              <div key={l} className="kpi-card"><div className="kpi-label">{l}</div><div className="kpi-value" style={{color:c,fontSize:20,marginTop:4}}>{v}</div></div>
            ))}
          </div>

          {Object.keys(result.anomaly_types||{}).length>0 && (
            <div className="card" style={{marginBottom:16}}>
              <div className="card-title" style={{marginBottom:12}}>Anomaly Types Breakdown</div>
              <div style={{display:"flex",flexWrap:"wrap",gap:10}}>
                {Object.entries(result.anomaly_types).map(([t,c])=>(
                  <div key={t} style={{background:`${TYPE_COLOR[t]||"#666"}12`,border:`1px solid ${TYPE_COLOR[t]||"#666"}30`,borderRadius:8,padding:"10px 14px"}}>
                    <div style={{fontWeight:600,color:TYPE_COLOR[t]||"#666",fontSize:13}}>{TYPE_LABEL[t]||t}</div>
                    <div style={{color:"var(--text2)",fontSize:12}}>{c} occurrences</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Tabs tabs={[{key:"chart",label:"Time Series"},{key:"list",label:`Anomalies (${result.anomaly_count})`},{key:"devices",label:"By Device"}]} active={tab} onChange={setTab}/>

          {tab==="chart" && (
            <div className="card">
              <div className="card-title" style={{marginBottom:12}}>Consumption with Anomalies Highlighted</div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={result.time_series?.map(d=>({...d,ts:d.timestamp?.slice(5,16)}))}>
                  <defs>
                    <linearGradient id="anomGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={.18}/><stop offset="100%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
                  <XAxis dataKey="ts" tick={{fill:"var(--text2)",fontSize:9}} interval="preserveStartEnd"/>
                  <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
                  <Tooltip content={({active,payload})=>{
                    if(!active||!payload?.length) return null
                    const d=payload[0]?.payload
                    return (
                      <div style={{background:"var(--bg2)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 14px",fontSize:12}}>
                        <div style={{color:"var(--text2)",marginBottom:4}}>{d.ts}</div>
                        <div style={{color:d.is_anomaly?"var(--danger)":"var(--accent)",fontWeight:600}}>{d.energy_kwh} kWh {d.is_anomaly?"⚠️ ANOMALY":""}</div>
                      </div>
                    )
                  }}/>
                  <Area type="monotone" dataKey="energy_kwh" stroke="#3b82f6" fill="url(#anomGrad)" strokeWidth={1.5} name="kWh"
                    dot={props=>{
                      const {cx,cy,payload}=props
                      if(!payload.is_anomaly) return null
                      return <circle key={`a${cx}${cy}`} cx={cx} cy={cy} r={4} fill="#ef4444" stroke="none" opacity={.85}/>
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>
              <div style={{display:"flex",gap:16,fontSize:12,color:"var(--text2)",marginTop:8}}>
                <span><span style={{color:"#3b82f6"}}>─</span> Normal</span>
                <span><span style={{color:"#ef4444"}}>●</span> Anomaly</span>
              </div>
            </div>
          )}

          {tab==="list" && (
            <div className="card">
              <DataTable maxRows={150}
                columns={[
                  {key:"timestamp",   label:"Timestamp",    style:{fontFamily:"monospace",fontSize:11}},
                  {key:"device_id",   label:"Device",       render:v=><Badge variant="info">{v}</Badge>},
                  {key:"energy_kwh",  label:"Energy kWh",   style:{color:"var(--danger)",fontWeight:600}},
                  {key:"anomaly_score",label:"Score",        render:v=>v?.toFixed(3)},
                  {key:"anomaly_type", label:"Type",         render:v=><span style={{fontSize:11,padding:"2px 7px",borderRadius:4,background:`${TYPE_COLOR[v]||"#666"}18`,color:TYPE_COLOR[v]||"#666"}}>{TYPE_LABEL[v]||v}</span>},
                ]}
                rows={result.anomalies}
              />
            </div>
          )}

          {tab==="devices" && (
            <div className="card">
              <DataTable
                columns={[
                  {key:"device_id",       label:"Device"},
                  {key:"total_readings",  label:"Total Readings", render:v=>v?.toLocaleString()},
                  {key:"anomaly_count",   label:"Anomalies",      style:{fontWeight:600},render:(v)=><span style={{color:v>0?"var(--danger)":"var(--success)"}}>{v}</span>},
                  {key:"anomaly_rate_pct",label:"Rate",            render:(v,row)=>(
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <ProgressBar value={v} max={20} color={v>5?"var(--danger)":"var(--success)"} height={5}/>
                      <span style={{fontSize:11,whiteSpace:"nowrap"}}>{v}%</span>
                    </div>
                  )},
                ]}
                rows={result.device_summary}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
