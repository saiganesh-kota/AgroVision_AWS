import React, { useState } from 'react'
import { TrendingUp, RefreshCw, BarChart2, Leaf, AlertTriangle, CheckCircle, Info } from 'lucide-react'

const CROP_BASE = {
  Wheat:     { base: 18, unit: 'q/acre', range: [8, 30],  inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Rice:      { base: 22, unit: 'q/acre', range: [10, 40], inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Tomato:    { base: 80, unit: 'q/acre', range: [40, 140],inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Cotton:    { base: 8,  unit: 'q/acre', range: [3, 18],  inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Maize:     { base: 20, unit: 'q/acre', range: [10, 36], inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Soybean:   { base: 12, unit: 'q/acre', range: [6, 22],  inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Groundnut: { base: 10, unit: 'q/acre', range: [5, 20],  inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
  Sugarcane: { base: 250,unit: 'q/acre', range: [150, 400],inputs: ['area','rainfall','ph','fertilizer','irrigation'] },
}

const MARKET_PRICE = {
  Wheat: 2275, Rice: 2183, Tomato: 1200, Cotton: 6620,
  Maize: 1870, Soybean: 4600, Groundnut: 6377, Sugarcane: 315,
}

function Slider({ label, min, max, step=1, value, onChange, unit='', hint='' }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div>
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-agro-400 font-medium">{label}</span>
        <span className="font-bold" style={{ color:'var(--green)' }}>{value}{unit}</span>
      </div>
      <div className="relative h-2 rounded-full" style={{ background:'var(--glass-bg2)' }}>
        <div className="absolute left-0 top-0 h-2 rounded-full transition-all"
          style={{ width:`${pct}%`, background:'var(--green)' }} />
        <input type="range" min={min} max={max} step={step} value={value}
          onChange={e => onChange(Number(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer h-2" />
      </div>
      {hint && <div className="text-[10px] text-agro-700 mt-0.5">{hint}</div>}
    </div>
  )
}

export default function YieldEstimatorPage() {
  const [crop,        setCrop]        = useState('Wheat')
  const [area,        setArea]        = useState(2)
  const [ph,          setPh]          = useState(6.5)
  const [rainfall,    setRainfall]    = useState(80)
  const [fertilizer,  setFertilizer]  = useState(60)
  const [irrigation,  setIrrigation]  = useState(70)
  const [disease,     setDisease]     = useState(10) // severity from scan
  const [calculated,  setCalculated]  = useState(null)

  const cropData = CROP_BASE[crop] || CROP_BASE.Wheat
  const msp      = MARKET_PRICE[crop] || 2000

  function calculate() {
    const base = cropData.base

    // Factor multipliers — all capped at 1.0 for % display
    const phFactor        = Math.min(1.0, ph >= 6.0 && ph <= 7.5 ? 1.0 : ph >= 5.5 && ph <= 8.0 ? 0.88 : 0.74)
    const rainfallFactor  = Math.min(1.0, rainfall >= 60 && rainfall <= 120 ? 1.0 : rainfall >= 40 ? 0.85 : 0.70)
    const fertFactor      = Math.min(1.0, 0.65 + (fertilizer / 100) * 0.35)
    const irrigFactor     = Math.min(1.0, 0.70 + (irrigation / 100) * 0.30)
    const diseasePenalty  = Math.max(0.0, 1.0 - (disease / 100) * 0.65)

    const rawYield = base * phFactor * rainfallFactor * fertFactor * irrigFactor * diseasePenalty
    const totalYield = rawYield * area

    // Clamp to realistic range
    const perAcreYield  = Math.max(cropData.range[0], Math.min(cropData.range[1], rawYield))
    const totalYieldFin = perAcreYield * area

    const revenue       = totalYieldFin * msp / 100 // msp is per quintal
    const costPerAcre   = { Wheat:12000, Rice:15000, Tomato:25000, Cotton:18000,
                             Maize:10000, Soybean:12000, Groundnut:14000, Sugarcane:20000 }[crop] || 14000
    const totalCost     = costPerAcre * area
    const profit        = revenue - totalCost
    const roi           = ((profit / totalCost) * 100).toFixed(1)

    setCalculated({
      perAcreYield: perAcreYield.toFixed(1),
      totalYield:   totalYieldFin.toFixed(1),
      revenue:      Math.round(revenue),
      cost:         Math.round(totalCost),
      profit:       Math.round(profit),
      roi,
      factors: { ph: phFactor, rainfall: rainfallFactor, fert: fertFactor, irrig: irrigFactor, disease: diseasePenalty },
      msp,
    })
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-agro-100 flex items-center gap-2">
          <TrendingUp size={20} style={{ color:'var(--green)' }} /> Yield & Profit Estimator
        </h1>
        <p className="text-agro-600 text-sm mt-0.5">
          AI-powered yield forecast with MSP-based profit calculation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Inputs */}
        <div className="card p-5 space-y-5">
          {/* Crop select */}
          <div>
            <div className="text-xs font-semibold text-agro-400 uppercase tracking-wider mb-2">Select Crop</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.keys(CROP_BASE).map(c => (
                <button key={c} onClick={() => { setCrop(c); setCalculated(null) }}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
                  style={{
                    background:  crop===c ? 'var(--glass-bg2)' : 'transparent',
                    borderColor: crop===c ? 'var(--green)' : 'var(--border)',
                    color:       crop===c ? 'var(--on-surface)' : 'var(--muted)',
                  }}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          <Slider label="Field Area" min={0.5} max={20} step={0.5} value={area} onChange={v=>{setArea(v);setCalculated(null)}} unit=" acres" hint="Enter your field size in acres" />
          <Slider label="Soil pH" min={4.5} max={9} step={0.1} value={ph} onChange={v=>{setPh(v);setCalculated(null)}} hint="Optimal: 6.0–7.5" />
          <Slider label="Expected Rainfall" min={0} max={300} step={5} value={rainfall} onChange={v=>{setRainfall(v);setCalculated(null)}} unit=" mm" hint="Monthly average for growing season" />
          <Slider label="Fertilizer Application" min={0} max={100} step={5} value={fertilizer} onChange={v=>{setFertilizer(v);setCalculated(null)}} unit="%" hint="% of recommended dose applied" />
          <Slider label="Irrigation Coverage" min={0} max={100} step={5} value={irrigation} onChange={v=>{setIrrigation(v);setCalculated(null)}} unit="%" hint="% of water requirement met" />
          <Slider label="Disease Severity (from scan)" min={0} max={80} step={5} value={disease} onChange={v=>{setDisease(v);setCalculated(null)}} unit="%" hint="Set to 0 if no disease detected" />

          <button onClick={calculate} className="btn-primary w-full justify-center py-3 mt-2">
            <BarChart2 size={15} /> Calculate Yield & Profit
          </button>
        </div>

        {/* Results */}
        <div className="space-y-4">
          {!calculated ? (
            <div className="card p-8 flex flex-col items-center justify-center gap-3 text-center" style={{ minHeight:300 }}>
              <TrendingUp size={40} strokeWidth={1} style={{ color:'var(--border)' }} />
              <div className="text-sm text-agro-600">Adjust inputs and click Calculate</div>
            </div>
          ) : (
            <>
              {/* Yield card */}
              <div className="card p-5">
                <div className="text-xs font-semibold text-agro-600 uppercase tracking-wider mb-3">Estimated Yield</div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl text-center" style={{ background:'rgba(34,197,94,0.08)', border:'1px solid rgba(34,197,94,0.2)' }}>
                    <div className="text-2xl font-bold" style={{ color:'var(--green)' }}>{calculated.perAcreYield}</div>
                    <div className="text-xs text-agro-600 mt-0.5">{cropData.unit}</div>
                  </div>
                  <div className="p-3 rounded-xl text-center" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                    <div className="text-2xl font-bold text-agro-100">{calculated.totalYield}</div>
                    <div className="text-xs text-agro-600 mt-0.5">Total ({area} acres)</div>
                  </div>
                </div>
              </div>

              {/* P&L */}
              <div className="card p-5">
                <div className="text-xs font-semibold text-agro-600 uppercase tracking-wider mb-3">Profit & Loss (MSP: ₹{calculated.msp}/q)</div>
                <div className="space-y-2">
                  {[
                    { label:'Expected Revenue', val: `₹${calculated.revenue.toLocaleString()}`, color:'var(--green)' },
                    { label:'Total Cost',        val: `₹${calculated.cost.toLocaleString()}`,    color:'var(--muted)' },
                    { label:'Net Profit',        val: `₹${calculated.profit.toLocaleString()}`,  color: calculated.profit >= 0 ? 'var(--green)' : 'var(--danger)' },
                    { label:'ROI',               val: `${calculated.roi}%`,                       color: Number(calculated.roi) >= 20 ? 'var(--green)' : Number(calculated.roi) >= 0 ? 'var(--amber)' : 'var(--danger)' },
                  ].map(row => (
                    <div key={row.label} className="flex justify-between items-center py-2 border-b" style={{ borderColor:'var(--border)' }}>
                      <span className="text-xs text-agro-500">{row.label}</span>
                      <span className="text-sm font-bold" style={{ color: row.color }}>{row.val}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Factor breakdown */}
              <div className="card p-5">
                <div className="text-xs font-semibold text-agro-600 uppercase tracking-wider mb-3">Yield Factor Analysis</div>
                <div className="space-y-2">
                  {[
                    { label:'Soil pH',       val: calculated.factors.ph   },
                    { label:'Rainfall',      val: calculated.factors.rainfall },
                    { label:'Fertilizer',    val: calculated.factors.fert  },
                    { label:'Irrigation',    val: calculated.factors.irrig },
                    { label:'Disease Impact',val: calculated.factors.disease },
                  ].map(f => (
                    <div key={f.label}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-agro-500">{f.label}</span>
                        <span className="font-semibold" style={{ color: f.val >= 0.95 ? 'var(--green)' : f.val >= 0.80 ? 'var(--amber)' : 'var(--danger)' }}>
                          {(f.val * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="h-1.5 rounded-full" style={{ background:'var(--glass-bg2)' }}>
                        <div className="h-full rounded-full transition-all duration-700"
                          style={{ width:`${Math.min(100, f.val*100)}%`, background: f.val>=0.95?'var(--green)':f.val>=0.80?'var(--amber)':'var(--danger)' }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {calculated.profit < 0 && (
                <div className="p-4 rounded-xl flex items-start gap-3"
                  style={{ background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.25)' }}>
                  <AlertTriangle size={16} className="text-red-400 shrink-0 mt-0.5" />
                  <div className="text-xs text-red-300">
                    <strong>Loss predicted.</strong> Consider reducing inputs, treating disease, or switching to a higher-value crop.
                    Check Govt Schemes for subsidies that can reduce your cost.
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
