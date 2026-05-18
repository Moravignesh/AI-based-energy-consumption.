import React, { useEffect, useState } from "react"
import { Download, FileText, RefreshCw } from "lucide-react"
import api from "../services/api.js"
import { Spinner, Alert } from "../components/ui.jsx"

export default function ReportsPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/reports"), [])
  const [report,  setReport]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const load = async () => {
    setLoading(true); setError(null)
    try { setReport((await api.reportSummary()).data) }
    catch(e) { setError(e.message) }
    finally { setLoading(false) }
  }
  useEffect(()=>{ load() }, [])

  const download = (url, name) => { const a=document.createElement("a"); a.href=url; a.download=name; a.click() }

  return (
    <div>
      <div style={{display:"flex",gap:10,marginBottom:20,flexWrap:"wrap"}}>
        <button className="btn btn-secondary" onClick={load} disabled={loading}><RefreshCw size={13}/> Refresh</button>
        <button className="btn btn-primary" onClick={()=>download(api.exportCSV(),"energy_data.csv")}><Download size={13}/> Export Data CSV</button>
        <button className="btn btn-primary" onClick={()=>download(api.exportReportCSV(),"energy_report.csv")}><Download size={13}/> Export Report CSV</button>
        <button className="btn btn-secondary" onClick={()=>download(api.exportJSON(),"energy_report.json")}><Download size={13}/> Export JSON</button>
      </div>

      {loading && <Spinner/>}
      {error   && <Alert type="error">{error}</Alert>}

      {report && (
        <div className="grid-2" style={{gap:16}}>
          {/* Report metadata */}
          <div className="card">
            <div className="card-title" style={{marginBottom:14}}>Report Metadata</div>
            {[
              ["Generated At",   report.report_metadata?.generated_at?.slice(0,19).replace("T"," ")],
              ["Period Start",   report.report_metadata?.period_start?.slice(0,10)],
              ["Period End",     report.report_metadata?.period_end?.slice(0,10)],
              ["Data Days",      report.report_metadata?.data_days],
              ["Total Records",  report.report_metadata?.total_records?.toLocaleString()],
            ].map(([l,v])=>(
              <div key={l} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:"1px solid var(--border)",fontSize:13}}>
                <span style={{color:"var(--text2)"}}>{l}</span><strong>{v}</strong>
              </div>
            ))}
          </div>

          {/* Consumption */}
          <div className="card">
            <div className="card-title" style={{marginBottom:14}}>Consumption Summary</div>
            {Object.entries(report.consumption_summary||{}).map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:"1px solid var(--border)",fontSize:13}}>
                <span style={{color:"var(--text2)"}}>{k.replace(/_/g," ")}</span>
                <strong>{typeof v==="number"?v.toLocaleString():v}</strong>
              </div>
            ))}
          </div>

          {/* Cost */}
          <div className="card">
            <div className="card-title" style={{marginBottom:14}}>Cost Summary</div>
            {Object.entries(report.cost_summary||{}).map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:"1px solid var(--border)",fontSize:13}}>
                <span style={{color:"var(--text2)"}}>{k.replace(/_/g," ")}</span>
                <strong style={{color:k.includes("cost")?"var(--success)":undefined}}>{typeof v==="number"&&k!=="rate_usd_kwh"?`$${v.toLocaleString()}`:v}</strong>
              </div>
            ))}
          </div>

          {/* Optimization summary */}
          <div className="card">
            <div className="card-title" style={{marginBottom:14}}>Optimization Summary</div>
            {[
              ["Savings Potential kWh", report.optimization_summary?.savings_potential_kwh?.toFixed(0)+" kWh"],
              ["Savings Potential $",   "$"+report.optimization_summary?.savings_potential_usd?.toFixed(0)],
            ].map(([l,v])=>(
              <div key={l} style={{display:"flex",justifyContent:"space-between",padding:"7px 0",borderBottom:"1px solid var(--border)",fontSize:13}}>
                <span style={{color:"var(--text2)"}}>{l}</span><strong style={{color:"var(--success)"}}>{v}</strong>
              </div>
            ))}
            {report.optimization_summary?.top_recommendations?.length>0 && (
              <div style={{marginTop:10}}>
                <div style={{fontSize:12,color:"var(--text2)",marginBottom:6}}>Top Recommendations:</div>
                <ul style={{paddingLeft:16}}>
                  {report.optimization_summary.top_recommendations.map((r,i)=>(
                    <li key={i} style={{fontSize:12,color:"var(--text)",lineHeight:2}}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
