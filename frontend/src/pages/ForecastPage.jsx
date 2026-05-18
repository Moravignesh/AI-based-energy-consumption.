import React, { useEffect, useState } from "react"
import { Play, Download } from "lucide-react"
import { ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import api from "../services/api.js"
import { KpiCard, Alert, Spinner, Select, Tabs, ChartTooltip, DataTable } from "../components/ui.jsx"

const fmtTs = ts => ts ? ts.slice(5,16).replace("T"," ") : ""

export default function ForecastPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/forecast"), [])
  const [devices, setDevices]   = useState(["ALL"])
  const [form,    setForm]      = useState({ device_id:"ALL", horizon:"24h", model:"auto" })
  const [result,  setResult]    = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error,   setError]     = useState(null)
  const [tab,     setTab]       = useState("chart")

  useEffect(() => { api.forecastDevices().then(r=>setDevices(r.data.devices||["ALL"])).catch(()=>{}) }, [])

  const run = async () => {
    setLoading(true); setError(null)
    try { setResult((await api.runForecast(form)).data) }
    catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const chartData = result?.forecast?.slice(0,168).map(p=>({
    ts: fmtTs(p.timestamp),
    predicted: +p.predicted_kwh?.toFixed(3),
    lower: +p.lower_bound?.toFixed(3),
    upper: +p.upper_bound?.toFixed(3),
  })) || []

  return (
    <div>
      {/* Controls */}
      <div className="card" style={{maxWidth:700,marginBottom:20}}>
        <div className="grid-3" style={{gap:14,alignItems:"end"}}>
          <Select label="Device / Meter" value={form.device_id} onChange={v=>setForm({...form,device_id:v})}
            options={devices.map(d=>({value:d,label:d}))} />
          <Select label="Horizon" value={form.horizon} onChange={v=>setForm({...form,horizon:v})}
            options={[{value:"24h",label:"Next 24 Hours"},{value:"7d",label:"Next 7 Days"},{value:"30d",label:"Next 30 Days"}]}/>
          <Select label="Model" value={form.model} onChange={v=>setForm({...form,model:v})}
            options={[{value:"auto",label:"Auto (Best)"},{value:"arima",label:"ARIMA"},{value:"linear",label:"Linear Regression"}]}/>
        </div>
        <button className="btn btn-primary" style={{marginTop:14}} onClick={run} disabled={loading}>
          <Play size={13}/> {loading?"Forecasting…":"Run Forecast"}
        </button>
      </div>

      {loading && <Spinner/>}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <>
          {/* Metrics */}
          <div className="kpi-grid" style={{marginBottom:16}}>
            {[
              ["Model",          result.model_used,                       "var(--accent2)"],
              ["Horizon",        result.horizon,                          "var(--accent)"],
              ["Total Predicted",`${result.total_predicted_kwh} kWh`,    "var(--success)"],
              ["Accuracy",       result.accuracy_pct!=null?`${result.accuracy_pct.toFixed(1)}%`:"N/A", "var(--warning)"],
            ].map(([l,v,c])=>(
              <div key={l} className="kpi-card">
                <div className="kpi-label">{l}</div>
                <div className="kpi-value" style={{color:c,fontSize:20,marginTop:4}}>{v}</div>
              </div>
            ))}
          </div>

          {/* Peak alerts */}
          {result.peak_predictions?.map((p,i)=>(
            <div key={i} style={{padding:"10px 16px",marginBottom:8,background:"rgba(245,158,11,.08)",border:"1px solid rgba(245,158,11,.25)",borderRadius:8,fontSize:13,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
              <span>⚡ {p.alert_message}</span>
              <span className={`badge badge-${p.severity==="high"?"high":"medium"}`}>{p.severity}</span>
            </div>
          ))}

          {/* Tabs */}
          <Tabs tabs={[{key:"chart",label:"Forecast Chart"},{key:"table",label:"Data Table"}]} active={tab} onChange={setTab}/>

          {tab==="chart" && (
            <div className="card">
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData}>
                  <defs>
                    <linearGradient id="ci" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={.12}/>
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
                  <XAxis dataKey="ts" tick={{fill:"var(--text2)",fontSize:9}} interval="preserveStartEnd"/>
                  <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
                  <Tooltip content={<ChartTooltip/>}/>
                  <Legend wrapperStyle={{color:"var(--text2)",fontSize:12}}/>
                  <Area type="monotone" dataKey="upper" fill="url(#ci)" stroke="transparent" legendType="none"/>
                  <Area type="monotone" dataKey="lower" fill="var(--bg)" stroke="transparent" legendType="none"/>
                  <Line type="monotone" dataKey="predicted" stroke="#3b82f6" strokeWidth={2.5} dot={false} name="Predicted kWh"/>
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}

          {tab==="table" && (
            <div className="card">
              <DataTable
                columns={[
                  {key:"timestamp",  label:"Timestamp",      style:{fontFamily:"monospace",fontSize:12}},
                  {key:"predicted_kwh",label:"Predicted kWh",style:{fontWeight:600}},
                  {key:"lower_bound",  label:"Lower Bound",  style:{color:"var(--text2)"}},
                  {key:"upper_bound",  label:"Upper Bound",  style:{color:"var(--text2)"}},
                ]}
                rows={result.forecast}
                maxRows={200}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}
