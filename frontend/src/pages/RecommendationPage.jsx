import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../App'
import { getLastResult } from '../utils/storage'
import { getHistory } from '../api/api'
import clsx from 'clsx'
import {
  Sparkles, Target, Zap, Info, CheckCircle2, ScanLine,
  TrendingUp, DollarSign, Star, ShoppingBag, MapPin, Phone,
  ChevronDown, Clock, Leaf, FlaskConical, TreePine, AlertTriangle
} from 'lucide-react'
import { riskBadgeClass } from '../utils/helpers'

const ACTION_ICONS = { fungicide:'🧪', bactericide:'🦠', soil_fix:'🌱', ph_correction:'⚗️', irrigation:'💧', monitor:'👁️' }
const ACTION_DESC = {
  fungicide:     'Apply recommended antifungal spray to infected areas at prescribed dosage.',
  bactericide:   'Apply copper-based bactericide. Do NOT use fungicide — it is ineffective on bacteria.',
  soil_fix:      'Incorporate organic compost to improve soil structure and microbial activity.',
  ph_correction: 'Add lime to raise pH or sulphur to lower it. Retest after 4 weeks.',
  irrigation:    'Increase irrigation using drip systems. Avoid overhead watering on foliage.',
  monitor:       'Inspect every 2–3 days. Document changes in leaf colour and spots.',
}

function TreatmentCard({ t, isBest, isRecommended, treatmentDetail, culturalPractices }) {
  const effectPct = Math.round((t.effectiveness || 0) * 100)
  const costBar   = Math.round((t.cost || 0) * 100)
  const typeColor = t.type === 'Chemical' ? '#f97316' : t.type === 'Organic' ? '#22c55e' : 'var(--muted)'
  const detail    = treatmentDetail || {}
  const hasDetail = detail.product || detail.dosage || detail.frequency

  return (
    <div className={clsx('card p-4 transition-all', isRecommended && 'border')}
      style={{ borderColor: isRecommended ? 'var(--border-hi)' : 'var(--border)' }}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{ACTION_ICONS[t.name] || '🌾'}</span>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-agro-100 capitalize">{t.treatment_name || t.name?.replace(/_/g,' ')}</span>
              {isRecommended && (
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full flex items-center gap-1"
                  style={{ background: 'var(--glass-bg2)', color: 'var(--green)', border: '1px solid var(--border-hi)' }}>
                  <Sparkles size={8} /> AI Pick
                </span>
              )}
              {isBest && !isRecommended && (
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                  style={{ background: 'rgba(234,179,8,0.12)', color: '#d97706', border: '1px solid rgba(234,179,8,0.28)' }}>
                  Best Value
                </span>
              )}
            </div>
            <div className="text-xs mt-0.5" style={{ color: typeColor }}>● {t.type || 'Unknown'}</div>
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-lg font-bold font-display" style={{ color: 'var(--green)' }}>
            {effectPct}%
          </div>
          <div className="text-[10px] text-agro-600">effective</div>
        </div>
      </div>

      {/* Disease-specific product info (from knowledge base) */}
      {hasDetail ? (
        <div className="mb-3 p-3 rounded-xl space-y-1.5"
          style={{ background: 'rgba(34,197,94,0.05)', border: '1px solid rgba(34,197,94,0.15)' }}>
          {detail.product && (
            <div className="flex gap-2 text-xs">
              <span className="text-agro-500 shrink-0 w-16">Product:</span>
              <span className="text-agro-200 font-medium">{detail.product}</span>
            </div>
          )}
          {detail.dosage && (
            <div className="flex gap-2 text-xs">
              <span className="text-agro-500 shrink-0 w-16">Dosage:</span>
              <span className="text-agro-300">{detail.dosage}</span>
            </div>
          )}
          {detail.frequency && (
            <div className="flex gap-2 text-xs">
              <span className="text-agro-500 shrink-0 w-16">Frequency:</span>
              <span className="text-agro-300">{detail.frequency}</span>
            </div>
          )}
          {detail.organic_alt && (
            <div className="flex gap-2 text-xs">
              <span className="text-agro-500 shrink-0 w-16">🌿 Organic:</span>
              <span className="text-agro-300">{detail.organic_alt}</span>
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-agro-600 mb-3 leading-relaxed">
          {ACTION_DESC[t.name] || 'Consult your local agri-centre.'}
        </p>
      )}

      <div className="space-y-2">
        <div>
          <div className="flex justify-between text-[10px] text-agro-600 mb-1">
            <span>Effectiveness</span><span>{effectPct}%</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
            <div className="h-full rounded-full transition-all duration-700"
              style={{ width: `${effectPct}%`, background: effectPct > 60 ? 'var(--green)' : effectPct > 30 ? 'var(--amber)' : 'var(--danger)' }} />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-[10px] text-agro-600 mb-1">
            <span>Cost</span><span>₹{t.cost_inr || Math.round((t.cost || 0) * 300)}/acre</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
            <div className="h-full rounded-full" style={{ width: `${costBar}%`, background: 'var(--amber)' }} />
          </div>
        </div>
      </div>


    </div>
  )
}

export default function RecommendationPage() {
  const navigate = useNavigate()
  const { activeScan, setActiveScan } = useApp()
  const [history,     setHistory]     = useState([])
  const [showPicker,  setShowPicker]  = useState(false)
  const [loadingHist, setLoadingHist] = useState(false)

  // Primary data source: activeScan → localStorage fallback
  const r = activeScan?.result || getLastResult()

  // Load scan history for picker
  useEffect(() => {
    setLoadingHist(true)
    getHistory(30).then(d => { setHistory(Array.isArray(d) ? d : []); setLoadingHist(false) }).catch(() => setLoadingHist(false))
  }, [])

  function selectScan(scan) {
    setActiveScan({ result: scan.result, image_preview: null })
    setShowPicker(false)
  }

  if (!r) {
    return (
      <div className="p-6 flex flex-col items-center justify-center py-20 gap-4 text-agro-700">
        <div className="text-4xl">🌿</div>
        <div className="text-sm text-agro-500">No analysis yet. Run a scan first.</div>
        <button onClick={() => navigate('/scan')} className="btn-primary">
          <ScanLine size={15} /> Go to Scan
        </button>
      </div>
    )
  }

  const rec          = r.recommendation || 'Monitor crop regularly'
  const action       = r.recommendation_action || r.ai_recommended || 'monitor'
  const details      = r.recommendation_details || {}
  const explainScore = typeof r.explainability === 'number' ? r.explainability : 0
  const allTreatments = Array.isArray(r.recommendations) ? r.recommendations : []
  const treatments = allTreatments.filter(t => {
    const n = (t.name || t.treatment_name || '').toLowerCase()
    return n !== 'monitoring' && n !== 'monitor'
  })
  const bestValue    = r.best_value || ''
  const suppliers    = Array.isArray(r.nearby_suppliers) ? r.nearby_suppliers : []
  const expColor     = explainScore > 70 ? 'var(--green)' : explainScore > 40 ? 'var(--amber)' : 'var(--danger)'
  const urgencyColor = details.urgency === 'HIGH' ? 'var(--danger)' : 'var(--amber)'

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-agro-100 flex items-center gap-2">
            <Sparkles className="text-[var(--green)]" size={24} /> AI Recommendation
          </h1>
          <p className="text-agro-600 text-sm mt-1">ML + RL adaptive treatment plan</p>
        </div>
        {/* Scan selector — view advice for any past scan */}
        <div className="relative">
          <button onClick={() => setShowPicker(o => !o)}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded-xl font-medium transition-all"
            style={{ background:'var(--glass-bg2)', color:'var(--muted)', border:'1px solid var(--border)' }}>
            <Leaf size={12} />
            {r.crop_type || r.crop || 'Current scan'}
            <ChevronDown size={11} />
          </button>

          {showPicker && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowPicker(false)} />
              <div className="absolute right-0 mt-1 z-50 w-64 rounded-xl shadow-xl overflow-hidden max-h-72 overflow-y-auto"
                style={{ background:'var(--glass-bg)', border:'1px solid var(--border)', backdropFilter:'blur(16px)' }}>
                <div className="px-3 py-2 text-[10px] font-bold text-agro-600 uppercase tracking-wider border-b"
                  style={{ borderColor:'var(--border)' }}>
                  Select scan to view advice
                </div>
                {loadingHist ? (
                  <div className="p-3 text-xs text-agro-600">Loading…</div>
                ) : history.length === 0 ? (
                  <div className="p-3 text-xs text-agro-600">No history yet</div>
                ) : history.map((scan, i) => (
                  <button key={scan.id} onClick={() => selectScan(scan)}
                    className="w-full px-3 py-2.5 text-left flex items-center gap-2.5 transition-colors hover:bg-glass-bg2 border-b"
                    style={{ borderColor:'var(--border)', background: i === 0 ? 'var(--glass-bg2)' : 'transparent' }}>
                    <div className="text-lg">{ACTION_ICONS[scan.result?.recommendation_action] || '🌿'}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold text-agro-200 truncate">
                        {scan.result?.crop_type || scan.result?.crop || scan.crop || 'Unknown crop'}
                        {i === 0 && <span className="ml-1.5 text-[9px] text-green-400">● Latest</span>}
                      </div>
                      <div className="text-[10px] text-agro-600 flex items-center gap-1">
                        <Clock size={9} />
                        {new Date(scan.timestamp).toLocaleDateString('en-IN', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' })}
                      </div>
                      <div className="text-[10px] text-agro-500">
                        Severity: {(scan.result?.severity || 0).toFixed(0)}% · Risk: {scan.result?.risk || '—'}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── LEFT COLUMN (Main Content) ── */}
        <div className="lg:col-span-2 space-y-6">
          {/* Primary recommendation */}
          <div className="card p-6 relative overflow-hidden"
            style={{ 
              borderColor: 'var(--green)', 
              boxShadow: '0 0 30px rgba(34,197,94,0.15)',
              background: 'linear-gradient(145deg, var(--glass-bg) 0%, rgba(34,197,94,0.03) 100%)' 
            }}>
            <div className="absolute top-4 right-4 flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-full"
              style={{ color: 'var(--green)', background: 'var(--glass-bg2)', border: '1px solid var(--border-hi)' }}>
              <Sparkles size={12} /> Top AI Pick
            </div>
            <div className="flex items-start gap-4 mb-4 pr-24">
              <div className="text-5xl shrink-0 drop-shadow-md">{ACTION_ICONS[action] || '🌾'}</div>
              <div>
                <p className="text-xs font-semibold text-agro-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                  <Target size={12} /> Recommended Action
                </p>
                <h2 className="text-2xl font-bold font-display text-agro-100">{rec}</h2>
              </div>
            </div>
            <p className="text-sm text-agro-300 leading-relaxed mb-5 p-4 rounded-xl"
              style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
              {ACTION_DESC[action] || 'Continue regular monitoring.'}
            </p>
            
            {/* Pathogen info — shown when disease identified */}
            {(r.pathogen || r.pathogen_type) && r.pathogen_type !== 'none' && (
              <div className="mb-4 p-4 rounded-xl text-sm"
                style={{ background: 'rgba(234,179,8,0.08)', border: '1px solid rgba(234,179,8,0.3)' }}>
                <span className="text-amber-400 font-bold">🔬 Detected Pathogen: </span>
                <span className="text-agro-200 font-medium ml-1">{r.pathogen || 'Not identified'}</span>
                {r.pathogen_type && (
                  <span className="ml-2 text-agro-500 text-xs">({r.pathogen_type})</span>
                )}
                {r.pathogen_type === 'bacterial' && (
                  <div className="mt-2 text-red-400 font-semibold flex items-center gap-2">
                    <AlertTriangle size={14} /> Bacterial infection — fungicide will NOT work. Bactericide required.
                  </div>
                )}
              </div>
            )}
            
            <div className="flex flex-wrap gap-3">
              {details.urgency && (
                <span className="text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-1.5"
                  style={{ background: `${urgencyColor}18`, color: urgencyColor, border: `1px solid ${urgencyColor}30` }}>
                  <Zap size={14} /> {details.urgency} URGENCY
                </span>
              )}
              {details.estimated_cost > 0 && (
                <span className="text-xs font-semibold px-4 py-2 rounded-xl flex items-center gap-1.5"
                  style={{ background: 'var(--glass-bg2)', color: 'var(--muted)', border: '1px solid var(--border)' }}>
                  <DollarSign size={14} /> ₹{Math.round(details.estimated_cost)}/acre estimated
                </span>
              )}
              {details.effectiveness > 0 && (
                <span className="text-xs font-bold px-4 py-2 rounded-xl flex items-center gap-1.5"
                  style={{ background: 'rgba(34,197,94,0.1)', color: 'var(--green)', border: '1px solid rgba(34,197,94,0.3)' }}>
                  <CheckCircle2 size={14} /> {Math.round(details.effectiveness)}% EFFECTIVE
                </span>
              )}
            </div>
          </div>

          {/* ── Full Treatment Plan ── */}
          {(() => {
            const plan = r.treatment_plan || null
            if (!plan || (!plan.chemical_options?.length && !plan.organic_options?.length && !plan.cultural_practices?.length)) return null
            return (
              <div className="card overflow-hidden border border-[var(--border-hi)]">
                {/* Header banner */}
                <div className="p-5 pb-4" style={{
                  background: 'linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(59,130,246,0.1) 100%)',
                  borderBottom: '1px solid var(--border)'
                }}>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg"
                      style={{ background: 'rgba(34,197,94,0.2)', border: '1px solid rgba(34,197,94,0.4)' }}>
                      <FlaskConical size={22} style={{ color: 'var(--green)' }} />
                    </div>
                    <div>
                      <div className="text-lg font-bold" style={{ color: 'var(--on-surface)' }}>Full Treatment Plan</div>
                      <div className="text-sm mt-0.5" style={{ color: 'var(--muted)' }}>Detailed chemical, organic &amp; cultural prescriptions</div>
                    </div>
                    {plan.pathogen?.pathogen && (
                      <div className="ml-auto shrink-0 px-3 py-1.5 rounded-xl text-xs font-bold"
                        style={{ background: 'rgba(234,179,8,0.15)', border: '1px solid rgba(234,179,8,0.3)', color: '#d97706' }}>
                        🔬 {plan.pathogen.pathogen}
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-6 space-y-8">
                  {/* Chemical & Organic Options */}
                  {(plan.chemical_options?.length > 0 || plan.organic_options?.length > 0) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Left Column: Chemical */}
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-sm shadow-sm"
                            style={{ background: 'rgba(249,115,22,0.15)', border: '1px solid rgba(249,115,22,0.3)' }}>🧪</div>
                          <span className="text-sm font-bold tracking-wide uppercase text-[#f97316]">Chemical Options</span>
                        </div>
                        {plan.chemical_options?.length > 0 ? plan.chemical_options.map((opt, i) => (
                          <div key={`chem-${i}`} className="rounded-xl overflow-hidden shadow-sm"
                            style={{ border: '1px solid rgba(249,115,22,0.25)', background: 'rgba(249,115,22,0.05)' }}>
                            <div className="flex items-center gap-2.5 px-4 py-3" style={{ borderBottom: '1px solid rgba(249,115,22,0.25)' }}>
                              <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider"
                                style={{ background: 'rgba(249,115,22,0.15)', color: '#f97316' }}>
                                {opt.category || 'Chemical'}
                              </span>
                              <span className="text-sm font-bold" style={{ color: 'var(--on-surface)' }}>{opt.name || opt.title}</span>
                            </div>
                            <div className="px-4 py-4 space-y-3">
                              {opt.remedy && <p className="text-sm leading-relaxed" style={{ color: 'var(--agro-300)' }}>{opt.remedy}</p>}
                              {(opt.dosage || opt.frequency) && (
                                <div className="grid grid-cols-2 gap-3">
                                  {opt.dosage && (
                                    <div className="rounded-lg px-3 py-2" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)' }}>
                                      <div className="text-[10px] font-semibold uppercase tracking-wider mb-1 text-agro-500">Dosage</div>
                                      <div className="text-xs font-semibold text-agro-200">{opt.dosage}</div>
                                    </div>
                                  )}
                                  {opt.frequency && (
                                    <div className="rounded-lg px-3 py-2" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)' }}>
                                      <div className="text-[10px] font-semibold uppercase tracking-wider mb-1 text-agro-500">Frequency</div>
                                      <div className="text-xs font-semibold text-agro-200">{opt.frequency}</div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )) : <div className="text-xs text-agro-600 px-2 py-4 italic">No chemical treatments specified.</div>}
                      </div>

                      {/* Right Column: Organic */}
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-sm shadow-sm"
                            style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }}>🌿</div>
                          <span className="text-sm font-bold tracking-wide uppercase text-[#22c55e]">Organic Alternatives</span>
                        </div>
                        {plan.organic_options?.length > 0 ? plan.organic_options.map((opt, i) => (
                          <div key={`org-${i}`} className="rounded-xl overflow-hidden shadow-sm"
                            style={{ border: '1px solid rgba(34,197,94,0.25)', background: 'rgba(34,197,94,0.05)' }}>
                            <div className="flex items-center gap-2.5 px-4 py-3" style={{ borderBottom: '1px solid rgba(34,197,94,0.25)' }}>
                              <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider"
                                style={{ background: 'rgba(34,197,94,0.15)', color: '#22c55e' }}>
                                {opt.category || 'Organic'}
                              </span>
                              <span className="text-sm font-bold" style={{ color: 'var(--on-surface)' }}>{opt.name || opt.title}</span>
                            </div>
                            <div className="px-4 py-4 space-y-3">
                              {opt.remedy && <p className="text-sm leading-relaxed" style={{ color: 'var(--agro-300)' }}>{opt.remedy}</p>}
                              {(opt.dosage || opt.frequency) && (
                                <div className="grid grid-cols-2 gap-3">
                                  {opt.dosage && (
                                    <div className="rounded-lg px-3 py-2" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)' }}>
                                      <div className="text-[10px] font-semibold uppercase tracking-wider mb-1 text-agro-500">Dosage</div>
                                      <div className="text-xs font-semibold text-agro-200">{opt.dosage}</div>
                                    </div>
                                  )}
                                  {opt.frequency && (
                                    <div className="rounded-lg px-3 py-2" style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid var(--border)' }}>
                                      <div className="text-[10px] font-semibold uppercase tracking-wider mb-1 text-agro-500">Frequency</div>
                                      <div className="text-xs font-semibold text-agro-200">{opt.frequency}</div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )) : <div className="text-xs text-agro-600 px-2 py-4 italic">No organic alternatives specified.</div>}
                      </div>
                    </div>
                  )}

                  {/* Divider between sections */}
                  {plan.chemical_options?.length > 0 && plan.cultural_practices?.length > 0 && (
                    <div style={{ borderTop: '1px dashed var(--border-hi)' }} />
                  )}

                  {/* Cultural Practices */}
                  {plan.cultural_practices?.length > 0 && (
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl flex items-center justify-center shadow-sm"
                          style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }}>
                          <TreePine size={16} style={{ color: 'var(--green)' }} />
                        </div>
                        <span className="text-base font-bold text-agro-100">Cultural &amp; Traditional Practices</span>
                        <span className="text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider ml-auto"
                          style={{ background: 'rgba(34,197,94,0.1)', color: 'var(--green)', border: '1px solid rgba(34,197,94,0.25)' }}>
                          {plan.cultural_practices.length} step{plan.cultural_practices.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {plan.cultural_practices.map((practice, i) => (
                          <div key={i} className="flex items-start gap-3 p-4 rounded-xl transition-all hover:border-[var(--green)]"
                            style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
                            <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-black flex-shrink-0"
                              style={{ background: 'var(--glass-bg)', border: '2px solid var(--green)', color: 'var(--green)' }}>
                              {i + 1}
                            </div>
                            <p className="text-sm leading-relaxed flex-1 pt-0.5 text-agro-200">{practice}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Warning note */}
                  {plan.notes && (
                    <div className="flex items-start gap-3 p-4 rounded-xl shadow-inner"
                      style={{ background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.3)' }}>
                      <AlertTriangle size={18} className="text-orange-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm leading-relaxed font-medium" style={{ color: '#fbd38d' }}>{plan.notes}</p>
                    </div>
                  )}
                </div>
              </div>
            )
          })()}

          {/* Treatment comparison (Grid Layout now) */}
          {treatments.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Target size={18} className="text-agro-400" />
                <div className="text-lg font-bold text-agro-100">Alternative Options</div>
                <span className="text-xs text-agro-500 font-medium ml-2 bg-[var(--glass-bg2)] px-2 py-1 rounded border border-[var(--border)]">— Ranked by AI Value</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {treatments.map((t, i) => (
                  <TreatmentCard key={i} t={t}
                    isBest={t.name === bestValue}
                    isRecommended={t.name === action || t.priority === 'primary' || i === 0}
                    treatmentDetail={t.name === action ? details.treatment_detail : null}
                    culturalPractices={t.name === action ? (r.cultural_practices || details.cultural_practices) : null} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT COLUMN (Side Panel) ── */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Crop context banner */}
          <div className="card p-5 overflow-hidden relative">
            <div className="absolute -right-4 -top-4 opacity-10 text-9xl">🌾</div>
            <div className="text-xs font-bold text-agro-500 uppercase tracking-wider mb-2">Advice for</div>
            <div className="text-2xl font-bold text-agro-100 mb-2 drop-shadow-md">
              {r.crop_type || r.crop || 'Unknown Crop'}
            </div>
            
            <div className="flex flex-col gap-2 mt-4">
              <div className="flex justify-between items-center bg-[var(--glass-bg2)] p-2 rounded-lg border border-[var(--border)]">
                <span className="text-xs text-agro-500 font-semibold">Status</span>
                <span className="text-sm font-bold text-agro-200">
                  {r.disease_status || (r.severity > 10 ? 'Diseased' : 'Healthy')}
                </span>
              </div>
              <div className="flex justify-between items-center bg-[var(--glass-bg2)] p-2 rounded-lg border border-[var(--border)]">
                <span className="text-xs text-agro-500 font-semibold">Severity</span>
                <span className="text-sm font-bold text-agro-200">
                  {(r.severity||0).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between items-center bg-[var(--glass-bg2)] p-2 rounded-lg border border-[var(--border)]">
                <span className="text-xs text-agro-500 font-semibold">Risk Level</span>
                <span className={clsx('badge text-xs', riskBadgeClass(r.risk))}>{r.risk || 'Low'} Risk</span>
              </div>
            </div>
          </div>

          {/* Explainability score */}
          {explainScore > 0 && (
            <div className="card p-5 relative overflow-hidden text-center" style={{ border: `1px solid ${expColor}40` }}>
              <div className="absolute inset-0 opacity-5" style={{ background: `radial-gradient(circle at center, ${expColor} 0%, transparent 70%)` }} />
              <div className="text-xs font-bold text-agro-400 uppercase tracking-wider mb-4">AI Confidence Score</div>
              
              <div className="w-24 h-24 mx-auto rounded-full flex items-center justify-center text-4xl font-black drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]"
                style={{ 
                  background: `${expColor}15`, 
                  border: `4px solid ${expColor}`, 
                  color: expColor,
                  boxShadow: `0 0 20px ${expColor}30`
                }}>
                {Math.round(explainScore)}
              </div>
              <div className="text-xs text-agro-500 mt-4 font-medium px-4">Based on neural network certainty and environmental cross-validation</div>
            </div>
          )}

          {/* Nearby Agri-Shops (Google Places) */}
          {suppliers.length > 0 && (
            <div className="card p-5">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[var(--border)]">
                <div className="flex items-center gap-2">
                  <ShoppingBag size={18} className="text-[var(--amber)]" />
                  <div className="text-sm font-bold text-agro-100">Nearby Shops</div>
                </div>
                <span className="text-xs font-bold bg-[var(--glass-bg2)] px-2 py-1 rounded text-agro-400">{suppliers.length}</span>
              </div>
              <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                {suppliers.slice(0, 8).map((s, i) => (
                  <div key={i} className="flex flex-col gap-2 p-3.5 rounded-xl transition-all hover:bg-[var(--glass-bg2)] hover:border-[var(--green)] border border-[var(--border)]"
                    style={{ background: 'var(--glass-bg)' }}>
                    <div className="flex gap-3 items-start">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 shadow-sm"
                        style={{ background: i === 0 ? 'rgba(234,179,8,0.15)' : 'rgba(34,197,94,0.10)',
                          border: `1px solid ${i === 0 ? 'rgba(234,179,8,0.3)' : 'rgba(34,197,94,0.2)'}`,
                          color: i === 0 ? '#eab308' : 'var(--green)' }}>
                        {i === 0 ? '★' : `#${i + 1}`}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-bold text-agro-100 truncate">{s.name}</div>
                        <div className="text-[11px] text-agro-500 flex items-center gap-1 mt-1 truncate">
                          <MapPin size={10} className="shrink-0" /> {s.address || 'Nearby'}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between mt-1 pl-11">
                      {s.rating > 0 ? (
                        <div className="flex items-center gap-0.5">
                          {[1,2,3,4,5].map(star => (
                            <Star key={star} size={10}
                              fill={star <= Math.round(s.rating) ? '#eab308' : 'none'}
                              stroke="#eab308" strokeWidth={1.5} />
                          ))}
                          <span className="text-xs font-bold text-amber-400 ml-1.5">{s.rating.toFixed(1)}</span>
                        </div>
                      ) : <div />}
                      
                      <a href={`https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lon}&destination_place_id=${s.place_id}`}
                        target="_blank" rel="noreferrer"
                        className="text-[10px] font-bold uppercase tracking-wider px-3 py-1.5 rounded-lg transition-all hover:bg-[var(--green)] hover:text-black"
                        style={{ background: 'rgba(34,197,94,0.15)', color: 'var(--green)', textDecoration: 'none' }}>
                        Route
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
