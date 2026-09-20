import React, { useState, useEffect, useCallback } from 'react'
import { getSuppliers } from '../api/api'
import { getLastResult } from '../utils/storage'
import { useApp } from '../App'
import {
  Store, MapPin, Star, Navigation, RefreshCw,
  Phone, ExternalLink, Loader, SearchX, Filter, Edit2, Search
} from 'lucide-react'
import toast from 'react-hot-toast'

const CATEGORIES = ['All', 'Pesticide', 'Fertilizer', 'Seeds', 'Equipment', 'Krishi Kendra']
const RADII = [
  { label: '5 km',  value: 5000  },
  { label: '10 km', value: 10000 },
  { label: '15 km', value: 15000 },
  { label: '25 km', value: 25000 },
  { label: '50 km', value: 50000 },
]

export default function ShopsPage() {
  const { activeScan } = useApp()
  const [shops,      setShops]      = useState([])
  const [loading,    setLoading]    = useState(false)
  const [lat,        setLat]        = useState(null)
  const [lon,        setLon]        = useState(null)
  const [manualLat,  setManualLat]  = useState('')
  const [manualLon,  setManualLon]  = useState('')
  const [showManual, setShowManual] = useState(false)
  const [radius,     setRadius]     = useState(15000)
  const [filter,     setFilter]     = useState('All')
  const [searched,   setSearched]   = useState(false)
  const [locErr,     setLocErr]     = useState(false)

  // Pull lat/lon from last scan result if available
  useEffect(() => {
    const r = activeScan?.result || getLastResult()
    if (r?.lat && r?.lon) { setLat(String(r.lat)); setLon(String(r.lon)) }
  }, [activeScan])

  const detect = useCallback(async () => {
    setLoading(true); setLocErr(false)

    const applyCoords = (la, lo) => {
      setLat(la); setLon(lo)
      setManualLat(la); setManualLon(lo)
      setLoading(false)
    }

    const tryIP = async () => {
      try {
        const r = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(6000) })
        const d = await r.json()
        if (d.latitude && d.longitude) {
          applyCoords(String(parseFloat(d.latitude).toFixed(6)), String(parseFloat(d.longitude).toFixed(6)))
          toast('📡 Using approximate IP location', { icon: 'ℹ️', duration: 4000 })
          return true
        }
      } catch {}
      try {
        const r2 = await fetch('http://ip-api.com/json/', { signal: AbortSignal.timeout(6000) })
        const d2 = await r2.json()
        if (d2.status === 'success') {
          applyCoords(String(parseFloat(d2.lat).toFixed(6)), String(parseFloat(d2.lon).toFixed(6)))
          toast('📡 Using approximate IP location', { icon: 'ℹ️', duration: 4000 })
          return true
        }
      } catch {}
      return false
    }

    if (!navigator.geolocation) {
      const ok = await tryIP()
      if (!ok) { setLoading(false); setLocErr(true); toast.error('Could not detect location. Enter manually.') }
      return
    }

    const tryGeo = (highAccuracy, timeout) => new Promise((res, rej) =>
      navigator.geolocation.getCurrentPosition(res, rej, { enableHighAccuracy: highAccuracy, timeout, maximumAge: 60000 })
    )

    try {
      const pos = await tryGeo(true, 10000)
      applyCoords(pos.coords.latitude.toFixed(6), pos.coords.longitude.toFixed(6))
      toast.success('📍 Location detected!')
    } catch {
      try {
        const pos2 = await tryGeo(false, 15000)
        applyCoords(pos2.coords.latitude.toFixed(6), pos2.coords.longitude.toFixed(6))
        toast.success('📍 Location detected!')
      } catch (e2) {
        if (e2?.code === 1) toast('Location permission blocked — trying IP…', { icon: '🔄', duration: 2000 })
        const ok = await tryIP()
        if (!ok) {
          setLocErr(true); setLoading(false)
          toast.error('Could not detect location. Use Manual input below.', { duration: 5000 })
        }
      }
    }
  }, [])

  const applyManual = () => {
    const la = parseFloat(manualLat)
    const lo = parseFloat(manualLon)
    if (isNaN(la) || isNaN(lo) || la < -90 || la > 90 || lo < -180 || lo > 180) {
      return toast.error('Enter valid latitude (±90) and longitude (±180)')
    }
    setLat(String(la.toFixed(6)))
    setLon(String(lo.toFixed(6)))
    setShowManual(false)
    toast.success('Location updated!')
  }

  const search = useCallback(async () => {
    if (!lat || !lon) return toast.error('Please allow location access first')
    setLoading(true); setSearched(true)
    try {
      const data = await getSuppliers(lat, lon, radius)
      setShops(Array.isArray(data) ? data : [])
      if (!data?.length) {
        toast(
          `No shops found within ${RADII.find(r => r.value === radius)?.label}. ` +
          'Try increasing the search radius or open Google Maps manually.',
          { icon: '📍', duration: 5000 }
        )
      }
    } catch {
      toast.error('Could not fetch shops — check your Google Places API key in backend/.env')
      setShops([])
    } finally { setLoading(false) }
  }, [lat, lon, radius])

  // Auto-search if we have location from scan
  useEffect(() => {
    if (lat && lon && !searched) search()
  }, [lat, lon])

  const filtered = filter === 'All' ? shops : shops.filter(s =>
    (s.types || []).some(t => t.toLowerCase().includes(filter.toLowerCase())) ||
    s.name?.toLowerCase().includes(filter.toLowerCase())
  )

  // Fallback: open Google Maps search directly
  const openGoogleMaps = () => {
    if (!lat || !lon) return toast.error('Need location first')
    const query = encodeURIComponent('agricultural shop pesticide fertilizer near me')
    window.open(`https://www.google.com/maps/search/${query}/@${lat},${lon},13z`, '_blank')
  }

  return (
    <div className="page-container space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold font-display text-agro-100 flex items-center gap-2">
            <Store size={20} className="text-agro-400" /> Nearby Agri-Shops
          </h1>
          <p className="text-xs text-agro-600 mt-0.5">
            Pesticide stores, fertilizer shops & krishi kendras near you
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={detect} disabled={loading}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5">
            <Navigation size={12} /> Detect Location
          </button>
          <button onClick={() => setShowManual(v => !v)}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5">
            <Edit2 size={12} /> Manual
          </button>
          <button onClick={search} disabled={loading || !lat}
            className="btn-primary text-xs py-2 px-3 flex items-center gap-1.5">
            {loading ? <Loader size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            Search
          </button>
        </div>
      </div>

      {/* Manual location input */}
      {showManual && (
        <div className="card p-4 space-y-3">
          <div className="text-xs font-semibold text-agro-300">Enter Location Manually</div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-agro-600 mb-1 block">Latitude</label>
              <input className="input-field text-sm" placeholder="e.g. 16.4674"
                value={manualLat} onChange={e => setManualLat(e.target.value)} />
            </div>
            <div>
              <label className="text-[10px] text-agro-600 mb-1 block">Longitude</label>
              <input className="input-field text-sm" placeholder="e.g. 80.5082"
                value={manualLon} onChange={e => setManualLon(e.target.value)} />
            </div>
          </div>
          <p className="text-[10px] text-agro-700">
            Find your coordinates: open Google Maps → long press your location → copy the numbers shown
          </p>
          <button onClick={applyManual} className="btn-primary text-xs py-2">Apply Location</button>
        </div>
      )}

      {/* Location + radius row */}
      <div className="flex items-center gap-3 flex-wrap p-3 rounded-xl"
        style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
        <MapPin size={14} className={lat ? 'text-green-400' : 'text-agro-600'} />
        {lat && lon ? (
          <span className="text-xs text-agro-300 flex-1">
            📍 <span className="font-mono">{parseFloat(lat).toFixed(4)}°N, {parseFloat(lon).toFixed(4)}°E</span>
          </span>
        ) : (
          <span className="text-xs text-agro-600 flex-1">
            {locErr ? '⚠️ Location denied — try Manual input' : 'Click "Detect Location" or enter manually'}
          </span>
        )}
        {/* Radius picker */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] text-agro-600">Radius:</span>
          <select className="input-field text-xs py-1 px-2" value={radius}
            onChange={e => setRadius(Number(e.target.value))}>
            {RADII.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
      </div>

      {/* Category filter */}
      {shops.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {CATEGORIES.map(cat => (
            <button key={cat} onClick={() => setFilter(cat)}
              className="px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all border"
              style={{
                background: filter === cat ? 'rgba(34,197,94,0.15)' : 'var(--glass-bg2)',
                borderColor: filter === cat ? 'rgba(34,197,94,0.4)' : 'var(--border)',
                color: filter === cat ? 'var(--green)' : 'var(--muted)',
              }}>
              {cat}
            </button>
          ))}
          <span className="text-[10px] text-agro-700 self-center ml-1">{filtered.length} shops</span>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1,2,3,4].map(i => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="flex gap-3">
                <div className="w-12 h-12 rounded-xl bg-agro-800/40" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 bg-agro-800/40 rounded w-2/3" />
                  <div className="h-2 bg-agro-800/30 rounded w-1/2" />
                  <div className="h-2 bg-agro-800/20 rounded w-1/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state with alternatives */}
      {!loading && searched && filtered.length === 0 && (
        <div className="card p-8 flex flex-col items-center gap-4 text-center">
          <SearchX size={32} className="text-agro-700" strokeWidth={1} />
          <div className="text-sm text-agro-400 font-semibold">No shops found in {RADII.find(r => r.value === radius)?.label}</div>
          <div className="text-xs text-agro-600 max-w-xs leading-relaxed">
            Either your <code className="bg-agro-800/50 px-1 rounded">GOOGLE_PLACES_API_KEY</code> is not set,
            or there are no registered agri-shops in this radius.
          </div>
          <div className="flex gap-2 flex-wrap justify-center">
            <button onClick={() => { setRadius(50000); setTimeout(search, 100) }}
              className="btn-secondary text-xs py-2 px-3">
              🔍 Try 50 km radius
            </button>
            <button onClick={openGoogleMaps}
              className="btn-primary text-xs py-2 px-3 flex items-center gap-1.5">
              <ExternalLink size={11} /> Open Google Maps
            </button>
          </div>
          <p className="text-[10px] text-agro-700">
            Google Maps will show all agri-shops near your location
          </p>
        </div>
      )}

      {/* Shop cards */}
      {!loading && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {filtered.map((s, i) => (
            <div key={i} className="card p-4 flex gap-3 hover:border-green-500/30 transition-all"
              style={{ border: '1px solid var(--border)' }}>
              <div className="w-12 h-12 rounded-xl flex flex-col items-center justify-center shrink-0 text-center"
                style={{
                  background: i === 0 ? 'rgba(234,179,8,0.12)' : 'rgba(34,197,94,0.10)',
                  border: `1px solid ${i === 0 ? 'rgba(234,179,8,0.25)' : 'rgba(34,197,94,0.18)'}`,
                }}>
                <span className="text-lg">{i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '🏪'}</span>
                <span className="text-[9px] font-bold mt-0.5"
                  style={{ color: i === 0 ? '#eab308' : 'var(--green)' }}>#{i+1}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-agro-100 leading-tight">{s.name}</div>
                <div className="flex items-start gap-1 mt-1">
                  <MapPin size={9} className="text-agro-600 mt-0.5 shrink-0" />
                  <span className="text-[11px] text-agro-500 leading-relaxed">{s.address || 'Nearby'}</span>
                </div>
                {s.rating > 0 && (
                  <div className="flex items-center gap-1 mt-1.5">
                    {[1,2,3,4,5].map(star => (
                      <Star key={star} size={10}
                        fill={star <= Math.round(s.rating) ? '#eab308' : 'none'}
                        stroke="#eab308" strokeWidth={1.5} />
                    ))}
                    <span className="text-[10px] text-amber-400 font-semibold">{s.rating.toFixed(1)}</span>
                  </div>
                )}
                {s.types?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {s.types.slice(0,3).map(type => (
                      <span key={type} className="text-[9px] px-1.5 py-0.5 rounded-full capitalize"
                        style={{ background:'var(--glass-bg2)', color:'var(--muted)', border:'1px solid var(--border)' }}>
                        {type.replace(/_/g,' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex flex-col items-end justify-between shrink-0 gap-2">
                {s.open_now !== undefined && (
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    s.open_now ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'
                  }`}>
                    {s.open_now ? '● Open' : '● Closed'}
                  </span>
                )}
                <a href={`https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lon}`}
                  target="_blank" rel="noreferrer"
                  className="flex items-center gap-1 text-[10px] font-semibold px-2.5 py-1.5 rounded-lg"
                  style={{ background:'rgba(34,197,94,0.12)', color:'var(--green)', border:'1px solid rgba(34,197,94,0.2)', textDecoration:'none' }}>
                  <Navigation size={9} /> Directions
                </a>
                <a href={`https://www.google.com/maps/place/?q=place_id:${s.place_id}`}
                  target="_blank" rel="noreferrer"
                  className="flex items-center gap-1 text-[10px] text-agro-600 hover:text-agro-300"
                  style={{ textDecoration:'none' }}>
                  <ExternalLink size={9} /> Maps
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-[10px] text-agro-700 text-center">
        Powered by Google Places API · Sorted by rating
      </p>
    </div>
  )
}
