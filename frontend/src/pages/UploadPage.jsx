import React, { useState, useEffect } from "react"
import { Upload, Sparkles, CheckCircle, File } from "lucide-react"
import api from "../services/api.js"
import { Alert, Spinner } from "../components/ui.jsx"

export default function UploadPage({ onPathChange, onSuccess }) {
  useEffect(() => onPathChange?.("/upload"), [])
  const [loading, setLoading] = useState(false)
  const [result,  setResult]  = useState(null)
  const [error,   setError]   = useState(null)
  const [drag,    setDrag]    = useState(false)

  const handle = async (file) => {
    if (!file) return
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await api.uploadCSV(file)
      setResult(r.data); onSuccess?.()
    } catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const generate = async () => {
    setLoading(true); setError(null); setResult(null)
    try {
      const r = await api.generateSample()
      setResult(r.data); onSuccess?.()
    } catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <div className="grid-2" style={{ maxWidth: 860, gap: 20 }}>
        {/* CSV upload card */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 16 }}>📁 Upload CSV File</div>
          <div
            onDragOver={e => { e.preventDefault(); setDrag(true) }}
            onDragLeave={() => setDrag(false)}
            onDrop={e => { e.preventDefault(); setDrag(false); handle(e.dataTransfer.files[0]) }}
            onClick={() => document.getElementById("fi").click()}
            style={{
              border: `2px dashed ${drag ? "var(--accent)" : "var(--border)"}`,
              borderRadius: 10, padding: "36px 20px", textAlign: "center",
              cursor: "pointer", background: drag ? "rgba(59,130,246,.05)" : "var(--bg3)",
              transition: "all .15s", marginBottom: 16,
            }}
          >
            <Upload size={38} color="var(--text3)" style={{ margin: "0 auto 12px" }} />
            <p style={{ color: "var(--text2)", marginBottom: 4 }}>Drag & drop CSV here</p>
            <p style={{ color: "var(--text3)", fontSize: 12 }}>or click to browse</p>
          </div>
          <input id="fi" type="file" accept=".csv" style={{ display:"none" }}
            onChange={e => handle(e.target.files[0])} />
          <button className="btn btn-primary" style={{ width:"100%" }} disabled={loading}
            onClick={() => document.getElementById("fi").click()}>
            <File size={14} /> Select CSV File
          </button>
          <div style={{ marginTop:16, padding:12, background:"var(--bg3)", borderRadius:8, fontSize:12, color:"var(--text2)", lineHeight:1.8 }}>
            <strong style={{ color:"var(--text)" }}>Required:</strong> <code style={{color:"#93c5fd"}}>timestamp, energy_kwh</code><br/>
            <strong style={{ color:"var(--text)" }}>Optional:</strong> <code style={{color:"#93c5fd"}}>device_id, building_id, temperature, humidity, occupancy</code>
          </div>
        </div>

        {/* Generate sample card */}
        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>✨ Generate Sample Data</div>
          <p style={{ color:"var(--text2)", fontSize:13, lineHeight:1.7, marginBottom:16 }}>
            Generate 6 months of realistic synthetic energy data instantly — no CSV needed.
          </p>
          <ul style={{ color:"var(--text2)", paddingLeft:18, fontSize:13, lineHeight:2.2, marginBottom:20 }}>
            <li>5 devices across 2 buildings</li>
            <li>Hourly readings with seasonal patterns</li>
            <li>Business hours & weekend effects</li>
            <li>Temperature correlation for HVAC</li>
            <li>~2% injected anomalies</li>
          </ul>
          <button className="btn btn-success" style={{ width:"100%", padding:"12px" }} disabled={loading} onClick={generate}>
            <Sparkles size={14} /> {loading ? "Generating…" : "Generate 6-Month Sample Dataset"}
          </button>
        </div>
      </div>

      {loading && <Spinner style={{ marginTop:24 }} />}
      {error   && <Alert type="error" style={{ maxWidth:860, marginTop:16 }}>{error}</Alert>}

      {result && (
        <div className="card" style={{ maxWidth:860, marginTop:20 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, color:"var(--success)", marginBottom:16 }}>
            <CheckCircle size={18} /> <strong>Dataset loaded successfully!</strong>
          </div>
          <div className="grid-3" style={{ marginBottom:16 }}>
            {[
              ["Records",    result.records?.toLocaleString()],
              ["Devices",    result.devices?.length],
              ["Date Range", `${result.date_range?.start?.slice(0,10)} → ${result.date_range?.end?.slice(0,10)}`],
            ].map(([l,v]) => (
              <div key={l}><div className="kpi-label">{l}</div><div style={{fontWeight:700,fontSize:18,marginTop:4}}>{v}</div></div>
            ))}
          </div>
          <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
            {result.devices?.map(d => <span key={d} className="badge badge-info">{d}</span>)}
          </div>
          {result.warnings?.map((w,i) => <Alert key={i} type="warning" style={{marginTop:10}}>{w}</Alert>)}
        </div>
      )}
    </div>
  )
}
