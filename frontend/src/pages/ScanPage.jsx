import React, { useState, useRef, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../App'
import { predict, getSoilParams } from '../api/api'
import { saveLastResult } from '../utils/storage'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import {
  Upload, ScanLine, MapPin, Loader, X, Image, CheckCircle,
  Navigation, ChevronDown, Zap, Camera, AlertTriangle, Mic, MicOff
} from 'lucide-react'

const CROPS = [
  // Crops fully supported by 84-class trained model
  'Unknown',
  'Apple','Banana','Blueberry','Cherry','Citrus','Coffee',
  'Corn','Cotton','Grape','Groundnut','Mango','Orange',
  'Peach','Pepper','Potato','Raspberry','Rice','Soybean',
  'Squash','Strawberry','Sugarcane','Tea','Tomato','Wheat',
  // Additional crops with fallback knowledge base
  'Brinjal','Chilli','Maize','Onion'
]

const SCAN_STEPS = [
  { msg: 'Validating leaf image…',          pct: 10 },
  { msg: 'Preprocessing image…',            pct: 22 },
  { msg: 'Running leaf disease model…',     pct: 38 },
  { msg: 'Analysing soil & risk factors…',  pct: 55 },
  { msg: 'Computing geo-intelligence…',     pct: 72 },
  { msg: 'Running RL optimisation…',        pct: 87 },
  { msg: 'Generating recommendations…',     pct: 96 },
]

const PARAMS = [
  { key:'temperature', label:'Temperature (°C)', min:0,   max:50,  step:0.5, default:28  },
  { key:'humidity',    label:'Humidity (%)',      min:0,   max:100, step:1,   default:65  },
  { key:'ph',          label:'Soil pH',           min:0,   max:14,  step:0.1, default:6.5 },
  { key:'rainfall',    label:'Rainfall (mm)',     min:0,   max:500, step:5,   default:80  },
]

export default function ScanPage() {
  const { fields, activeField, setActiveScan } = useApp()
  const navigate  = useNavigate()
  const fileRef   = useRef()
  const videoRef  = useRef()
  const canvasRef = useRef()

  const [currentStep, setCurrentStep] = useState(1) // Wizard step tracking
  
  const [image,       setImage]       = useState(null)
  const [preview,     setPreview]     = useState(null)
  const [dragging,    setDragging]    = useState(false)
  const [crop,        setCrop]        = useState('Unknown')
  // ── Voice Input (Patent Feature — Edge AI / Accessibility) ──
  const [voiceActive, setVoiceActive] = useState(false)
  const recognitionRef = useRef(null)
  const [autoFilled,  setAutoFilled]  = useState(new Set()) // tracks which fields were auto-filled

  const startVoice = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return toast.error('Voice input not supported in this browser')
    const rec = new SR()
    rec.lang = 'en-IN'
    rec.interimResults = false
    rec.maxAlternatives = 5
    rec.onresult = (e) => {
      const heard = Array.from(e.results[0]).map(r => r.transcript.trim().toLowerCase())
      const match = CROPS.find(c => heard.some(h => h.includes(c.toLowerCase())))
      if (match) { setCrop(match); toast.success(`Crop set to "${match}" via voice`) }
      else { toast('Could not match a crop name. Try again.', { icon: '🎤' }) }
      setVoiceActive(false)
    }
    rec.onerror = () => { setVoiceActive(false); toast.error('Voice error — try again') }
    rec.onend   = () => setVoiceActive(false)
    recognitionRef.current = rec
    rec.start()
    setVoiceActive(true)
  }

  const stopVoice = () => {
    recognitionRef.current?.stop()
    setVoiceActive(false)
  }
  const [fieldId,     setFieldId]     = useState('')
  const [lat,         setLat]         = useState('')
  const [lon,         setLon]         = useState('')
  const [locLoading,  setLocLoading]  = useState(false)
  const [scanning,    setScanning]    = useState(false)
  const [scanPct,     setScanPct]     = useState(0)
  const [scanMsg,     setScanMsg]     = useState('')
  const [camOpen,     setCamOpen]     = useState(false)
  const [leafError,   setLeafError]   = useState('')
  const [soilData,    setSoilData]    = useState(null)
  const [soilLoading, setSoilLoading] = useState(false)
  const [params,      setParams]      = useState(() =>
    Object.fromEntries(PARAMS.map(p => [p.key, p.default]))
  )

  useEffect(() => { if (activeField) setFieldId(activeField) }, [activeField])

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) { toast.error('Please select a valid image file'); return }
    setImage(file); setPreview(URL.createObjectURL(file)); setLeafError('')
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  // ── After getting a confirmed lat/lon, fetch soil params ─────────────────
  const afterGPS = (la, lo) => {
    setLat(String(la)); setLon(String(lo)); setLocLoading(false)
    toast.success('📍 Location detected!')
    setSoilLoading(true)
    getSoilParams(la, lo).then(d => {
      setSoilData(d)
      const updates = {}; const filled = []
      if (d.temperature != null && d.temperature > 0) {
        updates.temperature = parseFloat(d.temperature.toFixed(1))
        filled.push(`🌡️ Temperature: ${updates.temperature}°C`)
      }
      if (d.humidity != null && d.humidity > 0) {
        updates.humidity = Math.round(d.humidity)
        filled.push(`💧 Humidity: ${updates.humidity}%`)
      }
      if (d.rainfall_estimate != null) {
        updates.rainfall = Math.round(d.rainfall_estimate)
        filled.push(`🌧️ Rainfall: ${updates.rainfall}mm`)
      }
      if (d.ph != null && d.ph > 0) {
        updates.ph = parseFloat(d.ph.toFixed(1))
        filled.push(`🧪 Soil pH: ${updates.ph}`)
      }
      if (Object.keys(updates).length > 0) {
        setParams(p => ({ ...p, ...updates }))
        setAutoFilled(new Set(Object.keys(updates)))
        filled.forEach((msg, i) => {
          setTimeout(() => toast.success(`Auto-filled — ${msg}`, {
            duration: 3500, icon: '📡', style: { fontSize: '12px' },
          }), i * 600)
        })
      }
      setSoilLoading(false)
    }).catch(() => { setSoilLoading(false) })
  }

  // ── IP-based fallback (no browser permission needed) ──────────────────────
  const ipFallback = async () => {
    try {
      // Try ipapi.co first (free, no key)
      const r = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(6000) })
      const d = await r.json()
      if (d.latitude && d.longitude) {
        afterGPS(parseFloat(d.latitude).toFixed(6), parseFloat(d.longitude).toFixed(6))
        toast('📡 Using approximate IP location (city-level)', {
          icon: 'ℹ️', duration: 4000,
        })
        return true
      }
    } catch {}
    try {
      // Second fallback: ip-api.com
      const r2 = await fetch('http://ip-api.com/json/', { signal: AbortSignal.timeout(6000) })
      const d2 = await r2.json()
      if (d2.status === 'success' && d2.lat && d2.lon) {
        afterGPS(parseFloat(d2.lat).toFixed(6), parseFloat(d2.lon).toFixed(6))
        toast('📡 Using approximate IP location (city-level)', {
          icon: 'ℹ️', duration: 4000,
        })
        return true
      }
    } catch {}
    return false
  }

  // ── Main GPS detection — tries 3 strategies in order ─────────────────────
  const getGPS = async () => {
    if (!navigator.geolocation) {
      // No browser geolocation at all — go straight to IP fallback
      setLocLoading(true)
      const ok = await ipFallback()
      if (!ok) {
        toast.error('Could not detect location. Enter latitude/longitude manually below.')
        setLocLoading(false)
      }
      return
    }

    setLocLoading(true)

    // Strategy 1 — high accuracy (GPS chip, slower)
    const tryHighAccuracy = () => new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      })
    })

    // Strategy 2 — low accuracy (cell/wifi, faster, more permissive)
    const tryLowAccuracy = () => new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false,
        timeout: 15000,
        maximumAge: 60000,
      })
    })

    try {
      // Try high-accuracy first
      const pos = await tryHighAccuracy()
      afterGPS(pos.coords.latitude.toFixed(6), pos.coords.longitude.toFixed(6))
    } catch (e1) {
      // High-accuracy failed — try low-accuracy
      try {
        const pos2 = await tryLowAccuracy()
        afterGPS(pos2.coords.latitude.toFixed(6), pos2.coords.longitude.toFixed(6))
      } catch (e2) {
        // Both geolocation attempts failed
        const code = e2?.code || e1?.code
        if (code === 1) {
          // PERMISSION_DENIED — browser blocked location; try IP fallback silently
          toast('Browser location blocked — trying IP fallback…', {
            icon: '🔄', duration: 2500,
          })
          const ok = await ipFallback()
          if (!ok) {
            toast.error(
              'Location blocked. Enable Location in browser Settings, or type coordinates manually below.',
              { duration: 6000 }
            )
            setLocLoading(false)
          }
        } else if (code === 2) {
          // POSITION_UNAVAILABLE — try IP
          const ok = await ipFallback()
          if (!ok) {
            toast.error('Location unavailable. Try again or enter coordinates manually.')
            setLocLoading(false)
          }
        } else {
          // TIMEOUT or unknown
          const ok = await ipFallback()
          if (!ok) {
            toast.error('Location timed out. Enter coordinates manually or try again.')
            setLocLoading(false)
          }
        }
      }
    }
  }

  const openCamera = async () => {
    setCamOpen(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      videoRef.current.srcObject = stream; videoRef.current.play()
    } catch { toast.error('Camera not available'); setCamOpen(false) }
  }

  const capturePhoto = () => {
    const canvas = canvasRef.current, video = videoRef.current
    canvas.width = video.videoWidth; canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    canvas.toBlob(blob => {
      handleFile(new File([blob], 'capture.jpg', { type: 'image/jpeg' }))
      video.srcObject?.getTracks().forEach(t => t.stop()); setCamOpen(false)
    }, 'image/jpeg', 0.92)
  }

  const runScan = async () => {
    if (!image) return toast.error('Please select an image first')
    setScanning(true); setScanPct(0); setScanMsg(SCAN_STEPS[0].msg); setLeafError('')

    let step = 0
    const timer = setInterval(() => {
      if (step < SCAN_STEPS.length - 1) { step++; setScanPct(SCAN_STEPS[step].pct); setScanMsg(SCAN_STEPS[step].msg) }
    }, 700)

    try {
      const fd = new FormData()
      fd.append('image', image)
      fd.append('crop', crop)
      fd.append('crop_type', crop)   // backend uses crop_type as the linked field
      PARAMS.forEach(p => fd.append(p.key, params[p.key]))
      if (lat)     fd.append('lat',      lat)
      if (lon)     fd.append('lon',      lon)
      if (fieldId) fd.append('field_id', fieldId)

      const data = await predict(fd)
      clearInterval(timer)

      // ── Leaf validation rejection ──────────────────────────────────────
      if (data.status === 'not_a_leaf') {
        setScanning(false); setScanPct(0); setScanMsg('')
        setLeafError(data.error || 'Please upload a clear leaf image.')
        return
      }

      setScanPct(100); setScanMsg('Analysis complete!')
      setActiveScan({ result: data, image_preview: preview })
      saveLastResult({ ...data, _image_preview: preview })
      toast.success('Scan complete!')
      setTimeout(() => {
        if (data.scan?.id) navigate(`/analysis/${data.scan.id}`)
        else navigate('/analysis')
      }, 500)
    } catch (e) {
      clearInterval(timer); setScanning(false); setScanPct(0); setScanMsg('')
      const msg = e?.response?.data?.error || e.message || 'Scan failed'
      if (e?.response?.status === 422 && e?.response?.data?.status === 'not_a_leaf') {
        setLeafError(e.response.data.error || 'Not a leaf image.')
      } else {
        toast.error(msg)
      }
    }
  }

  const renderStepIndicator = () => (
    <div className="flex items-center justify-between max-w-xl mx-auto mb-8 relative px-4">
      <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-1 bg-[var(--glass-bg2)] -z-10 rounded-full overflow-hidden">
        <div className="h-full transition-all duration-500" style={{ width: currentStep === 1 ? '0%' : currentStep === 2 ? '50%' : '100%', background: 'var(--green)' }} />
      </div>
      {[
        { num: 1, label: 'Image & Crop' },
        { num: 2, label: 'Location & Env' },
        { num: 3, label: 'Review & Run' }
      ].map((s) => (
        <div key={s.num} className="flex flex-col items-center gap-2">
          <div className={clsx('w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300',
            currentStep >= s.num ? 'bg-[var(--green)] text-black shadow-[0_0_12px_rgba(34,197,94,0.4)]' : 'bg-[var(--glass-bg2)] text-[var(--muted)] border border-[var(--border)]'
          )}>
            {currentStep > s.num ? <CheckCircle size={18} /> : s.num}
          </div>
          <span className={clsx("text-[11px] font-medium tracking-wide", currentStep >= s.num ? 'text-[var(--on-surface)]' : 'text-[var(--muted)]')}>
            {s.label}
          </span>
        </div>
      ))}
    </div>
  )

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Camera overlay */}
      {camOpen && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4"
          style={{ background: 'rgba(0,0,0,0.93)' }}>
          <video ref={videoRef} className="w-full max-w-lg rounded-2xl" autoPlay playsInline />
          <canvas ref={canvasRef} className="hidden" />
          <div className="flex gap-4">
            <button onClick={capturePhoto} className="btn-primary px-8 py-3">📸 Capture</button>
            <button onClick={() => { videoRef.current?.srcObject?.getTracks().forEach(t => t.stop()); setCamOpen(false) }} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      <div>
        <h1 className="text-xl font-bold text-agro-100">New Crop Scan</h1>
        <p className="text-agro-600 text-sm mt-1">Upload a <strong>leaf</strong> or plant image to run the full AI pipeline</p>
      </div>

      {renderStepIndicator()}

      {/* Leaf validation error banner */}
      {leafError && (
        <div className="flex items-start gap-3 p-4 rounded-xl border glow-amber mb-6"
          style={{ background: 'rgba(245,158,11,0.08)', borderColor: 'rgba(245,158,11,0.35)', color: 'var(--amber)' }}>
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-sm">Not a leaf image detected</p>
            <p className="text-xs mt-1 opacity-80">{leafError}</p>
            <p className="text-xs mt-2 opacity-60">Tip: Take a close-up photo of the crop leaf with good lighting. Brown or yellowed diseased leaves are fine.</p>
          </div>
        </div>
      )}

      <div className="max-w-2xl mx-auto space-y-6">
        
        {/* STEP 1: Image & Crop Type */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-fade-in">
            {/* Drop zone */}
            <div className={clsx('upload-zone h-72 relative', dragging && 'active')}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => !preview && !scanning && fileRef.current?.click()}>
              <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden"
                onChange={e => handleFile(e.target.files[0])} />

              {preview ? (
                <>
                  <img src={preview} className="absolute inset-0 w-full h-full object-contain p-4" alt="Preview" />
                  {!scanning && (
                    <button onClick={e => { e.stopPropagation(); setImage(null); setPreview(null); setLeafError('') }}
                      className="absolute top-3 right-3 w-7 h-7 rounded-full bg-black/60 border flex items-center justify-center z-10 text-white"
                      style={{ borderColor: 'var(--border)' }}>
                      <X size={13} />
                    </button>
                  )}
                  {scanning && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 z-10 rounded-2xl"
                      style={{ background: 'rgba(3,10,5,0.9)', backdropFilter: 'blur(6px)' }}>
                      <Loader size={32} className="text-agro-400 animate-spin" />
                      <div className="text-center">
                        <div className="text-sm font-medium text-agro-200">{scanMsg}</div>
                        <div className="text-xs text-agro-600 mt-1">{scanPct}% complete</div>
                      </div>
                      <div className="w-52 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--glass-bg2)' }}>
                        <div className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${scanPct}%`, background: 'var(--green)' }} />
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-2"
                    style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
                    <Image size={28} className="text-agro-600" />
                  </div>
                  <div className="text-center">
                    <div className="text-base font-medium text-agro-300">Drop leaf image here or click to browse</div>
                    <div className="text-xs text-agro-700 mt-1">PNG, JPG, WEBP · Must be a plant/leaf photo</div>
                  </div>
                  <div className="flex gap-3 mt-4">
                    <button onClick={e => { e.stopPropagation(); fileRef.current?.click() }} className="btn-primary text-sm px-6 py-2">
                      <Upload size={14} className="mr-1.5" /> Upload
                    </button>
                    <button onClick={e => { e.stopPropagation(); openCamera() }} className="btn-secondary text-sm px-6 py-2">
                      <Camera size={14} className="mr-1.5" /> Camera
                    </button>
                  </div>
                </>
              )}
            </div>

            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-semibold text-agro-300">Crop Type</label>
                <button
                  onClick={voiceActive ? stopVoice : startVoice}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                    voiceActive
                      ? 'border-red-500/50 text-red-400 animate-pulse bg-red-950/20'
                      : 'border-agro-700 text-agro-500 hover:text-agro-300 hover:border-agro-500 bg-[var(--glass-bg2)]'
                  }`}
                  title="Say the crop name (e.g. 'Tomato', 'Rice')"
                >
                  {voiceActive ? <MicOff size={13} /> : <Mic size={13} />}
                  {voiceActive ? 'Listening…' : 'Use Voice'}
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto pr-2">
                {CROPS.map(c => (
                  <button key={c} onClick={() => setCrop(c)}
                    className="px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left border"
                    style={{
                      background: crop === c ? 'rgba(34,197,94,0.1)' : 'var(--glass-bg2)',
                      borderColor: crop === c ? 'var(--green)' : 'var(--border)',
                      color: crop === c ? 'var(--green)' : 'var(--muted)',
                    }}>
                    {c}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button 
                onClick={() => setCurrentStep(2)} 
                disabled={!image}
                className={clsx('btn-primary px-8 py-3 text-sm font-semibold transition-all', !image && 'opacity-50 cursor-not-allowed')}>
                Next: Location & Env →
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: Location & Environment */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-fade-in">
            {/* GPS */}
            <div className="card p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="text-sm font-semibold text-agro-300 flex items-center gap-2">
                  <MapPin size={15} className="text-agro-500" />
                  GPS Location
                  <span className="text-agro-700 font-normal text-xs ml-1">(improves geo-risk accuracy)</span>
                </div>
                <button onClick={getGPS} disabled={locLoading}
                  className="flex items-center gap-1.5 text-xs px-4 py-2 rounded-lg font-medium transition-all disabled:opacity-60"
                  style={{
                    background: lat && lon ? 'rgba(34,197,94,0.12)' : 'rgba(34,197,94,0.08)',
                    color: lat && lon ? 'var(--green)' : 'var(--muted)',
                    border: `1px solid ${lat && lon ? 'rgba(34,197,94,0.3)' : 'var(--border)'}`,
                  }}>
                  {locLoading
                    ? <><Loader size={13} className="animate-spin" /> Detecting…</>
                    : lat && lon
                      ? <><CheckCircle size={13} /> Detected ✓</>
                      : <><Navigation size={13} /> Auto-detect</>
                  }
                </button>
              </div>

              {/* Manual coordinate inputs */}
              <div className="grid grid-cols-2 gap-4">
                {[['lat','Latitude','e.g. 16.5062'],['lon','Longitude','e.g. 80.6480']].map(([key, label, ph]) => (
                  <div key={key}>
                    <label className="text-xs text-agro-600 mb-1.5 block">{label}</label>
                    <input className="input text-sm py-2.5" placeholder={ph} type="number" step="0.0001"
                      value={key === 'lat' ? lat : lon}
                      onChange={e => key === 'lat' ? setLat(e.target.value) : setLon(e.target.value)} />
                  </div>
                ))}
              </div>

              {/* Status row */}
              {lat && lon ? (
                <div className="mt-3 flex items-center gap-1.5 text-xs" style={{ color: 'var(--green)' }}>
                  <CheckCircle size={12} />
                  {parseFloat(lat).toFixed(4)}°N, {parseFloat(lon).toFixed(4)}°E
                  <span style={{ color: 'var(--muted)' }}>· geo-risk active</span>
                </div>
              ) : (
                <p className="mt-3 text-xs" style={{ color: 'var(--muted)' }}>
                  💡 Click Auto-detect or type coordinates manually above
                </p>
              )}

              {/* Soil parameters from GPS */}
              {soilLoading && (
                <div className="mt-3 flex items-center gap-2 text-xs text-agro-600">
                  <Loader size={12} className="animate-spin" /> Fetching real soil data for your location…
                </div>
              )}
              {soilData && !soilLoading && (
                <div className="mt-4 p-4 rounded-xl space-y-3"
                  style={{ background:'var(--glass-bg2)', border:'1px solid var(--border-hi)' }}>
                  <div className="text-xs font-bold text-agro-400 uppercase tracking-wider flex items-center gap-2">
                    🌍 Real Soil Data — {soilData.source}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label:'Soil pH',    val: soilData.ph != null ? soilData.ph.toFixed(1) : '—' },
                      { label:'Soil Temp',  val: soilData.soil_temperature != null ? soilData.soil_temperature.toFixed(1)+'°C' : '—' },
                    ].map(r => (
                      <div key={r.label} className="flex justify-between items-center text-xs border-b pb-2" style={{ borderColor: 'var(--border)' }}>
                        <span className="text-agro-600">{r.label}</span>
                        <span className="font-semibold text-agro-200">{r.val}</span>
                      </div>
                    ))}
                  </div>
                  {soilData.ph && (
                    <div className="text-xs text-agro-500 pt-1">
                      ✅ Soil pH & temperature auto-filled from real GPS data
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Environmental params */}
            <div className="card p-5">
              <div className="text-sm font-semibold mb-5 flex items-center gap-2" style={{ color: 'var(--on-surface)' }}>
                🌿 Environmental Conditions
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {PARAMS.map(p => {
                  const val = params[p.key] ?? p.default
                  const decrement = () => setParams(prev => ({
                    ...prev,
                    [p.key]: parseFloat(Math.max(p.min, parseFloat((prev[p.key] - p.step).toFixed(10))).toFixed(p.step < 1 ? 1 : 0))
                  }))
                  const increment = () => setParams(prev => ({
                    ...prev,
                    [p.key]: parseFloat(Math.min(p.max, parseFloat((prev[p.key] + p.step).toFixed(10))).toFixed(p.step < 1 ? 1 : 0))
                  }))
                  return (
                    <div key={p.key} className="space-y-3">
                      {/* Label row */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-semibold" style={{ color: 'var(--muted)' }}>{p.label}</span>
                        {autoFilled.has(p.key) && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold animate-pulse"
                            style={{ background: 'rgba(34,197,94,0.15)', color: 'var(--green)', border: '1px solid rgba(34,197,94,0.3)' }}>
                            📡 Auto
                          </span>
                        )}
                      </div>

                      {/* Stepper control */}
                      <div className="flex items-center gap-3 p-2.5 rounded-xl"
                        style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
                        <button
                          type="button"
                          onClick={decrement}
                          disabled={val <= p.min}
                          className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg transition-all active:scale-95 select-none disabled:opacity-30 hover:bg-[var(--glass-bg)]"
                          style={{
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--border-hi)',
                            color: 'var(--green)',
                          }}
                        >−</button>

                        <div className="flex-1 text-center">
                          <div className="text-lg font-bold tabular-nums leading-none" style={{ color: 'var(--on-surface)' }}>
                            {typeof val === 'number' ? val.toFixed(p.step < 1 ? (p.step < 0.5 ? 1 : 1) : 0) : val}
                          </div>
                          <div className="text-[10px] mt-1" style={{ color: 'var(--muted)' }}>
                            step {p.step}
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={increment}
                          disabled={val >= p.max}
                          className="w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg transition-all active:scale-95 select-none disabled:opacity-30 hover:bg-[var(--glass-bg)]"
                          style={{
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--border-hi)',
                            color: 'var(--green)',
                          }}
                        >+</button>
                      </div>

                      {/* Slider */}
                      <input
                        type="range"
                        min={p.min} max={p.max} step={p.step}
                        value={val}
                        onChange={e => setParams(prev => ({ ...prev, [p.key]: parseFloat(e.target.value) }))}
                        className="w-full"
                        style={{ accentColor: 'var(--green)' }}
                      />

                      {/* Min / Max labels */}
                      <div className="flex justify-between text-[10px]" style={{ color: 'var(--muted)' }}>
                        <span>{p.min}</span>
                        <span>{p.max}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
            
            {fields.length > 0 && (
              <div className="card p-5">
                <label className="text-sm font-semibold text-agro-300 mb-3 block">Assign to Field (Optional)</label>
                <div className="relative">
                  <select className="input text-sm py-2.5 appearance-none pr-10"
                    value={fieldId} onChange={e => setFieldId(e.target.value)}>
                    <option value="">No field (scan only)</option>
                    {fields.map(f => <option key={f.id} value={f.id}>{f.name}{f.crop_type ? ` (${f.crop_type})` : ''}</option>)}
                  </select>
                  <ChevronDown size={14} className="absolute right-4 top-1/2 -translate-y-1/2 text-agro-600 pointer-events-none" />
                </div>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <button onClick={() => setCurrentStep(1)} className="btn-secondary px-6 py-3 text-sm font-medium">
                ← Back
              </button>
              <button onClick={() => setCurrentStep(3)} className="btn-primary px-8 py-3 text-sm font-semibold">
                Next: Review & Run →
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Review & Run Pipeline */}
        {currentStep === 3 && (
          <div className="space-y-6 animate-fade-in">
            <div className="card p-6 border-2 border-[var(--border-hi)] shadow-[0_0_30px_rgba(34,197,94,0.05)]">
              <h3 className="text-lg font-bold text-[var(--on-surface)] mb-4">Review Your Scan Setup</h3>
              
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="space-y-1">
                  <div className="text-xs text-[var(--muted)]">Crop Type</div>
                  <div className="text-sm font-semibold text-[var(--green)]">{crop}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-[var(--muted)]">Location</div>
                  <div className="text-sm font-medium text-[var(--on-surface)]">
                    {lat && lon ? `${parseFloat(lat).toFixed(4)}°, ${parseFloat(lon).toFixed(4)}°` : 'Not provided'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-[var(--muted)]">Field Assignment</div>
                  <div className="text-sm font-medium text-[var(--on-surface)]">
                    {fieldId ? fields.find(f => f.id === fieldId)?.name || 'Unknown' : 'None'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-[var(--muted)]">Environment</div>
                  <div className="text-sm font-medium text-[var(--on-surface)]">
                    {params.temperature}°C, {params.humidity}% Hum
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-xl border bg-[var(--glass-bg2)] border-[var(--border)] mb-6">
                <div className="text-sm font-semibold text-agro-400 mb-3 flex items-center gap-2">
                  <Zap size={14} className="text-[var(--amber)]" /> What the AI pipeline will do
                </div>
                <ul className="space-y-2 text-xs text-agro-600">
                  {[
                    '✅ Validates image is a leaf (rejects non-plant)',
                    'Identifies specific disease name (e.g. Early Blight)',
                    'Soil & weather risk scoring (pH, humidity, rainfall)',
                    'Weather-disease correlation (Wallin blight model)',
                    'Geo-outbreak probability mapping',
                    '7-day disease progression forecast',
                    'Carbon footprint of treatment options',
                    'RL-optimised cost-effective treatment plan',
                    '🛒 Finds nearby agri shops via Google Maps',
                  ].map((t, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      {!t.startsWith('✅') && !t.startsWith('🛒') && <span className="text-agro-500 mt-0.5">→</span>}
                      <span style={{ color: t.startsWith('✅') ? 'var(--green)' : t.startsWith('🛒') ? 'var(--amber)' : undefined }}>{t}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {scanning && (
                <div className="mb-6 p-5 rounded-xl border border-[var(--border-hi)] bg-[var(--glass-bg)] flex flex-col items-center justify-center gap-4">
                  <Loader size={28} className="text-agro-400 animate-spin" />
                  <div className="text-center w-full">
                    <div className="text-sm font-medium text-agro-200 mb-2">{scanMsg}</div>
                    <div className="w-full h-2 rounded-full overflow-hidden bg-[var(--glass-bg2)]">
                      <div className="h-full rounded-full transition-all duration-500 bg-[var(--green)]"
                        style={{ width: `${scanPct}%` }} />
                    </div>
                    <div className="text-xs text-agro-600 mt-2">{scanPct}% complete</div>
                  </div>
                </div>
              )}

              <div className="flex gap-4">
                <button 
                  onClick={() => setCurrentStep(2)} 
                  disabled={scanning}
                  className="btn-secondary px-6 py-4 text-sm font-medium flex-1 max-w-[120px] disabled:opacity-40">
                  ← Back
                </button>
                <button 
                  onClick={runScan} 
                  disabled={scanning}
                  className={clsx('flex-1 flex items-center justify-center gap-2 py-4 rounded-xl font-bold text-base transition-all btn-primary shadow-lg',
                    scanning && 'opacity-60 cursor-not-allowed')}>
                  {scanning
                    ? <><Loader size={18} className="animate-spin" /> Analysing Pipeline…</>
                    : <><ScanLine size={18} /> Run AI Pipeline</>}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
