import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../App'
import { useLang } from '../utils/LangContext'
import { t } from '../utils/i18n'
import { getDashboard, getHealthTrend, getFeedbackStats } from '../api/api'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts'
import {
  Activity, AlertTriangle, Scan, TrendingUp, TrendingDown,
  Minus, ChevronRight, Zap, Shield, MapPin, Clock, Leaf,
  Brain, RefreshCw, CalendarDays, BarChart2
} from 'lucide-react'
import clsx from 'clsx'

const SEV_COLOR = { Low:'#22c55e', Moderate:'#eab308', High:'#f97316', Critical:'#ef4444' }
const SEV_CLASS = { Low:'badge-low', Moderate:'badge-moderate', High:'badge-high', Critical:'badge-critical' }

// ─────────────────────────────────────────────────────────────────
//  StatCard
// ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, icon: Icon, color = 'agro', trend }) {
  const colorMap = {
    agro:   { bg:'bg-agro-900/50',   text:'text-agro-400',   bar:'bg-agro-500'   },
    red:    { bg:'bg-red-900/50',    text:'text-red-400',    bar:'bg-red-500'    },
    yellow: { bg:'bg-yellow-900/50', text:'text-yellow-400', bar:'bg-yellow-500' },
    blue:   { bg:'bg-blue-900/50',   text:'text-blue-400',   bar:'bg-blue-500'   },
  }
  const c = colorMap[color] || colorMap.agro
  return (
    <div className="stat-card">
      <div className={clsx('absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl', c.bar)} />
      <div className="flex items-start justify-between">
        <div className="text-xs text-agro-600 font-medium uppercase tracking-wide">{label}</div>
        <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center', c.bg)}>
          <Icon size={16} className={c.text} />
        </div>
      </div>
      <div className="text-3xl font-bold text-agro-100 mt-1">{value}</div>
      <div className="flex items-center gap-2 mt-1">
        {trend === 'up'     && <TrendingUp   size={12} className="text-red-400" />}
        {trend === 'down'   && <TrendingDown size={12} className="text-agro-400" />}
        {trend === 'stable' && <Minus        size={12} className="text-agro-600" />}
        <span className="text-xs text-agro-600">{sub}</span>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
//  Custom Recharts tooltip
// ─────────────────────────────────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="card px-3 py-2 shadow-xl text-xs" style={{ borderColor:'var(--border)' }}>
      <div className="text-agro-400 mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background:p.color }} />
          <span className="text-agro-300">{p.name}:</span>
          <span className="font-medium text-agro-100">
            {typeof p.value === 'number' ? `${(p.value * 100).toFixed(0)}%` : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
//  Dashboard
// ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { user, activeField, fields } = useApp()
  const { lang } = useLang()
  const navigate = useNavigate()

  const [dash,    setDash]    = useState(null)
  const [trend,   setTrend]   = useState([])
  const [loading, setLoading] = useState(true)
  const [fbStats, setFbStats] = useState(null)

  const refresh = useCallback(() => {
    setLoading(true)
    Promise.all([
      getDashboard(activeField).catch(() => null),
      getHealthTrend(activeField, 30).catch(() => []),
    ]).then(([d, t]) => {
      setDash(d)
      setTrend(Array.isArray(t) ? t : [])
      setLoading(false)
    })
    getFeedbackStats().then(setFbStats).catch(() => {})
  }, [activeField])

  useEffect(() => { refresh() }, [refresh])

  const field = fields?.find(f => f.id === activeField)

  const trendData = trend.map(t => ({
    day:      t.day?.slice(5),
    severity: parseFloat((t.avg_severity || 0).toFixed(3)),
    scans:    t.scan_count,
  }))

  const sevDist = dash?.severity_distribution || {}
  const sevData = Object.entries(sevDist).map(([sev, cnt]) => ({
    sev, cnt, color: SEV_COLOR[sev] || '#22c55e'
  }))

  const healthScore = dash?.farm_health_score ?? 0
  const healthColor = healthScore > 70 ? 'agro' : healthScore > 40 ? 'yellow' : 'red'

  if (loading) {
    return (
      <div className="p-8 space-y-6">
        <div className="h-8 w-48 rounded-lg animate-pulse" style={{ background:'var(--glass-bg2)' }} />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_,i) => (
            <div key={i} className="h-32 rounded-2xl animate-pulse" style={{ background:'var(--glass-bg2)' }} />
          ))}
        </div>
        <div className="h-64 rounded-2xl animate-pulse" style={{ background:'var(--glass-bg2)' }} />
      </div>
    )
  }

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">

      {/* ── Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-agro-100">
            {greeting}, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-agro-600 text-sm mt-0.5">
            {field ? `Viewing ${field.name}` : 'All fields overview'} · {new Date().toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long' })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => navigate('/schemes')} className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5">
            🏛️ Govt Schemes
          </button>
          <button onClick={refresh} disabled={loading}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5"
            title="Refresh dashboard">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
          <button onClick={() => navigate('/scan')} className="btn-primary">
            <Scan size={15} /> {t(lang,'run_new_scan')}
          </button>
        </div>
      </div>

      {/* ── Stats grid ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label={t(lang,'farm_health')} value={`${healthScore}%`}  sub="Overall health index"        icon={Activity}       color={healthColor} trend={healthScore>70?'stable':'up'} />
        <StatCard label={t(lang,'total_scans')} value={dash?.total_scans ?? 0}        sub="Scans in database"          icon={Scan}           color="blue"   trend="stable" />
        <StatCard label={t(lang,'critical_alerts')} value={dash?.critical_count ?? 0}   sub="Needs immediate action"     icon={AlertTriangle}  color={(dash?.critical_count ?? 0) > 0 ? 'red' : 'agro'} trend={(dash?.critical_count ?? 0) > 0 ? 'up' : 'stable'} />
        <StatCard label={t(lang,'avg_severity')} value={`${((dash?.average_severity_score ?? 0)*100).toFixed(0)}%`} sub="Across all scans" icon={Zap} color={(dash?.average_severity_score ?? 0)<0.4?'agro':'yellow'} trend="stable" />
      </div>

      {/* ── Feature Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          { icon:'📅', label:'Crop Calendar',    sub:'Phase-wise tasks & risk alerts', path:'/calendar',     color:'#3b82f6' },
          { icon:'📈', label:'Yield Estimator',  sub:'AI profit forecast with MSP',    path:'/yield',        color:'#22c55e' },
          { icon:'🐛', label:'Pest Alerts',      sub:'Live threat forecast by crop',   path:'/pest-alerts',  color:'#f97316' },
          { icon:'🏛️', label:'Govt Schemes',     sub:'Subsidies & insurance',          path:'/schemes',      color:'#8b5cf6' },
        ].map(f => (
          <button key={f.path} onClick={() => navigate(f.path)}
            className="card p-4 text-left flex items-center gap-3 hover:scale-[1.01] transition-all duration-200 group"
            style={{ borderLeft: `3px solid ${f.color}22` }}>
            <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 text-2xl transition-transform duration-200 group-hover:scale-110"
              style={{ background: `${f.color}18`, border: `1px solid ${f.color}30` }}>
              {f.icon}
            </div>
            <div>
              <div className="text-sm font-bold transition-colors duration-200" style={{ color: 'var(--on-surface)' }}>{f.label}</div>
              <div className="text-xs mt-0.5" style={{ color: 'var(--muted)' }}>{f.sub}</div>
            </div>
            <div className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity duration-200"
              style={{ color: f.color }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6"/></svg>
            </div>
          </button>
        ))}
      </div>

      {/* ── Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Health trend */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <div className="text-sm font-semibold text-agro-200">Farm Health Trend</div>
              <div className="text-xs text-agro-600 mt-0.5">Avg severity score · last 30 days</div>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-agro-600">
              <div className="w-2.5 h-2.5 rounded-full bg-agro-500" /> Severity Index
            </div>
          </div>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trendData} margin={{ top:5, right:5, left:-20, bottom:0 }}>
                <defs>
                  <linearGradient id="sevGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0}   />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" vertical={false} />
                <XAxis dataKey="day" tick={{ fill:'var(--muted)', fontSize:11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill:'var(--muted)', fontSize:11 }} axisLine={false} tickLine={false} domain={[0,1]} tickFormatter={v=>`${(v*100).toFixed(0)}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="severity" name="Severity" stroke="#22c55e" strokeWidth={2} fill="url(#sevGrad)" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex flex-col items-center justify-center gap-3 text-agro-700">
              <Activity size={32} strokeWidth={1} />
              <div className="text-sm">No trend data yet. Run your first scan!</div>
              <button onClick={() => navigate('/scan')} className="btn-primary text-xs py-2">
                <Scan size={13} /> Run Scan
              </button>
            </div>
          )}
        </div>

        {/* Severity distribution */}
        <div className="card p-5">
          <div className="text-sm font-semibold text-agro-200 mb-1">Severity Distribution</div>
          <div className="text-xs text-agro-600 mb-5">All scans breakdown</div>
          {sevData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={sevData} margin={{ top:0, right:0, left:-30, bottom:0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.1)" vertical={false} />
                  <XAxis dataKey="sev" tick={{ fill:'var(--muted)', fontSize:10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill:'var(--muted)', fontSize:10 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="cnt" name="Scans" radius={[4,4,0,0]}>
                    {sevData.map((d,i) => <Cell key={i} fill={d.color} fillOpacity={0.85} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 space-y-2">
                {sevData.map(d => (
                  <div key={d.sev} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background:d.color }} />
                      <span className="text-agro-400">{d.sev}</span>
                    </div>
                    <span className="font-medium text-agro-200">{d.cnt} scans</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-40 flex items-center justify-center text-agro-700 text-sm">
              No scan data yet
            </div>
          )}
        </div>
      </div>

      {/* ── Alerts + Recent scans ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Alerts */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-agro-200 flex items-center gap-2">
              <AlertTriangle size={14} className="text-red-400" /> Recent Alerts
            </div>
            <span className="text-xs text-agro-600">{dash?.recent_alerts?.length ?? 0} active</span>
          </div>
          <div className="space-y-3">
            {(dash?.recent_alerts ?? []).length === 0 ? (
              <div className="flex flex-col items-center py-6 text-agro-700 gap-2">
                <Shield size={24} strokeWidth={1} />
                <span className="text-sm">No active alerts. Farm looks healthy!</span>
              </div>
            ) : dash.recent_alerts.slice(0,5).map((a,i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl"
                style={{ background:'rgba(239,68,68,0.06)', border:'1px solid rgba(239,68,68,0.2)' }}>
                <AlertTriangle size={13} className="text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-red-300 truncate">{a.crop}</div>
                  <div className="text-xs text-agro-500 mt-0.5 leading-relaxed line-clamp-2">{a.alert}</div>
                  <div className="text-[10px] text-agro-700 mt-1 flex items-center gap-1">
                    <Clock size={10} /> {new Date(a.timestamp).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent scans */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-agro-200">Recent Scans</div>
            <button onClick={() => navigate('/history')}
              className="text-xs text-agro-500 hover:text-agro-300 flex items-center gap-1 transition-colors">
              View all <ChevronRight size={12} />
            </button>
          </div>
          <div className="space-y-2">
            {(dash?.recent_scans ?? []).length === 0 ? (
              <div className="flex flex-col items-center py-6 text-agro-700 gap-2">
                <Scan size={24} strokeWidth={1} />
                <span className="text-sm">No scans yet. Run your first scan!</span>
                <button onClick={() => navigate('/scan')} className="btn-primary text-xs py-1.5 mt-1">
                  <Scan size={12} /> Start scanning
                </button>
              </div>
            ) : dash.recent_scans.map(s => (
              <div key={s.id} onClick={() => navigate(`/analysis/${s.id}`)}
                className="flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors group"
                onMouseEnter={e => e.currentTarget.style.background='var(--glass-bg2)'}
                onMouseLeave={e => e.currentTarget.style.background='transparent'}>
                {s.image_path ? (
                  <img src={`http://localhost:5001${s.image_path}`}
                    className="w-10 h-10 rounded-lg object-cover border flex-shrink-0"
                    style={{ borderColor:'var(--border)' }} alt=""
                    onError={e => { e.target.style.display='none' }} />
                ) : (
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                    <Leaf size={14} className="text-agro-600" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-agro-200 truncate">{s.crop || 'Unknown crop'}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={SEV_CLASS[s.result?.severity_level] || 'badge-low'}>
                      {s.result?.severity_level || 'Low'}
                    </span>
                    <span className="text-[10px] text-agro-700 flex items-center gap-1">
                      <Clock size={9} /> {new Date(s.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <ChevronRight size={14} className="text-agro-700 group-hover:text-agro-400 flex-shrink-0 transition-colors" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Fields overview ── */}
      {fields?.length > 0 && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-agro-200">Your Fields</div>
            <button onClick={() => navigate('/fields')}
              className="text-xs text-agro-500 hover:text-agro-300 flex items-center gap-1 transition-colors">
              Manage <ChevronRight size={12} />
            </button>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {fields.map(f => (
              <div key={f.id} onClick={() => navigate('/fields')}
                className="p-3 rounded-xl cursor-pointer transition-colors"
                style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}
                onMouseEnter={e => e.currentTarget.style.borderColor='var(--border-hi)'}
                onMouseLeave={e => e.currentTarget.style.borderColor='var(--border)'}>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 rounded-full" style={{ background:'var(--green)' }} />
                  <div className="text-xs font-medium text-agro-200 truncate">{f.name}</div>
                </div>
                {f.crop_type && <div className="text-[10px] text-agro-600 truncate">{f.crop_type}</div>}
                {f.area_acres > 0 && <div className="text-[10px] text-agro-700">{f.area_acres} acres</div>}
                {f.location && (
                  <div className="text-[10px] text-agro-700 flex items-center gap-1 mt-1">
                    <MapPin size={9} /> {f.location}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Adaptive Learning Loop (Patent Feature VII) ── */}
      {fbStats && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-agro-200 flex items-center gap-2">
              <Brain size={15} className="text-purple-400" />
              AI Self-Learning Status
              <span className="text-[10px] text-agro-600 font-normal">· System improves when you confirm/correct diagnoses</span>
            </div>
            <span className="text-xs text-agro-600">
              {fbStats.total} diagnosis{fbStats.total !== 1 ? 'es' : ''} confirmed by farmers
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {[
              { label:'Total Feedback',  value: fbStats.total,         color:'var(--green)'  },
              { label:'Correct',         value: fbStats.correct,       color:'var(--green)'  },
              { label:'Accuracy',        value:`${fbStats.accuracy}%`, color: fbStats.accuracy >= 70 ? 'var(--green)' : 'var(--amber)' },
              { label:'Model Status', value: fbStats.total >= 5 ? '✅ Self-learning' : '⏳ Warming up', color: fbStats.total >= 5 ? 'var(--green)' : 'var(--amber)' },
            ].map(({ label, value, color }) => (
              <div key={label} className="text-center p-3 rounded-xl"
                style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                <div className="text-xl font-bold font-display" style={{ color }}>{value}</div>
                <div className="text-[10px] text-agro-600 mt-0.5">{label}</div>
              </div>
            ))}
          </div>

          {/* Adaptive weights bars */}
          {fbStats.weights && Object.keys(fbStats.weights).length > 0 && (
            <div>
              <div className="text-xs font-semibold text-agro-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <RefreshCw size={10} /> Treatment Preference Weights (auto-updated)
              </div>
              <div className="space-y-1.5">
                {Object.entries(fbStats.weights).map(([action, weight]) => (
                  <div key={action} className="flex items-center gap-3">
                    <span className="text-xs text-agro-500 w-28 capitalize">{action.replace('_',' ')}</span>
                    <div className="flex-1 h-1.5 rounded-full overflow-hidden"
                      style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                      <div className="h-full rounded-full transition-all duration-700"
                        style={{
                          width:`${Math.round(weight*100)}%`,
                          background: weight>0.6?'var(--green)':weight>0.4?'var(--amber)':'var(--danger)'
                        }} />
                    </div>
                    <span className="text-xs font-mono text-agro-400 w-10 text-right">
                      {(weight*100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {fbStats.total < 5 && (
            <p className="text-xs text-agro-700 mt-3 text-center">
              Confirm {5 - fbStats.total} more scan diagnosis{5-fbStats.total!==1?'es':''} to activate AI self-learning
            </p>
          )}
        </div>
      )}

    </div>
  )
}
