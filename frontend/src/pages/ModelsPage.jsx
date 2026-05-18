import React, { useEffect, useState } from "react"
import { Play } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import api from "../services/api.js"
import { Spinner, Alert, Select, ChartTooltip } from "../components/ui.jsx"

const MODEL_COLORS = { ARIMA:"#3b82f6", LinearRegression:"#22c55e", Ridge:"#22c55e" }

export default function ModelsPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/models"), [])
  const [horizon, setHorizon] = useState("24h")
  const [result,  setResult]  = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    api.accuracyHistory().then(r=>setHistory(r.data.records||[])).catch(()=>{})
  }, [])

  const run = async () => {
    setLoading(true); setError(null)
    try { setResult((await api.compareModels("ALL", horizon)).data) }
    catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const chartData = result?.results?.[0]?.forecast_points?.map((p,i)=>({
    ts: p.timestamp?.slice(11,16),
    ...Object.fromEntries(result.results.map(r=>([r.model_name, r.forecast_points[i]?.predicted_kwh?.toFixed(3)])))
  })) || []

  return (
    <div>
      <div className="card" style={{maxWidth:500,marginBottom:20}}>
        <div className="grid-2" style={{gap:14,alignItems:"end"}}>
          <Select label="Forecast Horizon" value={horizon} onChange={setHorizon}
            options={[{value:"24h",label:"24 Hours"},{value:"7d",label:"7 Days"}]}/>
          <button className="btn btn-primary" onClick={run} disabled={loading} style={{height:34}}>
            <Play size={13}/> {loading?"Comparing…":"Compare Models"}
          </button>
        </div>
      </div>

      {loading && <Spinner/>}
      {error   && <Alert type="error">{error}</Alert>}

      {result && (
        <>
          <div style={{marginBottom:16}}>
            <div className="alert alert-success">
              🏆 Best model for {horizon}: <strong>{result.best_model}</strong>
            </div>
          </div>

          {/* Accuracy table */}
          <div className="card" style={{marginBottom:16}}>
            <div className="card-title" style={{marginBottom:12}}>Accuracy Comparison</div>
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>Accuracy</th><th>Train Time</th></tr></thead>
                <tbody>
                  {result.results.map(r=>(
                    <tr key={r.model_name}>
                      <td><strong style={{color:MODEL_COLORS[r.model_name]||"var(--text)"}}>{r.model_name}</strong>{result.best_model===r.model_name&&<span style={{marginLeft:6,fontSize:11,background:"rgba(34,197,94,.15)",color:"var(--success)",padding:"1px 6px",borderRadius:4}}>BEST</span>}</td>
                      <td>{r.mae?.toFixed(4)}</td>
                      <td>{r.rmse?.toFixed(4)}</td>
                      <td style={{color:r.accuracy_pct>90?"var(--success)":r.accuracy_pct>75?"var(--warning)":"var(--danger)",fontWeight:600}}>{r.accuracy_pct?.toFixed(1)}%</td>
                      <td style={{color:"var(--text2)"}}>{r.training_time_ms}ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Overlay chart */}
          {chartData.length>0 && (
            <div className="card">
              <div className="card-title" style={{marginBottom:12}}>Forecast Overlay Comparison</div>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
                  <XAxis dataKey="ts" tick={{fill:"var(--text2)",fontSize:9}} interval="preserveStartEnd"/>
                  <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
                  <Tooltip content={<ChartTooltip/>}/>
                  <Legend wrapperStyle={{color:"var(--text2)",fontSize:12}}/>
                  {result.results.map(r=>(
                    <Line key={r.model_name} type="monotone" dataKey={r.model_name} stroke={MODEL_COLORS[r.model_name]||"#888"} strokeWidth={2} dot={false}/>
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* History */}
          {history.length>0 && (
            <div className="card" style={{marginTop:16}}>
              <div className="card-title" style={{marginBottom:12}}>Recent Accuracy Log</div>
              <div className="table-wrap">
                <table className="data-table">
                  <thead><tr><th>Model</th><th>Horizon</th><th>MAE</th><th>Accuracy</th><th>Recorded</th></tr></thead>
                  <tbody>
                    {history.slice(0,15).map((r,i)=>(
                      <tr key={i}>
                        <td style={{color:MODEL_COLORS[r.model_name]}}>{r.model_name}</td>
                        <td>{r.horizon}</td>
                        <td>{r.mae?.toFixed(4)}</td>
                        <td style={{color:r.accuracy_pct>90?"var(--success)":"var(--warning)",fontWeight:600}}>{r.accuracy_pct?.toFixed(1)}%</td>
                        <td style={{color:"var(--text2)",fontSize:12}}>{r.created_at?.slice(0,16).replace("T"," ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
