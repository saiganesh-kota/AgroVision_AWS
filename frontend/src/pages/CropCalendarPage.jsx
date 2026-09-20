import React, { useState, useEffect } from 'react'
import { useApp } from '../App'
import { useNavigate } from 'react-router-dom'
import { Calendar, ChevronLeft, ChevronRight, Leaf, Droplets, Sun, Wind, AlertTriangle, CheckCircle } from 'lucide-react'
import clsx from 'clsx'

// ── Crop calendar data ────────────────────────────────────────────────────────
const CROP_CALENDARS = {
  Wheat: {
    icon: '🌾', color: '#eab308',
    months: {
      Oct: { phase: 'Sowing',       tasks: ['Prepare field', 'Sow seeds 20–25 kg/acre', 'Apply basal fertilizer'], risk: 'low' },
      Nov: { phase: 'Germination',  tasks: ['First irrigation', 'Monitor germination', 'Apply 25kg DAP/acre'], risk: 'low' },
      Dec: { phase: 'Tillering',    tasks: ['Second irrigation', 'Apply urea 50kg/acre', 'Weed control'], risk: 'medium' },
      Jan: { phase: 'Jointing',     tasks: ['Third irrigation', 'Watch for rust disease', 'Apply fungicide if needed'], risk: 'high' },
      Feb: { phase: 'Heading',      tasks: ['Fourth irrigation', 'Monitor for aphids', 'Apply pesticide'], risk: 'medium' },
      Mar: { phase: 'Grain Fill',   tasks: ['Fifth irrigation', 'Stop irrigation 2 weeks before harvest'], risk: 'low' },
      Apr: { phase: 'Harvest',      tasks: ['Harvest at 20% moisture', 'Thresh and clean', 'Store in dry place'], risk: 'low' },
    }
  },
  Rice: {
    icon: '🌿', color: '#22c55e',
    months: {
      May:  { phase: 'Nursery',     tasks: ['Prepare seedbed', 'Sow pre-soaked seeds', 'Maintain water level'], risk: 'low' },
      Jun:  { phase: 'Transplant',  tasks: ['Transplant 25-day seedlings', 'Apply basal dose NPK', 'Maintain 5cm water'], risk: 'medium' },
      Jul:  { phase: 'Tillering',   tasks: ['Apply urea 30kg/acre', 'Weed control', 'Monitor stem borer'], risk: 'high' },
      Aug:  { phase: 'Panicle',     tasks: ['Apply potash', 'Watch for blast disease', 'Maintain water level'], risk: 'high' },
      Sep:  { phase: 'Grain Fill',  tasks: ['Reduce irrigation', 'Monitor for BPH', 'Apply foliar spray'], risk: 'medium' },
      Oct:  { phase: 'Harvest',     tasks: ['Harvest at 20–25% moisture', 'Dry to 14%', 'Store properly'], risk: 'low' },
    }
  },
  Tomato: {
    icon: '🍅', color: '#ef4444',
    months: {
      Jun: { phase: 'Nursery',      tasks: ['Prepare seedbed', 'Sow seeds in trays', 'Shade from direct sun'], risk: 'low' },
      Jul: { phase: 'Transplant',   tasks: ['Transplant 30-day seedlings', 'Apply NPK 6:12:12', 'Install drip'], risk: 'medium' },
      Aug: { phase: 'Vegetative',   tasks: ['Apply urea 10kg/acre', 'Stake plants', 'Watch for early blight'], risk: 'high' },
      Sep: { phase: 'Flowering',    tasks: ['Apply calcium spray', 'Monitor for fruit borer', 'Foliar potash'], risk: 'high' },
      Oct: { phase: 'Fruiting',     tasks: ['Harvest mature red fruits', 'Apply fungicide for late blight', 'Grade & pack'], risk: 'medium' },
      Nov: { phase: 'Main Harvest', tasks: ['Peak harvest period', 'Apply post-harvest treatment', 'Market fresh'], risk: 'low' },
    }
  },
  Cotton: {
    icon: '🌸', color: '#6366f1',
    months: {
      Apr: { phase: 'Sowing',       tasks: ['Treat seeds with fungicide', 'Sow at 18"×36" spacing', 'Ensure moisture'], risk: 'low' },
      May: { phase: 'Germination',  tasks: ['Gap fill within 10 days', 'First irrigation', 'Apply DAP'], risk: 'low' },
      Jun: { phase: 'Vegetative',   tasks: ['Apply urea', 'Monitor jassids', 'Spray neem oil'], risk: 'medium' },
      Jul: { phase: 'Squaring',     tasks: ['Watch for bollworm', 'Apply recommended pesticide', 'Irrigation'], risk: 'high' },
      Aug: { phase: 'Boll Opening', tasks: ['Pink bollworm monitoring', 'Stop nitrogen application', 'Defoliate'], risk: 'high' },
      Oct: { phase: 'Picking',      tasks: ['First picking mature bolls', 'Dry in sun', 'Grade cotton'], risk: 'low' },
      Nov: { phase: 'Harvest',      tasks: ['Final picking', 'Clear field', 'Sell at APMC'], risk: 'low' },
    }
  },
  Maize: {
    icon: '🌽', color: '#f59e0b',
    months: {
      Jun: { phase: 'Sowing',       tasks: ['Sow seeds 3–4 cm deep', 'Apply basal fertilizer', 'Ensure 65% moisture'], risk: 'low' },
      Jul: { phase: 'Vegetative',   tasks: ['Thinning to one plant/hill', 'Apply urea 40kg/acre', 'Weed control'], risk: 'medium' },
      Aug: { phase: 'Tasseling',    tasks: ['Critical irrigation', 'Watch for FAW', 'Detassel if hybrid'], risk: 'high' },
      Sep: { phase: 'Grain Fill',   tasks: ['Apply potash spray', 'Monitor ear rot', 'Reduce irrigation'], risk: 'medium' },
      Oct: { phase: 'Maturity',     tasks: ['Harvest at black layer stage', 'Dry to 13.5% moisture', 'Store dry'], risk: 'low' },
    }
  },
}

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const RISK_COLOR  = { low:'#22c55e', medium:'#eab308', high:'#ef4444' }
const RISK_LABEL  = { low:'✅ Low Risk', medium:'⚠️ Moderate', high:'🔴 High Risk' }

export default function CropCalendarPage() {
  const { lastResult } = useApp()
  const navigate = useNavigate()
  const [selectedCrop, setSelectedCrop] = useState(() => {
    const auto = lastResult?.crop_type || lastResult?.crop
    return CROP_CALENDARS[auto] ? auto : 'Wheat'
  })
  const [currentMonthIdx, setCurrentMonthIdx] = useState(new Date().getMonth())

  const cal    = CROP_CALENDARS[selectedCrop]
  const month  = MONTH_NAMES[currentMonthIdx]
  const phase  = cal?.months[month]

  // All months that have data for selected crop
  const activeMonths = cal ? Object.keys(cal.months) : []

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-agro-100 flex items-center gap-2">
          <Calendar size={20} style={{ color: 'var(--green)' }} /> Crop Calendar
        </h1>
        <p className="text-agro-600 text-sm mt-0.5">
          Seasonal farming guide with phase-wise tasks &amp; risk alerts
        </p>
      </div>

      {/* Crop selector */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(CROP_CALENDARS).map(([name, data]) => (
          <button key={name} onClick={() => setSelectedCrop(name)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all border"
            style={{
              background:   selectedCrop === name ? 'var(--glass-bg2)' : 'transparent',
              borderColor:  selectedCrop === name ? data.color : 'var(--border)',
              color:        selectedCrop === name ? 'var(--on-surface)' : 'var(--muted)',
            }}>
            {data.icon} {name}
          </button>
        ))}
      </div>

      {/* Month nav */}
      <div className="card p-4">
        <div className="flex items-center justify-between mb-4">
          <button onClick={() => setCurrentMonthIdx(i => (i + 11) % 12)}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
            style={{ background:'var(--glass-bg2)', color:'var(--muted)' }}>
            <ChevronLeft size={16} />
          </button>
          <div className="text-center">
            <div className="text-lg font-bold text-agro-100">{MONTH_NAMES[currentMonthIdx]} 2025</div>
            <div className="text-xs text-agro-600">
              {phase ? `Phase: ${phase.phase}` : 'No specific activity this month'}
            </div>
          </div>
          <button onClick={() => setCurrentMonthIdx(i => (i + 1) % 12)}
            className="w-8 h-8 rounded-lg flex items-center justify-center transition-colors"
            style={{ background:'var(--glass-bg2)', color:'var(--muted)' }}>
            <ChevronRight size={16} />
          </button>
        </div>

        {/* Month grid */}
        <div className="grid grid-cols-12 gap-1">
          {MONTH_NAMES.map((m, i) => {
            const hasData  = activeMonths.includes(m)
            const isCurrent = i === currentMonthIdx
            const mRisk    = cal?.months[m]?.risk
            return (
              <button key={m} onClick={() => setCurrentMonthIdx(i)}
                className="aspect-square rounded-lg flex flex-col items-center justify-center transition-all text-[10px] font-medium border"
                style={{
                  background:  isCurrent ? cal.color + '22' : hasData ? 'var(--glass-bg2)' : 'transparent',
                  borderColor: isCurrent ? cal.color : hasData ? 'var(--border-hi)' : 'var(--border)',
                  color:       isCurrent ? 'var(--on-surface)' : hasData ? 'var(--muted)' : 'var(--border)',
                }}>
                {m}
                {hasData && mRisk && (
                  <div className="w-1.5 h-1.5 rounded-full mt-0.5" style={{ background: RISK_COLOR[mRisk] }} />
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Phase detail */}
      {phase ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Tasks */}
          <div className="card p-5 space-y-3">
            <div className="flex items-center gap-2">
              <CheckCircle size={16} style={{ color: 'var(--green)' }} />
              <div className="text-sm font-semibold text-agro-200">Tasks for {month}</div>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                style={{ background: cal.color + '20', color: cal.color, border: `1px solid ${cal.color}40` }}>
                {phase.phase}
              </span>
            </div>
            <div className="space-y-2">
              {phase.tasks.map((t, i) => (
                <div key={i} className="flex items-start gap-2.5 p-2.5 rounded-lg"
                  style={{ background:'var(--glass-bg2)' }}>
                  <div className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                    style={{ background: cal.color + '30', color: cal.color }}>
                    {i+1}
                  </div>
                  <span className="text-xs text-agro-300">{t}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk & Tips */}
          <div className="card p-5 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} style={{ color: RISK_COLOR[phase.risk] }} />
              <div className="text-sm font-semibold text-agro-200">Risk Level</div>
            </div>
            <div className="p-4 rounded-xl text-center"
              style={{ background: RISK_COLOR[phase.risk] + '15', border: `1px solid ${RISK_COLOR[phase.risk]}40` }}>
              <div className="text-2xl font-bold" style={{ color: RISK_COLOR[phase.risk] }}>
                {RISK_LABEL[phase.risk]}
              </div>
              <div className="text-xs text-agro-600 mt-1">Disease pressure this month</div>
            </div>

            <div className="p-3 rounded-xl text-xs text-agro-400 leading-relaxed"
              style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
              💡 <strong className="text-agro-300">Scan tip:</strong> During {phase.phase} phase, take close-up photos
              of leaves weekly to catch early disease signs. Use AgroVision Scan for instant diagnosis.
            </div>

            <button onClick={() => navigate('/scan')}
              className="btn-primary w-full justify-center text-sm py-2.5">
              <Leaf size={14} /> Scan Crop Now
            </button>
          </div>
        </div>
      ) : (
        <div className="card p-8 text-center">
          <div className="text-4xl mb-3">{cal?.icon}</div>
          <div className="text-sm font-medium text-agro-400">
            No specific {selectedCrop} activity in {month}
          </div>
          <div className="text-xs text-agro-600 mt-1">
            Use this time for field preparation, soil testing, or equipment maintenance.
          </div>
        </div>
      )}

      {/* Year overview */}
      <div className="card p-5">
        <div className="text-sm font-semibold text-agro-200 mb-4">
          {cal?.icon} {selectedCrop} — Full Season Overview
        </div>
        <div className="space-y-2">
          {Object.entries(cal?.months || {}).map(([m, data]) => (
            <div key={m} className="flex items-center gap-3">
              <div className="w-8 text-xs text-agro-600 font-mono">{m}</div>
              <div className="flex-1 h-7 rounded-lg flex items-center px-3 text-xs font-medium"
                style={{ background: cal.color + '18', border: `1px solid ${cal.color}30`, color: 'var(--on-surface)' }}>
                {data.phase}
              </div>
              <div className="w-3 h-3 rounded-full shrink-0" style={{ background: RISK_COLOR[data.risk] }} />
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 mt-3 pt-3 border-t" style={{ borderColor:'var(--border)' }}>
          {Object.entries(RISK_COLOR).map(([level, color]) => (
            <div key={level} className="flex items-center gap-1.5 text-xs text-agro-600">
              <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              {level.charAt(0).toUpperCase() + level.slice(1)} Risk
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
