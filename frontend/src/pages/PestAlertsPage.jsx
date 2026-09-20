import React, { useState, useEffect } from 'react'
import { useApp } from '../App'
import { useNavigate } from 'react-router-dom'
import { ShieldAlert, Bug, Leaf, RefreshCw, AlertTriangle, CheckCircle, Info, Thermometer, Droplets } from 'lucide-react'
import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || ''

const RISK_CONFIG = {
  Critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.10)', border: 'rgba(239,68,68,0.30)', icon: '🔴' },
  High:     { color: '#f97316', bg: 'rgba(249,115,22,0.10)', border: 'rgba(249,115,22,0.30)', icon: '🟠' },
  Medium:   { color: '#eab308', bg: 'rgba(234,179,8,0.10)',  border: 'rgba(234,179,8,0.30)',  icon: '🟡' },
  Low:      { color: '#22c55e', bg: 'rgba(34,197,94,0.10)',  border: 'rgba(34,197,94,0.30)',  icon: '🟢' },
}

const CROPS = ['Wheat','Rice','Tomato','Cotton','Maize','Potato','Soybean','Groundnut','Chilli','Sugarcane']

function AlertCard({ alert }) {
  const cfg = RISK_CONFIG[alert.risk_level] || RISK_CONFIG.Low
  const pct = Math.round(alert.probability * 100)

  return (
    <div className="card p-4 transition-all" style={{ borderColor: alert.is_active ? cfg.border : 'var(--border)' }}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1">
          <div className="text-2xl mt-0.5">{alert.type === 'fungal' ? '🍄' : '🐛'}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-agro-100">{alert.name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold capitalize"
                style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
                {cfg.icon} {alert.risk_level}
              </span>
              {alert.is_active && (
                <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold animate-pulse"
                  style={{ background:'rgba(239,68,68,0.12)', color:'#ef4444', border:'1px solid rgba(239,68,68,0.3)' }}>
                  ⚠️ Active Risk
                </span>
              )}
            </div>
            <div className="text-xs text-agro-500 mt-0.5 capitalize">{alert.type} threat</div>
            <div className="text-[10px] text-agro-600 mt-1">{alert.conditions}</div>
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-xl font-bold" style={{ color: cfg.color }}>{pct}%</div>
          <div className="text-[10px] text-agro-600">probability</div>
        </div>
      </div>

      {/* Probability bar */}
      <div className="mt-3">
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background:'var(--glass-bg2)' }}>
          <div className="h-full rounded-full transition-all duration-700"
            style={{ width:`${pct}%`, background: cfg.color }} />
        </div>
      </div>

      {/* Prevention tips */}
      {alert.prevention?.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <div className="text-[10px] font-semibold text-agro-600 uppercase tracking-wider">Prevention</div>
          {alert.prevention.map((tip, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-agro-400">
              <CheckCircle size={11} className="text-green-500 shrink-0 mt-0.5" />
              {tip}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function PestAlertsPage() {
  const { lastResult } = useApp()
  const navigate = useNavigate()

  const [crop,     setCrop]     = useState(() => lastResult?.crop_type || lastResult?.crop || 'Wheat')
  const [temp,     setTemp]     = useState(() => 28)
  const [humidity, setHumidity] = useState(() => 65)
  const [severity, setSeverity] = useState(() => lastResult?.severity || 0)
  const [geoRisk,  setGeoRisk]  = useState(() => lastResult?.geo_risk || 'Low')
  const [alerts,   setAlerts]   = useState([])
  const [loading,  setLoading]  = useState(false)
  const [fetched,  setFetched]  = useState(false)

  async function fetchAlerts() {
    setLoading(true)
    try {
      const res = await axios.get(`${BASE}/pest-alerts`, {
        params: { crop, temp, humidity, severity, geo_risk: geoRisk }
      })
      setAlerts(res.data)
      setFetched(true)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { fetchAlerts() }, [crop])

  const activeAlerts   = alerts.filter(a => a.is_active)
  const criticalAlerts = alerts.filter(a => a.risk_level === 'Critical' || a.risk_level === 'High')

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-agro-100 flex items-center gap-2">
            <ShieldAlert size={20} style={{ color:'var(--green)' }} /> Pest & Disease Alerts
          </h1>
          <p className="text-agro-600 text-sm mt-0.5">
            AI-powered threat forecast based on crop, weather & geo-risk
          </p>
        </div>
        <button onClick={fetchAlerts} disabled={loading} className="btn-primary text-sm py-2">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Controls */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-3 items-end">
          {/* Crop */}
          <div className="flex-1 min-w-36">
            <div className="text-xs text-agro-500 font-medium mb-1.5">Crop</div>
            <select className="input-field text-sm py-2 appearance-none"
              value={crop} onChange={e => setCrop(e.target.value)}>
              {CROPS.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          {/* Temp */}
          <div className="min-w-28">
            <div className="text-xs text-agro-500 font-medium mb-1.5 flex items-center gap-1">
              <Thermometer size={11} /> Temp (°C)
            </div>
            <input type="number" min={5} max={50} className="input-field text-sm py-2 w-24"
              value={temp} onChange={e => setTemp(Number(e.target.value))} />
          </div>
          {/* Humidity */}
          <div className="min-w-28">
            <div className="text-xs text-agro-500 font-medium mb-1.5 flex items-center gap-1">
              <Droplets size={11} /> Humidity (%)
            </div>
            <input type="number" min={0} max={100} className="input-field text-sm py-2 w-24"
              value={humidity} onChange={e => setHumidity(Number(e.target.value))} />
          </div>
          {/* Geo Risk */}
          <div className="min-w-32">
            <div className="text-xs text-agro-500 font-medium mb-1.5">Geo Risk</div>
            <select className="input-field text-sm py-2 appearance-none"
              value={geoRisk} onChange={e => setGeoRisk(e.target.value)}>
              {['Low','Medium','High'].map(r => <option key={r}>{r}</option>)}
            </select>
          </div>
          <button onClick={fetchAlerts} disabled={loading}
            className="btn-primary text-sm py-2 px-4 shrink-0">
            Analyse
          </button>
        </div>
      </div>

      {/* Summary */}
      {fetched && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label:'Total Threats', val: alerts.length,        color:'var(--muted)'   },
            { label:'Active Risks',  val: activeAlerts.length,  color:'#f97316'        },
            { label:'Critical/High', val: criticalAlerts.length,color:'#ef4444'        },
          ].map(s => (
            <div key={s.label} className="card p-4 text-center">
              <div className="text-2xl font-bold" style={{ color: s.color }}>{s.val}</div>
              <div className="text-xs text-agro-600 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Alert cards */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_,i) => (
            <div key={i} className="h-28 rounded-2xl animate-pulse" style={{ background:'var(--glass-bg2)' }} />
          ))}
        </div>
      ) : fetched ? (
        alerts.length > 0 ? (
          <div className="space-y-3">
            {alerts.map((a, i) => <AlertCard key={i} alert={a} />)}
          </div>
        ) : (
          <div className="card p-10 text-center">
            <CheckCircle size={36} className="mx-auto mb-3 text-green-500" />
            <div className="text-sm font-medium text-agro-300">No significant threats detected</div>
            <div className="text-xs text-agro-600 mt-1">Conditions look favourable for {crop}</div>
          </div>
        )
      ) : null}

      {/* Info */}
      <div className="p-4 rounded-xl flex items-start gap-3"
        style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
        <Info size={14} className="text-agro-500 shrink-0 mt-0.5" />
        <div className="text-xs text-agro-500 leading-relaxed">
          Alerts are generated from crop-specific threat models combined with current temperature,
          humidity, seasonal factors, and geo-risk data from your area. Higher humidity + temperature
          within disease-conducive ranges increases probability scores.
        </div>
      </div>
    </div>
  )
}
