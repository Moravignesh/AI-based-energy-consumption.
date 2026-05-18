import React, { useEffect, useState } from "react"
import { Monitor } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import api from "../services/api.js"
import { Spinner, Alert, DataTable, Badge, KpiCard, ChartTooltip } from "../components/ui.jsx"

export default function DevicesPage({ onPathChange }) {
  useEffect(() => onPathChange?.("/devices"), [])
  const [devices, setDevices] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.listDevices().then(r=>{ setDevices(r.data.devices||[]); setLoading(false) }).catch(e=>{ setError(e.message); setLoading(false) })
  }, [])

  const loadDetail = async (id) => {
    setSelected(id); setDetail(null)
    try { setDetail((await api.deviceDetail(id)).data) } catch {}
  }

  if (loading) return <Spinner/>
  if (error)   return <Alert type="error">{error}</Alert>

  return (
    <div className="grid-2" style={{gap:20,alignItems:"start"}}>
      <div className="card">
        <div className="card-title" style={{marginBottom:14}}><Monitor size={14} style={{display:"inline",marginRight:6}}/>All Devices ({devices.length})</div>
        <DataTable
          columns={[
            {key:"device_id",   label:"Device",      render:v=><strong>{v}</strong>},
            {key:"building_id", label:"Building",    render:v=><Badge variant="info">{v||"—"}</Badge>},
            {key:"total_kwh",   label:"Total kWh",   render:v=>v?.toFixed(0)},
            {key:"share_pct",   label:"Share",       render:v=>`${v}%`},
            {key:"cost_usd",    label:"Cost ($)",    render:v=>`$${v?.toFixed(0)}`},
          ]}
          rows={devices}
        />
        <div style={{marginTop:12,display:"flex",flexWrap:"wrap",gap:6}}>
          {devices.map(d=>(
            <button key={d.device_id} className={`btn btn-sm ${selected===d.device_id?"btn-primary":"btn-secondary"}`} onClick={()=>loadDetail(d.device_id)}>
              {d.device_id}
            </button>
          ))}
        </div>
      </div>

      {selected && (
        <div>
          {!detail ? <Spinner/> : (
            <>
              <div className="card" style={{marginBottom:14}}>
                <div className="card-title" style={{marginBottom:14}}>{detail.device_id} — Stats</div>
                <div className="grid-2" style={{gap:10}}>
                  {[
                    ["Total kWh",   detail.stats?.total_kwh?.toFixed(0)],
                    ["Avg Daily",   `${detail.stats?.avg_daily_kwh?.toFixed(1)} kWh`],
                    ["Cost",        `$${detail.stats?.cost_usd?.toFixed(0)}`],
                    ["Readings",    detail.stats?.reading_count?.toLocaleString()],
                  ].map(([l,v])=>(
                    <div key={l} style={{background:"var(--bg3)",borderRadius:8,padding:"10px 12px"}}>
                      <div style={{fontSize:11,color:"var(--text2)"}}>{l}</div>
                      <div style={{fontWeight:700,fontSize:16,marginTop:2}}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="card">
                <div className="card-title" style={{marginBottom:12}}>Hourly Pattern</div>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={detail.hourly_pattern}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)"/>
                    <XAxis dataKey="hour" tick={{fill:"var(--text2)",fontSize:10}} tickFormatter={h=>`${h}h`}/>
                    <YAxis tick={{fill:"var(--text2)",fontSize:10}}/>
                    <Tooltip content={<ChartTooltip/>}/>
                    <Bar dataKey="avg_kwh" fill="#6366f1" name="Avg kWh" radius={[2,2,0,0]}/>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
