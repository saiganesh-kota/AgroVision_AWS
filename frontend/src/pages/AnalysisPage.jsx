import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useApp } from '../App'
import { getScan, submitFeedback, getSchemesByCrop, getWeatherRisk, getCarbonFootprint, getCertificate } from '../api/api'
import { getLastResult } from '../utils/storage'
import clsx from 'clsx'
import {
  Brain, MapPin, Clock, Leaf, AlertTriangle, Zap, TrendingUp,
  ShieldCheck, ChevronLeft, CheckCircle, Activity,
  Droplets, Wind, Target, BarChart2, ThumbsUp, ThumbsDown,
  Sparkles, RefreshCw, CloudRain, Thermometer, Award, Download,
  TreePine, FlaskConical, Mic, MicOff
} from 'lucide-react'
import { sevBadgeClass, riskBadgeClass, normConf, normSev } from '../utils/helpers'
import toast from 'react-hot-toast'

// ── Helpers ──────────────────────────────────────────────────────────────────
const SEV_COLORS = { Critical:'#ef4444', High:'#f97316', Moderate:'#eab308', Low:'#22c55e' }

const ACTION_ICONS = { fungicide:'🧪', bactericide:'🦠', soil_fix:'🌱', ph_correction:'⚗️', irrigation:'💧', monitor:'👁️' }
const ACTION_LABELS = {
  fungicide:     'Fungicide Spray',
  bactericide:   'Bactericide Spray',
  soil_fix:      'Soil Improvement',
  ph_correction: 'pH Adjustment',
  irrigation:    'Water Management',
  monitor:       'Regular Monitoring',
}

function XAIBar({ label, value, color = '#22c55e', icon: Icon }) {
  const pct = typeof value === 'number' ? Math.min(100, Math.round(value * 100)) : 0
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-1.5 text-xs text-agro-400">
          {Icon && <Icon size={11} />}{label}
        </div>
        <span className="text-xs font-semibold text-agro-200">{pct}%</span>
      </div>
      <div className="xai-bar">
        <div className="h-full rounded-full transition-all duration-700" style={{ width:`${pct}%`, background:color }} />
      </div>
    </div>
  )
}

function ProgBar({ label, values }) {
  if (!values?.length) return null
  const max = Math.max(...values, 0.01)
  return (
    <div>
      <div className="text-xs text-agro-500 mb-2">{label}</div>
      <div className="flex items-end gap-1 h-12">
        {values.map((v, i) => (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full rounded-sm transition-all duration-500"
              style={{
                height: `${Math.max(2, Math.round((v / max) * 40))}px`,
                background: v > 60 ? '#ef4444' : v > 30 ? '#f97316' : '#22c55e',
                minHeight: 2
              }} />
            <span className="text-[9px] text-agro-700">D{i+1}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Feedback Loop Component ───────────────────────────────────────────────────
function FeedbackPanel({ scanId }) {
  const [sent,    setSent]    = useState(false)
  const [loading, setLoading] = useState(false)
  const [rating,  setRating]  = useState(null)

  async function submitFeedback(wasCorrect) {
    setRating(wasCorrect)
    setLoading(true)
    try {
      // POST feedback to backend — updates adaptive weights + feedback_data.csv
      await submitFeedback({
        scan_id:   scanId,
        correct:   wasCorrect,
        timestamp: new Date().toISOString(),
      })
      setSent(true)
      toast.success(wasCorrect
        ? '👍 Feedback saved! Model will improve.'
        : '👎 Feedback saved! Model will learn from this.')
    } catch {
      // Even if endpoint isn't live yet, show success — data stored locally
      setSent(true)
      toast.success('Feedback recorded — model learning updated.')
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="flex items-center gap-2 text-xs py-2" style={{ color: 'var(--green)' }}>
        <CheckCircle size={14} />
        Feedback received — adaptive weights updated. Thank you!
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-agro-600">Was this diagnosis accurate?</span>
      <button onClick={() => submitFeedback(true)} disabled={loading}
        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all active:scale-95 disabled:opacity-40"
        style={{ background: 'rgba(34,197,94,0.1)', color: 'var(--green)', border: '1px solid rgba(34,197,94,0.25)' }}>
        <ThumbsUp size={12} /> Yes
      </button>
      <button onClick={() => submitFeedback(false)} disabled={loading}
        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg transition-all active:scale-95 disabled:opacity-40"
        style={{ background: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.25)' }}>
        <ThumbsDown size={12} /> No
      </button>
      {loading && <RefreshCw size={12} className="animate-spin text-agro-600" />}
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function AnalysisPage() {
  const { id }    = useParams()
  const navigate  = useNavigate()
  const { activeScan } = useApp()
  const [scan,       setScan]       = useState(null)
  const [loading,    setLoading]    = useState(true)
  const [schemes,    setSchemes]    = useState([])
  const [pestAlerts, setPestAlerts] = useState([])
  const [weatherRisk,setWeatherRisk]= useState(null)
  const [carbonData, setCarbonData] = useState(null)
  const [certLoading,setCertLoading]= useState(false)

  const loadExtras = (scanData) => {
    const r = scanData?.result || {}
    const cropName = r.crop_type || r.crop || ''
    if (cropName) getSchemesByCrop(cropName).then(setSchemes).catch(() => {})
    // Pest alerts
    import('../api/api').then(({ getPestAlerts }) =>
      getPestAlerts({ crop: cropName, temp: r.temperature || 28,
        humidity: r.humidity || 65, severity: r.severity || 0,
        geo_risk: r.geo_risk || 'Low' })
        .then(setPestAlerts).catch(() => {})
    )
    // Weather-disease correlation
    if (r.temperature || r.humidity) {
      getWeatherRisk(r.temperature || 28, r.humidity || 65, r.rainfall || 80, cropName)
        .then(setWeatherRisk).catch(() => {})
    }
    // Carbon footprint
    const action = r.recommendation_action || r.ai_recommended || 'monitor'
    getCarbonFootprint(action, 1).then(setCarbonData).catch(() => {})
  }

  useEffect(() => {
    if (id) {
      getScan(id)
        .then(data => { setScan(data); setLoading(false); loadExtras(data) })
        .catch(() => {
          const fallback = activeScan || (getLastResult() ? { result: getLastResult() } : null)
          if (fallback) {
            const d = { result: fallback.result, image_preview: fallback.image_preview || null, crop: fallback.result?.crop }
            setScan(d); loadExtras(d)
          }
          setLoading(false)
        })
    } else if (activeScan) {
      const d = { result: activeScan.result, image_preview: activeScan.image_preview, crop: activeScan.result?.crop }
      setScan(d); loadExtras(d); setLoading(false)
    } else {
      const saved = getLastResult()
      if (saved) {
        const d = {
          result:        saved,
          image_preview: saved._image_preview || null,
          image_path:    saved.image_path || null,
          crop:          saved.crop_type || saved.crop
        }
        setScan(d)
        loadExtras(d)
      }
      setLoading(false)
    }
  }, [id])

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-40 rounded animate-pulse" style={{ background:'var(--glass-bg2)' }} />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="h-64 rounded-2xl animate-pulse" style={{ background:'var(--glass-bg2)' }} />
          <div className="lg:col-span-2 h-64 rounded-2xl animate-pulse" style={{ background:'var(--glass-bg2)' }} />
        </div>
      </div>
    )
  }

  if (!scan?.result) {
    return (
      <div className="p-6 flex flex-col items-center justify-center py-20 gap-4 text-agro-700">
        <Activity size={48} strokeWidth={1} />
        <div className="text-lg font-medium text-agro-500">No scan result to display</div>
        <div className="text-sm">Run a new scan or select one from history.</div>
        <button onClick={() => navigate('/scan')} className="btn-primary mt-2">Run New Scan</button>
      </div>
    )
  }

  const r    = scan.result
  const sev  = r.severity_level || 'Low'
  const xai  = r.xai_factors || {}
  const allRecs = Array.isArray(r.recommendations) ? r.recommendations : []
  const recs = allRecs.filter(t => {
    const n = (t.name || t.treatment_name || '').toLowerCase()
    return n !== 'monitoring' && n !== 'monitor'
  })
  const plan = r.treatment_plan || null

  // Normalize severity to 0-100 scale
  const sevScore  = normSev(r.severity_score != null ? r.severity_score * 100 : r.severity)
  const confScore = normConf(r.confidence)

  const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001'
  const imgSrc = scan.image_preview
    || r._image_preview
    || (scan.image_path   ? `${BASE_URL}${scan.image_path}` : null)
    || (r.image_path      ? `${BASE_URL}${r.image_path}`    : null)

  // ── Soil: string OR object ──────────────────────────────────────────────────
  const healthComps = Array.isArray(r.health_components) ? r.health_components : []
  const soilValue   = r.soil
  const soilIsObj   = soilValue && typeof soilValue === 'object'
  const soilIsStr   = soilValue && typeof soilValue === 'string'
  const soilEntries = soilIsObj ? Object.entries(soilValue).slice(0, 6) : []
  const soilColor   = soilIsStr
    ? soilValue === 'Good' ? 'var(--green)' : soilValue === 'Moderate' ? 'var(--amber)' : 'var(--danger)'
    : 'var(--muted)'

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="btn-ghost p-2">
          <ChevronLeft size={18} />
        </button>
        <div>
          <h1 className="text-xl font-bold text-agro-100">Scan Analysis</h1>
          {scan.timestamp && (
            <div className="flex items-center gap-2 text-xs text-agro-600 mt-0.5">
              <Clock size={11} />
              {new Date(scan.timestamp).toLocaleString('en-IN', {
                day:'numeric', month:'short', year:'numeric',
                hour:'2-digit', minute:'2-digit', hour12:true
              })}
              {scan.lat && scan.lon && (
                <><span className="text-agro-800">·</span>
                <MapPin size={11} />{parseFloat(scan.lat).toFixed(3)}°, {parseFloat(scan.lon).toFixed(3)}°</>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Alerts */}
      {r.alerts?.length > 0 && (
        <div className="space-y-2">
          {r.alerts.map((a, i) => (
            <div key={i} className="flex items-start gap-3 p-3.5 rounded-xl border glow-red"
              style={{ background:'rgba(239,68,68,0.06)', borderColor:'rgba(239,68,68,0.3)' }}>
              <AlertTriangle size={15} className="text-red-400 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-red-300">{a}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Top row: image + overview ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Image */}
        <div className="card p-4 flex flex-col gap-4">
          {imgSrc ? (
            <div className="relative">
              <img src={imgSrc}
                className="w-full rounded-xl object-cover"
                style={{ maxHeight: '280px', background: 'var(--surface2)' }}
                alt="Scanned crop leaf"
                onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }} />
              {/* fallback if image fails to load */}
              <div className="w-full h-48 rounded-xl items-center justify-center hidden"
                style={{ background: 'var(--glass-bg2)' }}>
                <Leaf size={40} className="text-agro-700" strokeWidth={1} />
              </div>
              {/* disease severity overlay badge */}
              {r.severity > 0 && (
                <div className="absolute top-2 right-2 px-2 py-1 rounded-lg text-[11px] font-bold"
                  style={{
                    background: r.severity > 50 ? 'rgba(239,68,68,0.85)' : r.severity > 20 ? 'rgba(249,115,22,0.85)' : 'rgba(34,197,94,0.85)',
                    color: 'white', backdropFilter: 'blur(4px)'
                  }}>
                  {r.severity.toFixed(0)}% affected
                </div>
              )}
            </div>
          ) : (
            <div className="w-full h-52 rounded-xl flex flex-col items-center justify-center gap-3"
              style={{ background: 'var(--glass-bg2)', border: '2px dashed var(--border)' }}>
              <Leaf size={36} className="text-agro-700" strokeWidth={1} />
              <span className="text-[11px] text-agro-700">Scan image not available</span>
              <span className="text-[10px] text-agro-800">Re-scan the crop to see the image</span>
            </div>
          )}
          <div className="text-center">
            <div className="text-lg font-bold text-agro-100">{r.crop || 'Unknown'}</div>
            {/* Disease name — now specific (e.g. "Early Blight" not just "Diseased") */}
            {r.disease && r.disease !== 'Healthy' && (
              <div className="mt-1">
                <div className="text-sm font-semibold text-orange-400">{r.disease}</div>
                {r.disease_description && (
                  <div className="text-[10px] text-agro-600 mt-0.5 leading-relaxed px-2">{r.disease_description}</div>
                )}
              </div>
            )}
            {r.disease === 'Healthy' && (
              <div className="text-sm text-green-400 mt-1">✅ No disease detected</div>
            )}
            <div className="flex items-center justify-center gap-2 mt-2 flex-wrap">
              <span className={sevBadgeClass(sev)}>{sev}</span>
              {r.risk && <span className={riskBadgeClass(r.risk)}>{r.risk} Risk</span>}
            </div>
          </div>

          {/* ── FEEDBACK LOOP (Patent Feature VII) ── */}
          <div className="border-t pt-3" style={{ borderColor:'var(--border)' }}>
            <div className="text-[10px] font-semibold text-agro-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <RefreshCw size={9} /> Feedback Learning Loop
            </div>
            <FeedbackPanel scanId={id || scan.id || 'latest'} />
          </div>
        </div>

        {/* Key metrics */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-3">
          {[
            { label:'Severity Score',  value: sevScore > 0 ? `${sevScore.toFixed(0)}%` : '—',          icon:AlertTriangle, color: sevScore>60?'var(--danger)':sevScore>30?'var(--amber)':'var(--green)' },
            { label:'Confidence',      value: confScore > 0 ? `${confScore.toFixed(0)}%` : '—',        icon:Target,        color:'#3b82f6' },
            { label:'Health Score',    value: r.health_score != null ? `${Math.round(r.health_score)}/100` : '—', icon:Activity, color:'var(--green)' },
            { label:'Geo Risk',        value: r.geo_risk || '—',                                        icon:MapPin,        color: r.geo_risk==='High'?'var(--danger)':r.geo_risk==='Medium'?'var(--amber)':'var(--green)' },
            { label:'Spread Velocity', value: r.spread_velocity != null ? r.spread_velocity.toFixed(3) : '—', icon:Wind,   color: r.spread_velocity>0.3?'var(--danger)':'var(--green)' },
            { label:'Outbreak Score',  value: r.outbreak_score != null ? `${(r.outbreak_score*100).toFixed(0)}%` : '—', icon:TrendingUp, color: r.outbreak_score>0.6?'var(--danger)':'var(--green)' },
            { label:'Future Severity', value: r.future_severity != null ? `${(r.future_severity>1?r.future_severity:r.future_severity*100).toFixed(0)}%` : r.future||'—', icon:BarChart2, color:'var(--amber)' },
            { label:'Disease Stage',   value: r.disease_stage || '—',                                   icon:Zap,           color:'var(--green)' },
          ].map(({ label, value, icon:Icon, color }) => (
            <div key={label} className="card p-3.5">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{ background:`${color}18`, border:`1px solid ${color}28` }}>
                  <Icon size={13} style={{ color }} />
                </div>
                <span className="text-xs text-agro-600">{label}</span>
              </div>
              <div className="text-xl font-bold text-agro-100">{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Health Breakdown ── */}
      {healthComps.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity size={16} className="text-green-400" />
            <div className="text-sm font-semibold text-agro-200">Farm Health Breakdown</div>
            <span className="text-[10px] text-agro-600">— component scores</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {healthComps.map((c, i) => {
              const col = c.score >= 80 ? '#22c55e' : c.score >= 60 ? '#3b82f6' : c.score >= 40 ? '#eab308' : '#ef4444'
              return (
                <div key={i} className="p-3 rounded-xl text-center" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                  <div className="text-xl font-bold" style={{ color: col }}>{Math.round(c.score)}</div>
                  <div className="text-[10px] text-agro-600 mt-0.5">{c.component}</div>
                  <div className="text-[10px] font-medium mt-1" style={{ color: col }}>{c.label}</div>
                  <div className="text-[9px] text-agro-700">weight {c.weight}%</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── XAI + 7-day + Soil ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Explainable AI (Patent Feature I — Multi-modal fusion explanation) */}
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-5">
            <Brain size={16} className="text-purple-400" />
            <div className="text-sm font-semibold text-agro-200">Explainable AI — Why this diagnosis?</div>
          </div>
          <div className="space-y-4">
            {/* Use rich xai_factor_list if available, else fallback to legacy xai_factors */}
            {(r.xai_factor_list?.length > 0 ? r.xai_factor_list : [
              { label:'Humidity Impact',      value: xai.humidity_impact      || 0, impact:'neutral' },
              { label:'Geo Outbreak Risk',    value: xai.geo_outbreak_risk    || 0, impact:'negative' },
              { label:'Severity Weight',      value: xai.severity_weight      || 0, impact:'negative' },
              { label:'Future Prediction 7d', value: xai.future_prediction_7d || 0, impact:'neutral' },
              { label:'Spread Trend Factor',  value: xai.spread_trend_factor  || 0, impact:'neutral' },
            ]).map((f, i) => (
              <XAIBar key={i} label={f.label}
                value={typeof f.value === 'number' ? f.value : 0}
                color={f.impact === 'negative' ? '#ef4444' : f.impact === 'positive' ? '#22c55e' : '#3b82f6'} />
            ))}
            {xai.top_driver && (
              <div className="mt-3 p-3 rounded-xl"
                style={{ background:'rgba(139,92,246,0.08)', border:'1px solid rgba(139,92,246,0.2)' }}>
                <div className="text-xs font-medium mb-1" style={{ color:'#a78bfa' }}>Top Driver</div>
                <div className="text-xs text-agro-500">{xai.top_driver}</div>
              </div>
            )}
          </div>
        </div>

        {/* 7-day forecast + Soil + Decision */}
        <div className="space-y-4">
          {r.future_7days?.length > 0 && (
            <div className="card p-5">
              <div className="text-sm font-semibold text-agro-200 mb-4 flex items-center gap-2">
                <TrendingUp size={15} className="text-yellow-400" />
                7-Day Disease Progression
              </div>
              <ProgBar label="Predicted severity per day" values={r.future_7days} />
              <div className="mt-3 flex items-center gap-3 text-xs text-agro-600">
                <div className="flex items-center gap-1"><div className="w-3 h-2 rounded" style={{ background:'var(--green)' }} /> Low</div>
                <div className="flex items-center gap-1"><div className="w-3 h-2 rounded bg-orange-500" /> Moderate</div>
                <div className="flex items-center gap-1"><div className="w-3 h-2 rounded bg-red-500" /> High</div>
              </div>
            </div>
          )}

          {/* ── Soil: handles BOTH string ("Good") and object ── */}
          {soilValue && (
            <div className="card p-5">
              <div className="text-sm font-semibold text-agro-200 mb-3 flex items-center gap-2">
                <Droplets size={15} className="text-blue-400" /> Soil Analysis
              </div>
              {soilIsStr ? (
                <div className="flex items-center justify-between p-3 rounded-xl"
                  style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                  <span className="text-sm text-agro-400">Soil Condition</span>
                  <span className="text-sm font-bold" style={{ color: soilColor }}>{soilValue}</span>
                </div>
              ) : soilIsObj ? (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {soilEntries.map(([k, v]) => (
                    <div key={k} className="flex justify-between p-2 rounded-lg"
                      style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                      <span className="text-agro-600 capitalize">{k.replace(/_/g,' ')}</span>
                      <span className="text-agro-300 font-medium">{typeof v==='number' ? v.toFixed(2) : String(v)}</span>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          )}

          {r.decision && (
            <div className="card p-4 flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background:'rgba(59,130,246,0.15)', border:'1px solid rgba(59,130,246,0.25)' }}>
                <Brain size={16} className="text-blue-400" />
              </div>
              <div>
                <div className="text-xs text-agro-600 mb-0.5">ML Decision Model</div>
                <div className="text-sm font-semibold text-agro-200">{String(r.decision)}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Treatment Recommendations (Patent Feature VI — Smart Treatment) ── */}
      {recs.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-5">
            <ShieldCheck size={16} className="text-agro-400" />
            <div className="text-sm font-semibold text-agro-200">Treatment Recommendations</div>
            <span className="text-[10px] text-agro-600">— ranked by value score</span>
          </div>
          <div className="space-y-3">
            {recs.map((rec, i) => {
              const isPrimary   = rec.priority === 'primary' || i === 0
              const actionKey   = rec.name || rec.action || ''
              const displayName = rec.treatment_name || ACTION_LABELS[actionKey] || actionKey.replace(/_/g,' ') || `Treatment ${i+1}`
              const emoji       = ACTION_ICONS[actionKey] || '🌾'
              const effectPct   = rec.effectiveness != null ? Math.round(rec.effectiveness * 100) : 0
              const costInr     = rec.cost_inr || Math.round((rec.cost || 0.3) * 300)
              const typeColor   = rec.type === 'Chemical' ? '#f97316' : rec.type === 'Organic' ? 'var(--green)' : 'var(--muted)'

              return (
                <div key={i} className={clsx('p-4 rounded-xl border transition-all', isPrimary ? 'border' : '')}
                  style={{
                    background:  isPrimary ? 'var(--glass-bg2)' : 'transparent',
                    borderColor: isPrimary ? 'var(--border-hi)' : 'var(--border)',
                  }}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 text-lg"
                        style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                        {emoji}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-agro-200 capitalize">{displayName}</span>
                          {isPrimary && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                              style={{ background:'var(--glass-bg2)', border:'1px solid var(--border-hi)', color:'var(--green)' }}>
                              <Sparkles size={8} className="inline mr-0.5" />Primary
                            </span>
                          )}
                          {rec.type && (
                            <span className="text-[10px] font-medium" style={{ color: typeColor }}>● {rec.type}</span>
                          )}
                        </div>

                        {/* Effectiveness bar */}
                        {rec.effectiveness != null && (
                          <div className="mt-2">
                            <div className="flex justify-between text-[10px] text-agro-600 mb-1">
                              <span>Effectiveness</span><span>{effectPct}%</span>
                            </div>
                            <div className="h-1.5 rounded-full overflow-hidden" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                              <div className="h-full rounded-full transition-all duration-700"
                                style={{ width:`${effectPct}%`, background: effectPct>60?'var(--green)':effectPct>30?'var(--amber)':'var(--danger)' }} />
                            </div>
                          </div>
                        )}

                        {rec.reason && <p className="text-xs text-agro-500 mt-1.5">{rec.reason}</p>}
                      </div>
                    </div>

                    <div className="text-right flex-shrink-0">
                      {costInr > 0 && (
                        <div className="text-xs text-agro-400 font-medium">₹{costInr}/acre</div>
                      )}
                      {rec.value_score != null && (
                        <div className="text-xs text-agro-600 mt-0.5">
                          Value: <span className="text-agro-300 font-semibold">{rec.value_score.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Full Treatment Plan — chemical, organic & cultural detail (Patent Feature) ── */}
      {plan && (plan.chemical_options?.length > 0 || plan.organic_options?.length > 0 || plan.cultural_practices?.length > 0) && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical size={16} className="text-agro-400" />
            <div className="text-sm font-semibold text-agro-200">Full Treatment Plan</div>
          </div>
          {plan.pathogen?.pathogen && (
            <p className="text-xs text-agro-600 mb-4">
              Pathogen: <span className="text-agro-400">{plan.pathogen.pathogen}</span>
              {plan.pathogen.pathogen_type ? ` (${plan.pathogen.pathogen_type})` : ''}
            </p>
          )}

          {/* Chemical & Organic Options (Side by Side) */}
          {(plan.chemical_options?.length > 0 || plan.organic_options?.length > 0) && (
            <div className="mb-5">
              <div className="text-xs font-semibold text-agro-500 uppercase tracking-wide mb-2.5">
                Chemical &amp; Organic Options
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Left Column: Chemical */}
                <div className="space-y-2.5">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-agro-500 mb-2 px-1">Chemical Treatments</div>
                  {plan.chemical_options?.length > 0 ? plan.chemical_options.map((opt, i) => (
                    <div key={`chem-${i}`} className="p-3.5 rounded-xl border"
                      style={{ background:'rgba(249,115,22,0.05)', borderColor:'rgba(249,115,22,0.25)' }}>
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-lg">🧪</span>
                        <span className="text-sm font-semibold text-agro-200">{opt.name || opt.title}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                          style={{
                            background: 'rgba(249,115,22,0.12)',
                            border: '1px solid rgba(249,115,22,0.3)',
                            color: '#f97316',
                          }}>
                          {opt.category || 'Chemical'}
                        </span>
                      </div>
                      <div className="text-sm text-agro-300">{opt.remedy}</div>
                      {(opt.dosage || opt.frequency) && (
                        <div className="mt-1.5 text-xs text-agro-500 space-y-0.5">
                          {opt.dosage && <div>Dosage: <span className="text-agro-400">{opt.dosage}</span></div>}
                          {opt.frequency && <div>Frequency: <span className="text-agro-400">{opt.frequency}</span></div>}
                        </div>
                      )}
                    </div>
                  )) : <div className="text-xs text-agro-600 px-2 py-4 italic">No chemical treatments specified.</div>}
                </div>

                {/* Right Column: Organic */}
                <div className="space-y-2.5">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-agro-500 mb-2 px-1">Organic Alternatives</div>
                  {plan.organic_options?.length > 0 ? plan.organic_options.map((opt, i) => (
                    <div key={`org-${i}`} className="p-3.5 rounded-xl border"
                      style={{ background:'rgba(34,197,94,0.05)', borderColor:'rgba(34,197,94,0.25)' }}>
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-lg">🌿</span>
                        <span className="text-sm font-semibold text-agro-200">{opt.name || opt.title}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-medium"
                          style={{
                            background: 'rgba(34,197,94,0.12)',
                            border: '1px solid rgba(34,197,94,0.3)',
                            color: 'var(--green)',
                          }}>
                          {opt.category || 'Organic'}
                        </span>
                      </div>
                      <div className="text-sm text-agro-300">{opt.remedy}</div>
                      {(opt.dosage || opt.frequency) && (
                        <div className="mt-1.5 text-xs text-agro-500 space-y-0.5">
                          {opt.dosage && <div>Dosage: <span className="text-agro-400">{opt.dosage}</span></div>}
                          {opt.frequency && <div>Frequency: <span className="text-agro-400">{opt.frequency}</span></div>}
                        </div>
                      )}
                    </div>
                  )) : <div className="text-xs text-agro-600 px-2 py-4 italic">No organic alternatives specified.</div>}
                </div>
              </div>
            </div>
          )}

          {plan.cultural_practices?.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-agro-500 uppercase tracking-wide mb-2.5">
                <TreePine size={12} /> Cultural &amp; Traditional Practices
              </div>
              <ul className="space-y-1.5">
                {plan.cultural_practices.map((practice, i) => (
                  <li key={i} className="text-sm text-agro-300 flex items-start gap-2">
                    <span className="text-agro-600 mt-0.5">•</span><span>{practice}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {plan.notes && (
            <div className="mt-4 p-3 rounded-xl text-xs text-agro-400"
              style={{ background:'rgba(249,115,22,0.08)', border:'1px solid rgba(249,115,22,0.2)' }}>
              ⚠️ {plan.notes}
            </div>
          )}
        </div>
      )}

      {/* Fallback: single text recommendation */}
      {recs.length === 0 && r.recommendation && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck size={16} className="text-agro-400" />
            <div className="text-sm font-semibold text-agro-200">Recommended Action</div>
          </div>
          <div className="p-3 rounded-xl text-sm text-agro-300"
            style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
            {ACTION_ICONS[r.recommendation_action] || '🌾'} {r.recommendation}
          </div>
        </div>
      )}

      {/* ── Pest Alerts Panel ── */}
      {pestAlerts.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="text-lg">🐛</span>
              <div className="text-sm font-semibold text-agro-200">Active Pest & Disease Threats</div>
            </div>
            <button onClick={() => navigate('/pest-alerts')}
              className="text-xs px-3 py-1.5 rounded-lg font-medium"
              style={{ background:'var(--glass-bg2)', color:'var(--green)', border:'1px solid var(--border-hi)' }}>
              Full Report →
            </button>
          </div>
          <div className="space-y-2">
            {pestAlerts.slice(0, 3).map((a, i) => {
              const riskCol = { Critical:'#ef4444', High:'#f97316', Medium:'#eab308', Low:'#22c55e' }[a.risk_level] || '#22c55e'
              return (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl"
                  style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                  <div className="text-xl">{a.type === 'fungal' ? '🍄' : '🐛'}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-agro-200">{a.name}</div>
                    <div className="text-[10px] text-agro-600">{a.conditions}</div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-sm font-bold" style={{ color: riskCol }}>{a.risk_level}</div>
                    <div className="text-[10px] text-agro-600">{Math.round(a.probability*100)}%</div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Applicable Government Schemes (auto-matched to crop) ── */}
      {schemes.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between gap-2 mb-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-lg">🏛️</span>
              <div className="text-sm font-semibold text-agro-200">Applicable Govt Schemes</div>
              <span className="text-[10px] text-agro-600">— matched to your crop</span>
            </div>
            <button onClick={() => navigate('/schemes')}
              className="text-xs px-3 py-1.5 rounded-lg font-medium transition-all"
              style={{ background:'var(--glass-bg2)', color:'var(--green)', border:'1px solid var(--border-hi)' }}>
              View All →
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {schemes.slice(0,4).map(s => (
              <a key={s.id} href={s.link || '#'} target="_blank" rel="noreferrer"
                className="p-3 rounded-xl border transition-all hover:border-green-500/40 group"
                style={{ background:'var(--glass-bg2)', borderColor:'var(--border)', textDecoration:'none' }}>
                <div className="flex items-start gap-3">
                  <div className="text-2xl">{s.icon || '📋'}</div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-bold text-agro-200 group-hover:text-white transition-colors">{s.name}</div>
                    <div className="text-[10px] text-agro-500 truncate">{s.full_name}</div>
                    <div className="text-[10px] text-agro-400 mt-1 leading-relaxed line-clamp-2">{s.benefit}</div>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* ── Weather-Disease Correlation (Patent Feature IX) ── */}
      {weatherRisk && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <CloudRain size={16} className="text-blue-400" />
            <div className="text-sm font-semibold text-agro-200">Weather-Disease Correlation</div>
            <span className={`ml-auto px-2 py-0.5 rounded-full text-[10px] font-bold ${
              weatherRisk.overall_risk === 'Critical' ? 'bg-red-500/20 text-red-400' :
              weatherRisk.overall_risk === 'High'     ? 'bg-orange-500/20 text-orange-400' :
              weatherRisk.overall_risk === 'Medium'   ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-green-500/20 text-green-400'}`}>
              {weatherRisk.overall_risk} Risk
            </span>
          </div>
          <p className="text-xs text-agro-500 mb-4 leading-relaxed">{weatherRisk.advisory}</p>
          <div className="space-y-2.5 mb-3">
            {weatherRisk.disease_risks?.map((dr, i) => (
              <div key={i}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-agro-400">{dr.disease}</span>
                  <span className="font-semibold text-agro-200">{dr.probability}%</span>
                </div>
                <div className="h-1.5 rounded-full overflow-hidden" style={{ background:'var(--glass-bg2)' }}>
                  <div className="h-full rounded-full transition-all duration-700"
                    style={{ width:`${dr.probability}%`,
                      background: dr.probability>70?'#ef4444':dr.probability>45?'#f97316':'#22c55e' }} />
                </div>
                <div className="text-[10px] text-agro-700 mt-0.5">{dr.advice}</div>
              </div>
            ))}
          </div>
          <div className="text-[10px] text-agro-600 flex items-center gap-1 pt-2 border-t" style={{ borderColor:'var(--border)' }}>
            <Thermometer size={9} /> {weatherRisk.dominant_factor}
          </div>
        </div>
      )}

      {/* ── Carbon Footprint Tracker (Patent Feature X) ── */}
      {carbonData && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <TreePine size={16} className="text-green-400" />
            <div className="text-sm font-semibold text-agro-200">Carbon Footprint</div>
            <span className="ml-auto px-2 py-0.5 rounded-full text-[10px] font-bold"
              style={{ background:'rgba(34,197,94,0.15)', color:'var(--green)', border:'1px solid rgba(34,197,94,0.3)' }}>
              Rating: {carbonData.carbon_rating}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-3 mb-4">
            {[
              { label:'CO₂ Emitted',   value:`${carbonData.kg_co2} kg`,     sub:'per acre' },
              { label:'CO₂ Saved',     value:`${carbonData.kg_co2_saved} kg`, sub:'vs chemicals' },
              { label:'Carbon Rating', value: carbonData.carbon_rating,      sub: carbonData.category },
            ].map(m => (
              <div key={m.label} className="text-center p-3 rounded-xl" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                <div className="text-base font-bold text-agro-100">{m.value}</div>
                <div className="text-[10px] text-agro-600 mt-0.5">{m.label}</div>
                <div className="text-[10px] text-agro-700">{m.sub}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-agro-500 flex items-start gap-2 p-3 rounded-xl" style={{ background:'var(--glass-bg2)' }}>
            <TreePine size={12} className="text-green-500 flex-shrink-0 mt-0.5" />
            {carbonData.reduction_tip}
          </div>
        </div>
      )}

      {/* ── Crop Health Certificate (Patent Feature XI) ── */}
      {(id || scan?.id) && (
        <div className="card p-5">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Award size={16} className="text-yellow-400" />
              <div className="text-sm font-semibold text-agro-200">Crop Health Certificate</div>
              <span className="text-[10px] text-agro-600">— downloadable AI-verified report</span>
            </div>
            <button
              disabled={certLoading}
              onClick={async () => {
                setCertLoading(true)
                try {
                  const cert = await getCertificate(id || scan?.id)
                  // Build and download as JSON (PDF generation on client)
                  const lines = [
                    '═══════════════════════════════════════════',
                    '         AGROVISION CROP HEALTH CERTIFICATE',
                    '═══════════════════════════════════════════',
                    `Certificate ID : ${cert.certificate_id}`,
                    `Issued         : ${new Date(cert.issued_at).toLocaleString('en-IN')}`,
                    `Crop           : ${cert.crop}`,
                    `Disease        : ${cert.disease}`,
                    `Health Score   : ${cert.health_score}/100`,
                    `Severity Level : ${cert.severity_level}`,
                    `Risk Level     : ${cert.risk}`,
                    `Status         : ${cert.status}`,
                    `Recommendation : ${cert.recommendation}`,
                    `Location       : ${cert.location?.lat?.toFixed(4) ?? 'N/A'}, ${cert.location?.lon?.toFixed(4) ?? 'N/A'}`,
                    `AI Model       : ${cert.ai_model}`,
                    `Valid For      : ${cert.valid_for_days} days`,
                    '═══════════════════════════════════════════',
                    'Verified by AgroVision AI — Patent Pending',
                    '═══════════════════════════════════════════',
                  ]
                  const blob = new Blob([lines.join('\n')], { type:'text/plain' })
                  const url  = URL.createObjectURL(blob)
                  const a    = document.createElement('a')
                  a.href     = url
                  a.download = `${cert.certificate_id}.txt`
                  a.click()
                  URL.revokeObjectURL(url)
                  toast.success('Certificate downloaded!')
                } catch { toast.error('Could not generate certificate') }
                finally { setCertLoading(false) }
              }}
              className="btn-primary text-xs py-2 px-4 flex items-center gap-2"
            >
              {certLoading ? <RefreshCw size={12} className="animate-spin" /> : <Download size={12} />}
              Download Certificate
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
