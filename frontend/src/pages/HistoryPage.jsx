import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../App'
import { getHistory } from '../api/api'
import { Scan, Clock, MapPin, Filter, Search, ChevronRight, Leaf, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

const SEV_CLASS = { Low: 'badge-low', Moderate: 'badge-moderate', High: 'badge-high', Critical: 'badge-critical' }
const SEV_ORDER = { Critical: 0, High: 1, Moderate: 2, Low: 3 }

function groupByDate(scans) {
  const groups = {}
  scans.forEach(s => {
    const day = new Date(s.timestamp).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })
    if (!groups[day]) groups[day] = []
    groups[day].push(s)
  })
  return groups
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const { setActiveScan } = useApp()
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterSev, setFilterSev] = useState('All')

  useEffect(() => {
    getHistory(200)
      .then(data => { setScans(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = scans.filter(s => {
    const matchSearch = !search || s.crop?.toLowerCase().includes(search.toLowerCase()) ||
      s.result?.disease?.toLowerCase().includes(search.toLowerCase()) ||
      s.field_name?.toLowerCase().includes(search.toLowerCase())
    const matchSev = filterSev === 'All' || (s.result?.severity_level || s.result?.severity) === filterSev
    return matchSearch && matchSev
  })

  const grouped = groupByDate(filtered)

  if (loading) {
    return (
      <div className="p-6 space-y-4">
        <div className="h-8 w-32 bg-surface-200 rounded animate-pulse" />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-20 bg-surface-100 rounded-2xl animate-pulse" />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-agro-100">Scan History</h1>
          <p className="text-agro-600 text-sm mt-0.5">{scans.length} total scans recorded</p>
        </div>
        <button onClick={() => navigate('/scan')} className="btn-primary">
          <Scan size={14} /> New Scan
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1 min-w-48 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-agro-600" />
          <input
            className="input pl-9 text-sm py-2"
            placeholder="Search crop, disease, field..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={13} className="text-agro-600" />
          {['All', 'Critical', 'High', 'Moderate', 'Low'].map(s => (
            <button
              key={s}
              onClick={() => setFilterSev(s)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                filterSev === s
                  ? s === 'All' ? 'bg-agro-700/40 border border-agro-600/50 text-agro-200'
                    : s === 'Critical' ? 'bg-red-900/40 border border-red-700/50 text-red-300'
                    : s === 'High' ? 'bg-orange-900/40 border border-orange-700/50 text-orange-300'
                    : s === 'Moderate' ? 'bg-yellow-900/40 border border-yellow-700/50 text-yellow-300'
                    : 'bg-agro-900/40 border border-agro-700/50 text-agro-300'
                  : 'bg-surface-200 border border-surface-border text-agro-600 hover:text-agro-400'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-agro-700 gap-3">
          <Leaf size={40} strokeWidth={1} />
          <div className="text-base font-medium text-agro-500">No scans found</div>
          <div className="text-sm">
            {scans.length === 0
              ? 'Run your first scan to see history here'
              : 'Try adjusting the search or filter'}
          </div>
          {scans.length === 0 && (
            <button onClick={() => navigate('/scan')} className="btn-primary mt-2">
              <Scan size={14} /> Run First Scan
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(grouped).map(([date, dayScans]) => (
            <div key={date}>
              <div className="flex items-center gap-3 mb-4">
                <div className="text-xs font-semibold text-agro-500 uppercase tracking-wider">{date}</div>
                <div className="flex-1 h-px bg-surface-border" />
                <div className="text-xs text-agro-700">{dayScans.length} scan{dayScans.length !== 1 ? 's' : ''}</div>
              </div>
              <div className="space-y-3">
                {dayScans.map((scan, i) => {
                  const r = scan.result || {}
                  const sev = r.severity_level || r.severity || 'Low'
                  const isAlert = (r.alerts?.length > 0) || sev === 'Critical' || sev === 'High'
                  return (
                    <div
                      key={scan.id}
                      className="timeline-item group"
                    >
                      {/* Timeline dot */}
                      <div className={clsx(
                        'absolute left-0 top-4 w-6 h-6 rounded-full flex items-center justify-center z-10',
                        sev === 'Critical' ? 'bg-red-900/60 border border-red-700/50' :
                        sev === 'High' ? 'bg-orange-900/60 border border-orange-700/50' :
                        sev === 'Moderate' ? 'bg-yellow-900/60 border border-yellow-700/50' :
                        'bg-agro-900/60 border border-agro-700/50'
                      )}>
                        {isAlert
                          ? <AlertTriangle size={11} className={sev === 'Critical' || sev === 'High' ? 'text-red-400' : 'text-yellow-400'} />
                          : <Scan size={11} className="text-agro-500" />
                        }
                      </div>

                      <div className={clsx(
                        'card p-4 hover:border-agro-700/40 transition-all group-hover:shadow-agro',
                        isAlert && 'border-red-900/30'
                      )}>
                        <div className="flex items-start gap-3">
                          {scan.image_path ? (
                            <img
                              src={`http://localhost:5001${scan.image_path}`}
                              className="w-14 h-14 rounded-xl object-cover border border-surface-border flex-shrink-0"
                              alt=""
                              onError={e => { e.target.style.display = 'none' }}
                            />
                          ) : (
                            <div className="w-14 h-14 rounded-xl bg-surface-200 border border-surface-border flex items-center justify-center flex-shrink-0">
                              <Leaf size={18} className="text-agro-600" />
                            </div>
                          )}

                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-sm font-semibold text-agro-200">{r.crop || scan.crop || 'Unknown'}</span>
                              {r.disease && r.disease !== 'Healthy' && (
                                <span className="text-xs text-agro-500">· {r.disease}</span>
                              )}
                              <span className={SEV_CLASS[sev] || 'badge-low'}>{sev}</span>
                              {r.risk && (
                                <span className={clsx('px-2 py-0.5 rounded-full text-[10px] font-medium border',
                                  r.risk === 'High' ? 'bg-red-950/50 text-red-400 border-red-800/40' :
                                  r.risk === 'Medium' ? 'bg-yellow-950/50 text-yellow-400 border-yellow-800/40' :
                                  'bg-agro-950/50 text-agro-500 border-agro-800/40'
                                )}>
                                  {r.risk} Risk
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-4 mt-2 flex-wrap">
                              <div className="flex items-center gap-1.5 text-xs text-agro-600">
                                <Clock size={11} />
                                {new Date(scan.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                              </div>
                              {scan.lat && scan.lon && (
                                <div className="flex items-center gap-1.5 text-xs text-agro-600">
                                  <MapPin size={11} />
                                  {parseFloat(scan.lat).toFixed(3)}°, {parseFloat(scan.lon).toFixed(3)}°
                                </div>
                              )}
                              {scan.field_name && (
                                <div className="flex items-center gap-1.5 text-xs text-agro-600">
                                  <Leaf size={11} />
                                  {scan.field_name}
                                </div>
                              )}
                            </div>

                            {r.recommendation && (
                              <div className="mt-2 text-xs text-agro-500 truncate">
                                → {r.recommendation}
                              </div>
                            )}

                            {r.alerts?.length > 0 && (
                              <div className="mt-2 flex items-center gap-1.5 text-xs text-red-400">
                                <AlertTriangle size={10} />
                                {r.alerts[0]}
                              </div>
                            )}
                          </div>

                          <div className="flex flex-col items-end gap-2 flex-shrink-0">
                            {r.health_score != null && (
                              <div className="text-center">
                                <div className="text-lg font-bold text-agro-300">{Math.round(r.health_score)}</div>
                                <div className="text-[9px] text-agro-700">health</div>
                              </div>
                            )}
                            <div className="flex gap-1.5">
                              <button
                                onClick={() => navigate(`/analysis/${scan.id}`)}
                                className="text-[10px] px-2 py-1 rounded-lg font-medium transition-all"
                                style={{ background:'var(--glass-bg2)', color:'var(--muted)', border:'1px solid var(--border)' }}>
                                📊 Analysis
                              </button>
                              <button
                                onClick={() => { setActiveScan({ result: scan.result }); navigate('/recommendation') }}
                                className="text-[10px] px-2 py-1 rounded-lg font-medium transition-all"
                                style={{ background:'rgba(34,197,94,0.1)', color:'var(--green)', border:'1px solid rgba(34,197,94,0.25)' }}>
                                💊 Advice
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}