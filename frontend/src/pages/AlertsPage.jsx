import React, { useEffect, useState } from "react"
import { Bell, CheckCircle, Trash2, CheckCheck } from "lucide-react"
import api from "../services/api.js"
import { Spinner, Alert, Badge, DataTable } from "../components/ui.jsx"
import { useApp } from "../App.jsx"

const SEV_VAR = { low:"low", medium:"medium", high:"high", critical:"high" }

export default function AlertsPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/alerts"), [])
  const { refreshStatus } = useApp()
  const [alerts,  setAlerts]  = useState([])
  const [counts,  setCounts]  = useState({})
  const [loading, setLoading] = useState(true)
  const [filter,  setFilter]  = useState({})

  const load = async () => {
    setLoading(true)
    try {
      const [a, c] = await Promise.all([api.listAlerts(filter), api.alertCounts()])
      setAlerts(a.data.alerts||[]); setCounts(c.data)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filter])

  const markRead  = async id => { await api.markRead(id); load(); refreshStatus?.() }
  const resolve   = async id => { await api.resolveAlert(id); load(); refreshStatus?.() }
  const del       = async id => { await api.deleteAlert(id); load(); refreshStatus?.() }
  const markAll   = async ()  => { await api.markAllRead(); load(); refreshStatus?.() }

  return (
    <div>
      {/* Summary */}
      <div className="kpi-grid" style={{marginBottom:16}}>
        {[
          ["Total Alerts",    counts.total||0,     "var(--text)"],
          ["Unread",          counts.unread||0,    "var(--warning)"],
          ["Unresolved",      counts.unresolved||0,"var(--danger)"],
          ["High Priority",   counts.by_severity?.high||0, "var(--danger)"],
        ].map(([l,v,c])=>(
          <div key={l} className="kpi-card"><div className="kpi-label">{l}</div><div className="kpi-value" style={{color:c,marginTop:4}}>{v}</div></div>
        ))}
      </div>

      {/* Actions */}
      <div style={{display:"flex",gap:8,marginBottom:16,flexWrap:"wrap"}}>
        <button className="btn btn-secondary btn-sm" onClick={markAll}><CheckCheck size={13}/> Mark All Read</button>
        {["low","medium","high","critical"].map(s=>(
          <button key={s} className={`btn btn-sm ${filter.severity===s?"btn-primary":"btn-secondary"}`}
            onClick={()=>setFilter(f=>f.severity===s?{}:{...f,severity:s})}>
            {s.charAt(0).toUpperCase()+s.slice(1)}
          </button>
        ))}
        <button className="btn btn-secondary btn-sm" onClick={()=>setFilter({is_read:false})}>Unread Only</button>
        <button className="btn btn-secondary btn-sm" onClick={()=>setFilter({})}>Clear Filter</button>
      </div>

      {loading ? <Spinner/> : (
        <div className="card">
          {alerts.length===0 ? (
            <div style={{textAlign:"center",padding:"40px",color:"var(--text2)"}}>
              <Bell size={32} style={{margin:"0 auto 12px",opacity:.3}}/>
              <div>No alerts match this filter.</div>
            </div>
          ) : (
            alerts.map(a=>(
              <div key={a.id} style={{
                padding:"14px 16px", marginBottom:8, borderRadius:8,
                background: a.is_read?"var(--bg3)":"rgba(59,130,246,.06)",
                border:`1px solid ${a.is_read?"var(--border)":"rgba(59,130,246,.2)"}`,
              }}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:12}}>
                  <div style={{flex:1}}>
                    <div style={{display:"flex",gap:6,marginBottom:6,flexWrap:"wrap"}}>
                      <Badge variant={SEV_VAR[a.severity]||"info"}>{a.severity.toUpperCase()}</Badge>
                      <Badge variant="info">{a.alert_type}</Badge>
                      {a.device_id && <Badge variant="purple">{a.device_id}</Badge>}
                      {!a.is_read && <span style={{fontSize:10,background:"var(--accent)",color:"#fff",padding:"1px 6px",borderRadius:999,fontWeight:700}}>NEW</span>}
                    </div>
                    <div style={{fontWeight:600,fontSize:13,marginBottom:4}}>{a.title}</div>
                    <div style={{fontSize:12,color:"var(--text2)",lineHeight:1.6}}>{a.message}</div>
                    <div style={{fontSize:11,color:"var(--text3)",marginTop:6}}>{a.created_at?.slice(0,16).replace("T"," ")}</div>
                  </div>
                  <div style={{display:"flex",gap:6,flexShrink:0}}>
                    {!a.is_read   && <button className="btn btn-ghost btn-icon btn-sm" title="Mark read" onClick={()=>markRead(a.id)}><CheckCircle size={14}/></button>}
                    {!a.is_resolved && <button className="btn btn-ghost btn-icon btn-sm" title="Resolve" onClick={()=>resolve(a.id)}><CheckCheck size={14}/></button>}
                    <button className="btn btn-ghost btn-icon btn-sm" title="Delete" onClick={()=>del(a.id)} style={{color:"var(--danger)"}}><Trash2 size={14}/></button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
