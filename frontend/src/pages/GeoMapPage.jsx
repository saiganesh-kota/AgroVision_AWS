import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getGeoPoints, getGeoHeatmap, getGeoForecast, getDiseaseHotspots, getZoneAlerts } from '../api/api'
import {
  ScanLine, MapPin, RefreshCw, Loader, X,
  Navigation, AlertTriangle, Activity,
  ChevronDown, Layers, Target, Info,
  BarChart2, Globe, Crosshair, Sprout, Store,
  Wheat, FlaskConical, Droplets, Warehouse, TreePine,
  ShoppingBag, Tractor, Thermometer, TrendingUp, TrendingDown,
  Minus, Zap, Eye, EyeOff, Flame
} from 'lucide-react'

/* ══════════════════════════════════════════════════════════════════════════
   SEVERITY CONFIG
══════════════════════════════════════════════════════════════════════════ */
const SEV = {
  Critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)',  border: 'rgba(239,68,68,0.4)',  glow: 'rgba(239,68,68,0.5)', hm: '#ef4444'  },
  High:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)', border: 'rgba(249,115,22,0.4)', glow: 'rgba(249,115,22,0.5)', hm: '#f97316' },
  Moderate: { color: '#eab308', bg: 'rgba(234,179,8,0.12)',  border: 'rgba(234,179,8,0.4)',  glow: 'rgba(234,179,8,0.5)', hm: '#eab308'  },
  Low:      { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  border: 'rgba(34,197,94,0.4)',  glow: 'rgba(34,197,94,0.5)', hm: '#22c55e'  },
}
const SEV_ORDER = ['Critical', 'High', 'Moderate', 'Low']

/* ══════════════════════════════════════════════════════════════════════════
   AGRICULTURE POI CONFIG
══════════════════════════════════════════════════════════════════════════ */
const AGRI_TYPES = {
  agri_shop:     { label: 'Agri Shop',        emoji: '🌾', color: '#84cc16', bg: 'rgba(132,204,22,0.15)', border: 'rgba(132,204,22,0.5)' },
  garden_centre: { label: 'Garden Centre',    emoji: '🌿', color: '#22c55e', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.5)'  },
  farm_shop:     { label: 'Farm Shop',        emoji: '🚜', color: '#a3e635', bg: 'rgba(163,230,53,0.15)', border: 'rgba(163,230,53,0.5)' },
  marketplace:   { label: 'Market / Mandi',   emoji: '🏪', color: '#fb923c', bg: 'rgba(251,146,60,0.15)', border: 'rgba(251,146,60,0.5)' },
  farmland:      { label: 'Farmland',         emoji: '🌱', color: '#4ade80', bg: 'rgba(74,222,128,0.12)', border: 'rgba(74,222,128,0.4)' },
  orchard:       { label: 'Orchard',          emoji: '🍎', color: '#f87171', bg: 'rgba(248,113,113,0.12)',border: 'rgba(248,113,113,0.4)'},
  greenhouse:    { label: 'Greenhouse',       emoji: '🏡', color: '#34d399', bg: 'rgba(52,211,153,0.12)', border: 'rgba(52,211,153,0.4)' },
  fertilizer:    { label: 'Fertilizer Store', emoji: '⚗️', color: '#a78bfa', bg: 'rgba(167,139,250,0.12)',border: 'rgba(167,139,250,0.4)'},
  water_point:   { label: 'Irrigation',       emoji: '💧', color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', border: 'rgba(56,189,248,0.4)' },
  storage:       { label: 'Storage / Silo',   emoji: '🏗️', color: '#fbbf24', bg: 'rgba(251,191,36,0.12)', border: 'rgba(251,191,36,0.4)' },
  nursery:       { label: 'Nursery',          emoji: '🌳', color: '#6ee7b7', bg: 'rgba(110,231,183,0.12)',border: 'rgba(110,231,183,0.4)'},
}

/* ══════════════════════════════════════════════════════════════════════════
   OVERPASS QUERY (agriculture only)
══════════════════════════════════════════════════════════════════════════ */
function buildOverpassQuery(south, west, north, east) {
  const bbox = `${south},${west},${north},${east}`
  return `[out:json][timeout:20];(node["shop"="agrarian"](${bbox});node["shop"="garden_centre"](${bbox});node["shop"="farm"](${bbox});node["shop"="seeds"](${bbox});node["shop"="fertilizer"](${bbox});node["amenity"="marketplace"]["marketplace"!="flea_market"](${bbox});node["landuse"="greenhouse"](${bbox});node["building"="greenhouse"](${bbox});node["man_made"="silo"](${bbox});node["man_made"="irrigation_terminal"](${bbox});node["landuse"="farmyard"](${bbox});node["landuse"="nursery"](${bbox});node["landuse"="orchard"](${bbox});way["landuse"="farmland"](${bbox});way["landuse"="orchard"](${bbox});way["landuse"="greenhouse_horticulture"](${bbox});way["landuse"="farmyard"](${bbox});way["landuse"="nursery"](${bbox});way["building"="greenhouse"](${bbox});way["man_made"="silo"](${bbox}););out center qt 60;`.trim()
}

function classifyPOI(el) {
  const t = el.tags || {}
  if (t.shop === 'agrarian' || t.shop === 'seeds' || t.shop === 'agrochemicals' || t.shop === 'pesticide') return 'agri_shop'
  if (t.shop === 'garden_centre') return 'garden_centre'
  if (t.shop === 'farm') return 'farm_shop'
  if (t.shop === 'fertilizer') return 'fertilizer'
  if (t.amenity === 'marketplace') return 'marketplace'
  if (t.landuse === 'greenhouse' || t.building === 'greenhouse' || t.landuse === 'greenhouse_horticulture') return 'greenhouse'
  if (t.man_made === 'silo' || t.man_made === 'storage_tank') return 'storage'
  if (t.man_made === 'irrigation_terminal') return 'water_point'
  if (t.landuse === 'farmyard' || t.landuse === 'farmland') return 'farmland'
  if (t.landuse === 'nursery') return 'nursery'
  if (t.landuse === 'orchard') return 'orchard'
  return null
}

function poiLatLon(el) {
  if (el.type === 'node') return [el.lat, el.lon]
  if (el.center) return [el.center.lat, el.center.lon]
  return null
}

const fmt6   = v => { const n = parseFloat(v); return isNaN(n) ? '—' : n.toFixed(6) }
const fmtDate = ts => ts ? new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'

/* ══════════════════════════════════════════════════════════════════════════
   MARKER HTML BUILDERS
══════════════════════════════════════════════════════════════════════════ */
function scanMarkerHtml(color, glow, severity, size = 16) {
  const pulse = severity === 'Critical'
    ? `<div style="position:absolute;inset:-4px;border-radius:50%;background:${glow};animation:ping 1.2s ease-in-out infinite;opacity:0.7"></div>` : ''
  return `<div style="position:relative;width:${size}px;height:${size}px;">${pulse}<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 0 8px ${glow};position:relative;z-index:1"></div></div>`
}

function hotspotMarkerHtml(rank, riskLevel) {
  const c = SEV[riskLevel] || SEV.High
  return `<div style="position:relative;width:28px;height:28px;">
    <div style="position:absolute;inset:-6px;border-radius:50%;background:${c.glow};animation:ping 1s ease-in-out infinite;opacity:0.8"></div>
    <div style="width:28px;height:28px;border-radius:50%;background:${c.color};border:2.5px solid white;box-shadow:0 0 12px ${c.glow};display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;color:white;position:relative;z-index:1">
      ${rank}
    </div>
  </div>`
}

function poiMarkerHtml(type) {
  const cfg = AGRI_TYPES[type] || { emoji: '🌾' }
  return `<div style="font-size:20px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.5))">${cfg.emoji}</div>`
}

function scanPopupHtml(p) {
  const sev   = SEV[p.severity_level] || SEV.Low
  const geoCs = p.geo_conditioned_severity != null ? parseFloat(p.geo_conditioned_severity).toFixed(1) : null
  const ndvi  = p.ndvi_proxy != null ? parseFloat(p.ndvi_proxy).toFixed(2) : null
  return `<div class="agro-popup">
    <div style="font-weight:700;font-size:13px;color:var(--on-surface);margin-bottom:6px">
      🌾 ${p.crop || 'Unknown Crop'}
    </div>
    <div style="font-size:11px;color:${sev.color};margin-bottom:8px;font-weight:600">
      ${p.disease || 'No disease'}
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:10px;margin-bottom:8px">
      <div style="background:var(--glass-bg2);padding:4px 6px;border-radius:6px">
        <div style="color:var(--muted)">Img Severity</div>
        <div style="color:var(--on-surface);font-weight:600">${parseFloat(p.severity||0).toFixed(1)}%</div>
      </div>
      ${geoCs ? `<div style="background:rgba(249,115,22,0.1);padding:4px 6px;border-radius:6px;border:1px solid rgba(249,115,22,0.25)">
        <div style="color:#f97316;font-size:9px;font-weight:600">GEO-COND SEV</div>
        <div style="color:#f97316;font-weight:700">${geoCs}%</div>
      </div>` : `<div style="background:var(--glass-bg2);padding:4px 6px;border-radius:6px">
        <div style="color:var(--muted)">Geo Risk</div>
        <div style="color:var(--on-surface);font-weight:600">${p.geo_risk||'Low'}</div>
      </div>`}
      <div style="background:var(--glass-bg2);padding:4px 6px;border-radius:6px">
        <div style="color:var(--muted)">Outbreak</div>
        <div style="color:var(--on-surface);font-weight:600">${parseFloat(p.outbreak_score||0).toFixed(3)}</div>
      </div>
      ${ndvi ? `<div style="background:rgba(34,197,94,0.08);padding:4px 6px;border-radius:6px">
        <div style="color:#22c55e;font-size:9px">NDVI Proxy</div>
        <div style="color:#22c55e;font-weight:600">${ndvi}</div>
      </div>` : `<div style="background:var(--glass-bg2);padding:4px 6px;border-radius:6px">
        <div style="color:var(--muted)">Spread Vel</div>
        <div style="color:var(--on-surface);font-weight:600">${parseFloat(p.spread_velocity||0).toFixed(3)}</div>
      </div>`}
    </div>
    ${p.cell_id ? `<div style="font-size:9px;color:var(--muted);margin-bottom:4px">📍 Cell: ${p.cell_id}</div>` : ''}
    <div style="font-size:9px;color:var(--muted)">${fmtDate(p.timestamp)}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:3px;font-size:9px;margin-top:4px;color:var(--muted)">
      <span>Lat: ${fmt6(p.lat)}</span><span>Lon: ${fmt6(p.lon)}</span>
    </div>
  </div>`
}

function poiPopupHtml(el, type) {
  const cfg = AGRI_TYPES[type] || { label: 'Place', emoji: '📍', color: '#22c55e' }
  const t   = el.tags || {}
  const name = t.name || cfg.label
  return `<div class="agro-popup">
    <div style="font-size:18px;margin-bottom:4px">${cfg.emoji}</div>
    <div style="font-weight:700;font-size:12px;color:var(--on-surface);margin-bottom:4px">${name}</div>
    <div style="font-size:10px;color:${cfg.color};font-weight:600;margin-bottom:6px">${cfg.label}</div>
    ${t['addr:street'] ? `<div style="font-size:10px;color:var(--muted)">${t['addr:street']}${t['addr:city'] ? ', ' + t['addr:city'] : ''}</div>` : ''}
    ${t.phone ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">📞 ${t.phone}</div>` : ''}
    ${t.opening_hours ? `<div style="font-size:10px;color:var(--muted);margin-top:2px">🕐 ${t.opening_hours}</div>` : ''}
  </div>`
}

/* ══════════════════════════════════════════════════════════════════════════
   FORECAST CHART (inline — no Recharts dependency)
══════════════════════════════════════════════════════════════════════════ */
function ForecastChart({ forecast }) {
  if (!forecast?.length) return null
  const max = Math.max(...forecast.map(d => d.risk_pct), 1)
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 72, padding: '0 4px' }}>
      {forecast.map((d, i) => {
        const h   = Math.max(4, (d.risk_pct / max) * 68)
        const cfg = SEV[d.risk_level] || SEV.Low
        return (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
            <div style={{ fontSize: 9, color: cfg.color, fontWeight: 700 }}>
              {d.risk_pct}%
            </div>
            <div style={{
              width: '100%', height: h, borderRadius: '4px 4px 0 0',
              background: `linear-gradient(to top, ${cfg.color}, ${cfg.color}88)`,
              boxShadow: `0 0 8px ${cfg.glow || cfg.color}55`,
              transition: 'height 0.4s ease',
            }} />
            <div style={{ fontSize: 8, color: 'var(--muted)', textAlign: 'center' }}>
              {new Date(d.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
            </div>
          </div>
        )
      })}
    </div>
  )
}

/* ══════════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
══════════════════════════════════════════════════════════════════════════ */
export default function GeoMapPage() {
  const navigate = useNavigate()

  // ── Core scan data ────────────────────────────────────────────────────────
  const [points,  setPoints]  = useState([])
  const [loading, setLoading] = useState(true)
  const [filter,  setFilter]  = useState('All')
  const [mapStyle,    setMapStyle]    = useState('standard')
  const [showTable,   setShowTable]   = useState(false)
  const [showCircles, setShowCircles] = useState(true)
  const [searchQ,     setSearchQ]     = useState('')

  // ── Agri POI layer ───────────────────────────────────────────────────────
  const [showAgri,    setShowAgri]    = useState(false)
  const [agriLoading, setAgriLoading] = useState(false)
  const [agriCount,   setAgriCount]   = useState(0)
  const [agriFilter,  setAgriFilter]  = useState('all')

  // ── Heat Map layer ───────────────────────────────────────────────────────
  const [showHeatmap,  setShowHeatmap]  = useState(false)
  const [heatmapData,  setHeatmapData]  = useState([])
  const [hmLoading,    setHmLoading]    = useState(false)

  // ── Disease Hotspots ─────────────────────────────────────────────────────
  const [showHotspots,  setShowHotspots]  = useState(false)
  const [hotspots,      setHotspots]      = useState([])
  const [hsLoading,     setHsLoading]     = useState(false)

  // ── 7-day Forecast panel ─────────────────────────────────────────────────
  const [forecastData,    setForecastData]    = useState(null)
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastPoint,   setForecastPoint]   = useState(null)  // point being forecasted

  // ── Zone Alerts ──────────────────────────────────────────────────────────
  const [zoneAlerts,    setZoneAlerts]    = useState([])
  const [alertsLoading, setAlertsLoading] = useState(false)
  const [showAlerts,    setShowAlerts]    = useState(true)

  // ── Refs ─────────────────────────────────────────────────────────────────
  const mapRef        = useRef(null)
  const mapInst       = useRef(null)
  const scanMarkersRef   = useRef([])
  const poiMarkersRef    = useRef([])
  const poiLayerRef      = useRef(null)
  const hmLayerRef       = useRef(null)    // heat map circles layer
  const hotspotLayerRef  = useRef(null)   // hotspot markers layer
  const circleLayerRef   = useRef(null)

  // ── Derived ───────────────────────────────────────────────────────────────
  const filtered = points.filter(p => {
    const matchSev = filter === 'All' || p.severity_level === filter
    const matchQ   = !searchQ || [p.crop, p.disease, p.severity_level].some(v => (v||'').toLowerCase().includes(searchQ.toLowerCase()))
    return matchSev && matchQ
  })

  const stats = {
    total:    points.length,
    critical: points.filter(p => p.severity_level === 'Critical').length,
    avgOut:   points.length ? (points.reduce((s, p) => s + (p.outbreak_score || 0), 0) / points.length).toFixed(3) : '0.000',
    hotCount: hotspots.length,
    heatCells:heatmapData.length,
    avgNdvi:  points.filter(p => p.ndvi_proxy != null).length
      ? (points.filter(p=>p.ndvi_proxy!=null).reduce((s,p)=>s+parseFloat(p.ndvi_proxy),0)/points.filter(p=>p.ndvi_proxy!=null).length).toFixed(2)
      : '—',
  }

  // ── Load scan geo points ──────────────────────────────────────────────────
  const load = useCallback(() => {
    setLoading(true)
    getGeoPoints().then(d => { setPoints(Array.isArray(d) ? d : []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  // ── Load zone alerts once points arrive ──────────────────────────────────
  useEffect(() => {
    if (!points.length) return
    const center = points[0]
    if (!center?.lat || !center?.lon) return
    setAlertsLoading(true)
    getZoneAlerts(center.lat, center.lon, 400)
      .then(d => { setZoneAlerts(Array.isArray(d) ? d : []) })
      .catch(() => {})
      .finally(() => setAlertsLoading(false))
  }, [points])

  // ── Build Leaflet map ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapRef.current || loading) return

    import('leaflet').then(mod => {
      const L = mod.default
      if (!document.querySelector('link[href*="leaflet"]')) {
        const css = document.createElement('link')
        css.rel = 'stylesheet'
        css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
        document.head.appendChild(css)
      }

      if (mapInst.current) { mapInst.current.remove(); mapInst.current = null }
      scanMarkersRef.current = []
      poiMarkersRef.current  = []

      const map = L.map(mapRef.current, { zoomControl: false, attributionControl: false })
      L.control.zoom({ position: 'topright' }).addTo(map)

      const tiles = {
        standard:  'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        terrain:   'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
      }
      L.tileLayer(tiles[mapStyle], { maxZoom: 19 }).addTo(map)

      const valid = points.filter(p => p.lat && p.lon)
      if (!valid.length) {
        map.setView([20.5937, 78.9629], 5)
      } else {
        map.setView([parseFloat(valid[0].lat), parseFloat(valid[0].lon)], 6)
      }

      // ── Scan markers ─────────────────────────────────────────────────────
      const scanLayer = L.layerGroup().addTo(map)
      circleLayerRef.current = L.layerGroup().addTo(map)

      valid.forEach(p => {
        const sev    = SEV[p.severity_level] || SEV.Low
        const icon   = L.divIcon({ html: scanMarkerHtml(sev.color, sev.glow, p.severity_level), className: '', iconSize: [16,16], iconAnchor: [8,8] })
        const marker = L.marker([parseFloat(p.lat), parseFloat(p.lon)], { icon })
          .bindPopup(scanPopupHtml(p), { maxWidth: 260 })
          .addTo(scanLayer)
        scanMarkersRef.current.push({ marker, p })

        if (showCircles) {
          const geoCs = p.geo_conditioned_severity ?? p.severity
          const radius = Math.max(3000, parseFloat(geoCs || p.severity || 0) * 400)
          L.circle([parseFloat(p.lat), parseFloat(p.lon)], {
            radius, color: sev.color, fillColor: sev.color, fillOpacity: 0.08, weight: 1, dashArray: '4,4'
          }).addTo(circleLayerRef.current)
        }
      })

      if (valid.length > 1) {
        try { map.fitBounds(L.latLngBounds(valid.map(p => [parseFloat(p.lat), parseFloat(p.lon)])), { padding: [40,40], maxZoom: 12 }) }
        catch {}
      }

      mapInst.current = map

      // Auto-load layers that are toggled on
      if (showAgri) setTimeout(() => fetchAgriPOIs(map, L), 500)
      if (showHeatmap) renderHeatmap(map, L, heatmapData)
      if (showHotspots) renderHotspots(map, L, hotspots)
    })

    return () => { if (mapInst.current) { mapInst.current.remove(); mapInst.current = null } }
  }, [points, loading, mapStyle, showCircles])  // eslint-disable-line

  // ── Agri POI fetch + render ───────────────────────────────────────────────
  const fetchAgriPOIs = useCallback((map, L) => {
    if (!map) return
    const b = map.getBounds()
    const q = buildOverpassQuery(b.getSouth(), b.getWest(), b.getNorth(), b.getEast())
    setAgriLoading(true)

    if (!poiLayerRef.current) poiLayerRef.current = L.layerGroup().addTo(map)
    else poiLayerRef.current.clearLayers()
    poiMarkersRef.current = []

    fetch('https://overpass-api.de/api/interpreter', { method:'POST', body:`data=${encodeURIComponent(q)}` })
      .then(r => r.json())
      .then(data => {
        const els = (data.elements || [])
        let count = 0
        els.forEach(el => {
          const type = classifyPOI(el)
          if (!type) return
          const ll = poiLatLon(el)
          if (!ll) return
          const cfg = AGRI_TYPES[type]
          const icon = L.divIcon({ html: poiMarkerHtml(type), className: '', iconSize: [24,24], iconAnchor: [12,12] })
          const marker = L.marker(ll, { icon })
            .bindPopup(poiPopupHtml(el, type), { maxWidth: 220 })
            .addTo(poiLayerRef.current)
          poiMarkersRef.current.push({ marker, type })
          count++
        })
        setAgriCount(count)
        setAgriLoading(false)
      })
      .catch(() => setAgriLoading(false))
  }, [])

  // ── Agri toggle ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapInst.current) return
    import('leaflet').then(mod => {
      const L = mod.default
      if (showAgri) {
        fetchAgriPOIs(mapInst.current, L)
      } else {
        if (poiLayerRef.current) { poiLayerRef.current.clearLayers(); setAgriCount(0) }
      }
    })
  }, [showAgri])  // eslint-disable-line

  // ── Agri sub-filter ───────────────────────────────────────────────────────
  useEffect(() => {
    poiMarkersRef.current.forEach(({ marker, type }) => {
      if (agriFilter === 'all' || type === agriFilter) {
        if (!mapInst.current?.hasLayer(marker)) marker.addTo(poiLayerRef.current)
      } else {
        if (poiLayerRef.current?.hasLayer(marker)) poiLayerRef.current.removeLayer(marker)
      }
    })
  }, [agriFilter])

  // ── Severity filter ───────────────────────────────────────────────────────
  useEffect(() => {
    scanMarkersRef.current.forEach(({ marker, p }) => {
      const show = filter === 'All' || p.severity_level === filter
      if (show && !mapInst.current?.hasLayer(marker)) marker.addTo(mapInst.current)
      else if (!show && mapInst.current?.hasLayer(marker)) mapInst.current?.removeLayer(marker)
    })
  }, [filter])

  // ── Heat Map load + render ────────────────────────────────────────────────
  const loadHeatmap = useCallback(() => {
    if (!points.length) return
    const c = points[0]
    setHmLoading(true)
    getGeoHeatmap(c.lat, c.lon, 500)
      .then(d => {
        const data = Array.isArray(d) ? d : []
        setHeatmapData(data)
        if (mapInst.current) {
          import('leaflet').then(mod => renderHeatmap(mapInst.current, mod.default, data))
        }
        setHmLoading(false)
      })
      .catch(() => setHmLoading(false))
  }, [points])

  const renderHeatmap = (map, L, data) => {
    if (hmLayerRef.current) { hmLayerRef.current.clearLayers() }
    else { hmLayerRef.current = L.layerGroup().addTo(map) }
    data.forEach(cell => {
      const risk   = cell.risk_score || 0
      const radius = Math.max(6000, risk * 20000)
      const col    = SEV[cell.risk_level]?.color || '#22c55e'
      L.circle([cell.lat, cell.lon], {
        radius,
        color:       col,
        fillColor:   col,
        fillOpacity: Math.max(0.05, risk * 0.55),
        weight:      1,
        opacity:     0.7,
      }).bindPopup(
        `<div class="agro-popup">
          <div style="font-weight:700;font-size:12px;color:var(--on-surface)">📡 Grid Cell Risk</div>
          <div style="font-size:11px;color:${col};margin:4px 0">${cell.risk_level} — ${cell.risk_pct}%</div>
          <div style="font-size:10px;color:var(--muted)">${cell.dominant_disease || '—'} in ${cell.dominant_crop || '—'}</div>
          <div style="font-size:10px;color:var(--muted)">Scans: ${cell.scan_count} · ${cell.distance_km} km</div>
          <div style="font-size:9px;color:var(--muted);margin-top:2px">NDVI Depletion: ${(cell.ndvi_depletion*100).toFixed(0)}%</div>
        </div>`, { maxWidth: 200 }
      ).addTo(hmLayerRef.current)
    })
  }

  useEffect(() => {
    if (!mapInst.current) return
    import('leaflet').then(mod => {
      const L = mod.default
      if (showHeatmap) {
        if (!heatmapData.length) loadHeatmap()
        else renderHeatmap(mapInst.current, L, heatmapData)
      } else {
        if (hmLayerRef.current) hmLayerRef.current.clearLayers()
      }
    })
  }, [showHeatmap])  // eslint-disable-line

  // ── Hotspot load + render ────────────────────────────────────────────────
  const loadHotspots = useCallback(() => {
    setHsLoading(true)
    getDiseaseHotspots(10)
      .then(d => {
        const data = Array.isArray(d) ? d : []
        setHotspots(data)
        if (mapInst.current) {
          import('leaflet').then(mod => renderHotspots(mapInst.current, mod.default, data))
        }
        setHsLoading(false)
      })
      .catch(() => setHsLoading(false))
  }, [])

  const renderHotspots = (map, L, data) => {
    if (hotspotLayerRef.current) hotspotLayerRef.current.clearLayers()
    else hotspotLayerRef.current = L.layerGroup().addTo(map)
    data.forEach(hs => {
      const col  = SEV[hs.risk_level]?.color || '#f97316'
      const icon = L.divIcon({ html: hotspotMarkerHtml(hs.rank, hs.risk_level), className: '', iconSize: [28,28], iconAnchor: [14,14] })
      L.marker([hs.lat, hs.lon], { icon })
        .bindPopup(`<div class="agro-popup">
          <div style="font-weight:700;font-size:12px;color:${col}">🔥 Hotspot #${hs.rank}</div>
          <div style="font-size:10px;color:var(--on-surface);margin:4px 0">${hs.dominant_disease || '—'} · ${hs.dominant_crop || '—'}</div>
          <div style="font-size:10px;color:var(--muted)">Compound Risk: ${(hs.compound_risk*100).toFixed(1)}%</div>
          <div style="font-size:10px;color:var(--muted)">Avg Severity: ${hs.avg_severity}% · ${hs.scan_count} scans</div>
          <div style="font-size:9px;color:var(--muted);margin-top:3px">Momentum: ${(hs.temporal_momentum*100).toFixed(0)}%</div>
        </div>`, { maxWidth: 220 })
        .addTo(hotspotLayerRef.current)
    })
  }

  useEffect(() => {
    if (!mapInst.current) return
    import('leaflet').then(mod => {
      const L = mod.default
      if (showHotspots) {
        if (!hotspots.length) loadHotspots()
        else renderHotspots(mapInst.current, L, hotspots)
      } else {
        if (hotspotLayerRef.current) hotspotLayerRef.current.clearLayers()
      }
    })
  }, [showHotspots])  // eslint-disable-line

  // ── Fly to + open forecast panel ─────────────────────────────────────────
  const flyTo = (p) => {
    if (mapInst.current) {
      mapInst.current.flyTo([parseFloat(p.lat), parseFloat(p.lon)], 13, { duration: 1.2 })
      const entry = scanMarkersRef.current.find(m => m.p.id === p.id)
      if (entry) setTimeout(() => entry.marker.openPopup(), 1300)
    }
    // Load 7-day forecast for this point
    setForecastPoint(p)
    setForecastLoading(true)
    setForecastData(null)
    getGeoForecast(p.lat, p.lon, 7)
      .then(d => { setForecastData(d); setForecastLoading(false) })
      .catch(() => setForecastLoading(false))
  }

  const trendIcon = (trend) => {
    if (trend === 'increasing') return <TrendingUp size={12} className="text-red-400" />
    if (trend === 'decreasing') return <TrendingDown size={12} className="text-green-400" />
    return <Minus size={12} className="text-yellow-400" />
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════════
  return (
    <div className="p-4 max-w-6xl mx-auto space-y-4">

      {/* ── Header ── */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-agro-100 flex items-center gap-2">
            <Globe size={20} className="text-green-400" /> Geo Intelligence Map
          </h1>
          <p className="text-agro-600 text-xs mt-0.5">
            Spatial agricultural data · Disease detection · Geospatial forecasting
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="btn-ghost text-xs flex items-center gap-1.5 px-3 py-1.5">
            <RefreshCw size={13} /> Refresh
          </button>
          <button onClick={() => navigate('/scan')} className="btn-primary text-xs flex items-center gap-1.5 px-3 py-1.5">
            <ScanLine size={13} /> New Scan
          </button>
        </div>
      </div>

      {/* ── Stats Grid ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Scans',   value: stats.total,     icon: <MapPin size={14}/>,       color: 'var(--green)' },
          { label: 'Critical',      value: stats.critical,  icon: <AlertTriangle size={14}/>, color: '#ef4444' },
          { label: 'Agri POIs',     value: agriCount,       icon: <Sprout size={14}/>,        color: '#84cc16' },
          { label: 'Avg Outbreak',  value: stats.avgOut,    icon: <Activity size={14}/>,      color: '#f97316' },
          { label: 'Heat Cells',    value: stats.heatCells, icon: <Flame size={14}/>,         color: '#fb923c' },
          { label: 'Hotspots',      value: stats.hotCount,  icon: <Zap size={14}/>,           color: '#eab308' },
        ].map(s => (
          <div key={s.label} className="card p-3">
            <div className="flex items-center gap-1.5 mb-1" style={{ color: s.color }}>{s.icon}<span className="text-[10px] text-agro-600 uppercase tracking-wider">{s.label}</span></div>
            <div className="text-lg font-bold font-display" style={{ color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── Controls Bar ── */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Severity filter */}
        <div className="flex items-center gap-1">
          {['All', ...SEV_ORDER].map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className="text-[10px] px-2.5 py-1 rounded-lg font-semibold transition-all"
              style={{
                background: filter === f ? (SEV[f]?.color || 'var(--green)') : 'var(--glass-bg2)',
                color:      filter === f ? 'white' : 'var(--muted)',
                border:     `1px solid ${filter === f ? 'transparent' : 'var(--border)'}`,
              }}>
              {f}
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-border opacity-30" />

        {/* Agri Layer toggle */}
        <button onClick={() => setShowAgri(o => !o)}
          className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-lg font-semibold transition-all"
          style={{
            background: showAgri ? 'rgba(132,204,22,0.15)' : 'var(--glass-bg2)',
            color:      showAgri ? '#84cc16' : 'var(--muted)',
            border:     `1px solid ${showAgri ? 'rgba(132,204,22,0.4)' : 'var(--border)'}`,
          }}>
          <Sprout size={12} />
          {agriLoading ? <Loader size={10} className="animate-spin" /> : null}
          🌾 Agri Layer
        </button>

        {/* Heat Map toggle */}
        <button onClick={() => setShowHeatmap(o => !o)}
          className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-lg font-semibold transition-all"
          style={{
            background: showHeatmap ? 'rgba(249,115,22,0.15)' : 'var(--glass-bg2)',
            color:      showHeatmap ? '#f97316' : 'var(--muted)',
            border:     `1px solid ${showHeatmap ? 'rgba(249,115,22,0.4)' : 'var(--border)'}`,
          }}>
          <Flame size={12} />
          {hmLoading ? <Loader size={10} className="animate-spin" /> : null}
          Heat Map
        </button>

        {/* Hotspots toggle */}
        <button onClick={() => setShowHotspots(o => !o)}
          className="flex items-center gap-1.5 text-[11px] px-3 py-1.5 rounded-lg font-semibold transition-all"
          style={{
            background: showHotspots ? 'rgba(234,179,8,0.15)' : 'var(--glass-bg2)',
            color:      showHotspots ? '#eab308' : 'var(--muted)',
            border:     `1px solid ${showHotspots ? 'rgba(234,179,8,0.4)' : 'var(--border)'}`,
          }}>
          <Zap size={12} />
          {hsLoading ? <Loader size={10} className="animate-spin" /> : null}
          Hotspots
        </button>

        <div className="w-px h-5 bg-border opacity-30" />

        {/* Search */}
        <input value={searchQ} onChange={e => setSearchQ(e.target.value)}
          placeholder="Search crop / disease…"
          className="input-field text-xs py-1.5 px-3 w-40"
          style={{ height: 30 }} />

        {/* Map style */}
        <select value={mapStyle} onChange={e => setMapStyle(e.target.value)}
          className="input-field text-xs py-1.5 px-2 w-28" style={{ height: 30 }}>
          <option value="standard">Standard</option>
          <option value="satellite">Satellite</option>
          <option value="terrain">Terrain</option>
        </select>

        {/* Circles toggle */}
        <button onClick={() => setShowCircles(o => !o)}
          className="flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-lg transition-all"
          style={{ background: 'var(--glass-bg2)', color: 'var(--muted)', border: '1px solid var(--border)' }}>
          {showCircles ? <Eye size={11}/> : <EyeOff size={11}/>} Circles
        </button>

        {/* Table toggle */}
        <button onClick={() => setShowTable(o => !o)}
          className="flex items-center gap-1 text-[10px] px-2.5 py-1.5 rounded-lg transition-all"
          style={{ background: showTable ? 'var(--green)' : 'var(--glass-bg2)', color: showTable ? 'white' : 'var(--muted)', border: '1px solid var(--border)' }}>
          <BarChart2 size={11}/> Table
        </button>
      </div>

      {/* ── Agri sub-filter ── */}
      {showAgri && agriCount > 0 && (
        <div className="card p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] font-bold text-agro-500 uppercase tracking-wider flex items-center gap-1">
              <Sprout size={11}/> Agriculture Layer
            </span>
            {[['all', '🌍 All'], ...Object.entries(AGRI_TYPES).map(([k, v]) => [k, `${v.emoji} ${v.label}`])].map(([key, label]) => (
              <button key={key} onClick={() => setAgriFilter(key)}
                className="text-[10px] px-2 py-0.5 rounded-md font-medium transition-all"
                style={{
                  background: agriFilter === key ? 'rgba(132,204,22,0.2)' : 'var(--glass-bg2)',
                  color:      agriFilter === key ? '#84cc16' : 'var(--muted)',
                  border:     `1px solid ${agriFilter === key ? 'rgba(132,204,22,0.4)' : 'var(--border)'}`,
                }}>
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Two-column layout: Map + Forecast Panel ── */}
      <div className={`flex gap-4 ${forecastData || forecastLoading ? 'items-start' : ''}`}>

        {/* ── Map Container ── */}
        <div className={`card overflow-hidden ${forecastData || forecastLoading ? 'flex-1' : 'w-full'}`} style={{ minHeight: 520 }}>
          {loading ? (
            <div className="flex items-center justify-center h-80 gap-3">
              <Loader size={20} className="animate-spin text-green-400" />
              <span className="text-agro-500 text-sm">Loading geo data…</span>
            </div>
          ) : (
            <div style={{ position: 'relative', height: forecastData ? 520 : 580 }}>
              <div ref={mapRef} style={{ width:'100%', height:'100%' }} />

              {/* Bottom coordinate hint */}
              {points.length > 0 && (
                <div style={{
                  position:'absolute', bottom:8, left:8, zIndex:500,
                  background:'var(--glass-bg)', backdropFilter:'blur(12px)',
                  border:'1px solid var(--border)', borderRadius:8,
                  padding:'4px 10px', fontSize:10, color:'var(--muted)',
                }}>
                  <Crosshair size={9} style={{ display:'inline', marginRight:4 }} />
                  Click scan marker to view details · 6-decimal precision
                </div>
              )}

              {/* No locations overlay */}
              {!loading && points.length === 0 && (
                <div style={{
                  position:'absolute', inset:0, display:'flex', flexDirection:'column',
                  alignItems:'center', justifyContent:'center', gap:8,
                  background:'rgba(3,10,5,0.6)', backdropFilter:'blur(8px)', zIndex:500,
                }}>
                  <Globe size={32} style={{ color:'var(--muted)' }} />
                  <p style={{ color:'var(--muted)', fontSize:13 }}>No geo-tagged scans yet</p>
                  <button onClick={() => navigate('/scan')} className="btn-primary text-xs">
                    <ScanLine size={12}/> Run First Scan
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── 7-day Forecast Panel ── */}
        {(forecastData || forecastLoading) && (
          <div className="card p-4 w-72 flex-shrink-0 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-agro-200 flex items-center gap-1.5">
                  <TrendingUp size={13} className="text-orange-400" /> 7-Day Forecast
                </div>
                {forecastPoint && (
                  <div className="text-[10px] text-agro-600 mt-0.5">
                    {forecastPoint.crop || 'Unknown'} · {fmt6(forecastPoint.lat)}, {fmt6(forecastPoint.lon)}
                  </div>
                )}
              </div>
              <button onClick={() => { setForecastData(null); setForecastPoint(null) }}
                className="text-agro-600 hover:text-agro-400 transition-colors">
                <X size={14} />
              </button>
            </div>

            {forecastLoading ? (
              <div className="flex items-center justify-center py-8 gap-2">
                <Loader size={16} className="animate-spin text-green-400" />
                <span className="text-xs text-agro-600">Simulating spread…</span>
              </div>
            ) : forecastData && (
              <>
                {/* Summary row */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="rounded-xl p-2.5" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                    <div className="text-[9px] text-agro-600 uppercase tracking-wider">Trend</div>
                    <div className="flex items-center gap-1 mt-0.5">
                      {trendIcon(forecastData.trend)}
                      <span className="text-xs font-bold text-agro-200 capitalize">{forecastData.trend}</span>
                    </div>
                  </div>
                  <div className="rounded-xl p-2.5" style={{ background:'rgba(249,115,22,0.08)', border:'1px solid rgba(249,115,22,0.2)' }}>
                    <div className="text-[9px] text-orange-400 uppercase tracking-wider">Peak Day</div>
                    <div className="text-xs font-bold text-orange-400 mt-0.5">
                      Day {forecastData.peak_risk_day} · {(forecastData.peak_risk_score*100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="rounded-xl p-2.5" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                    <div className="text-[9px] text-agro-600 uppercase tracking-wider">Spread Dir</div>
                    <div className="text-xs font-bold text-agro-200 mt-0.5">→ {forecastData.spread_direction}</div>
                  </div>
                  <div className="rounded-xl p-2.5" style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
                    <div className="text-[9px] text-agro-600 uppercase tracking-wider">Disease</div>
                    <div className="text-xs font-bold text-agro-200 mt-0.5 truncate">
                      {forecastData.dominant_disease || '—'}
                    </div>
                  </div>
                </div>

                {/* Chart */}
                <div>
                  <div className="text-[10px] text-agro-600 mb-2 flex items-center gap-1">
                    <BarChart2 size={10} /> Daily Disease Risk (%)
                  </div>
                  <ForecastChart forecast={forecastData.forecast} />
                </div>

                {/* Day-by-day list */}
                <div className="space-y-1 max-h-44 overflow-y-auto pr-1">
                  {(forecastData.forecast || []).map((d, i) => {
                    const cfg = SEV[d.risk_level] || SEV.Low
                    return (
                      <div key={i} className="flex items-center justify-between text-[10px] px-2 py-1.5 rounded-lg"
                        style={{ background:'var(--glass-bg2)', border:`1px solid ${cfg.color}25` }}>
                        <span className="text-agro-500">
                          {new Date(d.date).toLocaleDateString('en-IN', { weekday:'short', day:'numeric', month:'short' })}
                        </span>
                        <span className="font-bold" style={{ color: cfg.color }}>
                          {d.risk_level} · {d.risk_pct}%
                        </span>
                        <span className="text-agro-700">{(d.confidence*100).toFixed(0)}% conf</span>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* ── Map Legend ── */}
      <div className="card p-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Disease scan legend */}
          <div>
            <p className="text-[10px] font-bold text-agro-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <MapPin size={11}/> Disease Scan Markers
            </p>
            <div className="flex flex-wrap gap-2">
              {SEV_ORDER.map(s => (
                <div key={s} className="flex items-center gap-1.5 text-[10px]">
                  <div style={{ width:10, height:10, borderRadius:'50%', background:SEV[s].color, boxShadow:`0 0 6px ${SEV[s].glow}` }} />
                  <span style={{ color: SEV[s].color }}>{s}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Heat map legend */}
          <div>
            <p className="text-[10px] font-bold text-agro-500 uppercase tracking-wider mb-2 flex items-center gap-1">
              <Flame size={11}/> Heat Map Cells (0.1° grid)
            </p>
            <div className="flex items-center gap-1">
              <span className="text-[9px] text-agro-600">Low</span>
              {['#22c55e','#84cc16','#eab308','#f97316','#ef4444'].map((c,i) => (
                <div key={i} style={{ width:20, height:10, background:c, borderRadius:2, opacity:0.7 }} />
              ))}
              <span className="text-[9px] text-agro-600">Critical</span>
            </div>
            <p className="text-[9px] text-agro-700 mt-1">Each circle = compound risk of that 11 km² cell</p>
          </div>

          {/* Agri layer legend */}
          {showAgri && (
            <div>
              <p className="text-[10px] font-bold text-agro-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Sprout size={11}/> Agriculture Layer
                {!showAgri && <span className="text-agro-700 font-normal">(toggle on above)</span>}
              </p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(AGRI_TYPES).slice(0, 6).map(([key, cfg]) => (
                  <div key={key} className="flex items-center gap-1.5 text-[10px] px-2 py-1 rounded-lg"
                    style={{ background:cfg.bg, border:`1px solid ${cfg.border}` }}>
                    <span>{cfg.emoji}</span>
                    <span style={{ color:cfg.color }}>{cfg.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Zone Alerts Panel ── */}
      {(zoneAlerts.length > 0 || alertsLoading) && (
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle size={15} className="text-orange-400" />
              <span className="text-sm font-bold text-agro-200">Zone Disease Alerts</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                style={{ background:'rgba(249,115,22,0.1)', color:'#f97316', border:'1px solid rgba(249,115,22,0.25)' }}>
                {zoneAlerts.length} zone{zoneAlerts.length !== 1 ? 's' : ''}
              </span>
            </div>
            <button onClick={() => setShowAlerts(o => !o)}
              className="text-[10px] text-agro-600 flex items-center gap-1">
              {showAlerts ? <EyeOff size={11}/> : <Eye size={11}/>}
              {showAlerts ? 'Hide' : 'Show'}
            </button>
          </div>

          {alertsLoading && (
            <div className="flex items-center gap-2 py-2">
              <Loader size={14} className="animate-spin text-orange-400" />
              <span className="text-xs text-agro-600">Computing zone alerts…</span>
            </div>
          )}

          {showAlerts && !alertsLoading && (
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {zoneAlerts.slice(0, 8).map((alert, i) => {
                const cfg = SEV[alert.risk_level] || SEV.Low
                return (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-xl transition-all"
                    style={{ background:`${cfg.color}08`, border:`1px solid ${cfg.color}25` }}>
                    <div className="w-2 h-2 rounded-full mt-1 flex-shrink-0"
                      style={{ background: cfg.color, boxShadow:`0 0 6px ${cfg.glow || cfg.color}` }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md"
                          style={{ background:`${cfg.color}20`, color: cfg.color }}>
                          {alert.risk_level}
                        </span>
                        <span className="text-xs font-semibold text-agro-200">{alert.disease}</span>
                        <span className="text-[10px] text-agro-600">in {alert.crop}</span>
                      </div>
                      <p className="text-[10px] text-agro-500 mt-1 leading-relaxed">{alert.message}</p>
                      <div className="flex items-center gap-3 mt-1.5">
                        <span className="text-[9px] text-agro-700">Avg sev: {alert.avg_severity}%</span>
                        <span className="text-[9px] text-agro-700">{alert.scan_count} scans</span>
                        <span className="text-[9px] text-agro-700">{alert.distance_km} km away</span>
                        {alert.temporal_momentum > 0.3 && (
                          <span className="text-[9px] font-bold text-red-400 flex items-center gap-0.5">
                            <TrendingUp size={9}/> Accelerating
                          </span>
                        )}
                      </div>
                    </div>
                    <button onClick={() => {
                      if (mapInst.current) mapInst.current.flyTo([alert.lat, alert.lon], 11, { duration: 1.2 })
                    }} className="text-[9px] text-agro-600 hover:text-green-400 transition-colors flex-shrink-0 mt-1">
                      <Navigation size={11} />
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ── Hotspots Summary ── */}
      {showHotspots && hotspots.length > 0 && (
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={15} className="text-yellow-400" />
            <span className="text-sm font-bold text-agro-200">Disease Outbreak Hotspots</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{ background:'rgba(234,179,8,0.1)', color:'#eab308', border:'1px solid rgba(234,179,8,0.25)' }}>
              Top {hotspots.length}
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {hotspots.slice(0, 6).map((hs, i) => {
              const cfg = SEV[hs.risk_level] || SEV.Low
              return (
                <div key={i} className="flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition-all hover:scale-[1.01]"
                  style={{ background:`${cfg.color}08`, border:`1px solid ${cfg.color}25` }}
                  onClick={() => { if (mapInst.current) mapInst.current.flyTo([hs.lat, hs.lon], 12, { duration: 1.2 }) }}>
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                    style={{ background:`${cfg.color}20`, border:`1.5px solid ${cfg.color}`, color: cfg.color }}>
                    {hs.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-agro-200 truncate">{hs.dominant_disease || 'Unknown disease'}</div>
                    <div className="text-[10px] text-agro-600">{hs.dominant_crop || '—'} · {hs.avg_severity}% sev · {hs.scan_count} scans</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[9px] font-bold" style={{ color: cfg.color }}>
                        {(hs.compound_risk * 100).toFixed(1)}% risk
                      </span>
                      {hs.temporal_momentum > 0.3 && (
                        <span className="text-[9px] text-red-400 flex items-center gap-0.5">
                          <TrendingUp size={8}/> Rising
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Scan Data Table ── */}
      {showTable && filtered.length > 0 && (
        <div className="card p-5 overflow-x-auto">
          <div className="flex items-center gap-2 mb-4">
            <BarChart2 size={15} className="text-agro-400" />
            <span className="text-sm font-bold text-agro-200">Scan Data ({filtered.length})</span>
          </div>
          <table className="w-full text-xs">
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['#','Crop','Disease','Img Sev','Geo Sev','Cell ID','Geo Risk','NDVI','Lat','Lon','Date','Forecast'].map(h => (
                  <th key={h} className="text-left pb-2 pr-4 text-[10px] font-semibold text-agro-600 uppercase tracking-wider whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 50).map((p, i) => {
                const sev    = SEV[p.severity_level] || SEV.Low
                const geoSev = p.geo_conditioned_severity != null ? parseFloat(p.geo_conditioned_severity).toFixed(1) + '%' : '—'
                const ndvi   = p.ndvi_proxy != null ? parseFloat(p.ndvi_proxy).toFixed(2) : '—'
                return (
                  <tr key={p.id} style={{ borderBottom: '1px solid var(--border)', opacity: 0.9 }}
                    className="hover:opacity-100 transition-opacity">
                    <td className="py-2 pr-4 text-agro-600">{i + 1}</td>
                    <td className="py-2 pr-4 text-agro-200 font-medium whitespace-nowrap">{p.crop || '—'}</td>
                    <td className="py-2 pr-4 text-agro-400 whitespace-nowrap max-w-[120px] truncate">{p.disease || '—'}</td>
                    <td className="py-2 pr-4 font-semibold whitespace-nowrap" style={{ color: sev.color }}>
                      {parseFloat(p.severity || 0).toFixed(1)}%
                    </td>
                    <td className="py-2 pr-4 font-bold whitespace-nowrap" style={{ color: '#f97316' }}>{geoSev}</td>
                    <td className="py-2 pr-4 text-agro-600 font-mono text-[9px] whitespace-nowrap">{p.cell_id || '—'}</td>
                    <td className="py-2 pr-4 whitespace-nowrap">
                      <span className="px-1.5 py-0.5 rounded-md text-[9px] font-bold"
                        style={{ background:`${(SEV[p.geo_risk === 'High' ? 'Critical' : p.geo_risk === 'Medium' ? 'High' : 'Low']?.color || '#22c55e')}18`, color: SEV[p.geo_risk === 'High' ? 'Critical' : p.geo_risk === 'Medium' ? 'High' : 'Low']?.color || '#22c55e' }}>
                        {p.geo_risk || 'Low'}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-agro-500">{ndvi}</td>
                    <td className="py-2 pr-4 text-agro-600 font-mono">{fmt6(p.lat)}</td>
                    <td className="py-2 pr-4 text-agro-600 font-mono">{fmt6(p.lon)}</td>
                    <td className="py-2 pr-4 text-agro-600 whitespace-nowrap">{fmtDate(p.timestamp)}</td>
                    <td className="py-2 pr-4">
                      <button onClick={() => flyTo(p)}
                        className="text-[9px] font-semibold px-2 py-1 rounded-md flex items-center gap-1 transition-all"
                        style={{ background:'rgba(34,197,94,0.12)', color:'var(--green)', border:'1px solid rgba(34,197,94,0.25)' }}>
                        <Navigation size={9}/> Fly + Forecast
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Empty state ── */}
      {!loading && points.length === 0 && (
        <div className="card p-8 flex flex-col items-center gap-4 text-center">
          <Globe size={40} className="text-agro-700" />
          <div>
            <div className="text-sm font-bold text-agro-300 mb-1">No geo-tagged scans yet</div>
            <div className="text-xs text-agro-600">Run a scan with GPS enabled to see disease data on the map</div>
          </div>
          <button onClick={() => navigate('/scan')} className="btn-primary text-xs">
            <ScanLine size={12}/> Go to Scan
          </button>
        </div>
      )}

      {/* Leaflet ping animation */}
      <style>{`@keyframes ping{0%,100%{transform:scale(1);opacity:0.7}50%{transform:scale(1.8);opacity:0}}`}</style>
    </div>
  )
}
