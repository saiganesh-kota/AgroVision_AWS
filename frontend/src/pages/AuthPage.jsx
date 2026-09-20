import React, { useState, useEffect } from 'react'
import {
  Leaf, Eye, EyeOff, User, Mail, Lock, Phone, MapPin, CheckCircle
} from 'lucide-react'
import { loginUser, registerUser } from '../utils/storage'
import { useApp } from '../App'
import ThemeToggle from '../components/ThemeToggle'
import LangSwitcher from '../components/LangSwitcher'
import { useLang } from '../utils/LangContext'
import { t } from '../utils/i18n'

const INDIA_STATES = [
  'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat',
  'Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh',
  'Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab',
  'Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh',
  'Uttarakhand','West Bengal','Delhi','Jammu & Kashmir'
]

function FloatingLabel({ label, icon: Icon, children }) {
  return (
    <div>
      <label className="block text-xs font-semibold uppercase tracking-wider mb-1.5 flex items-center gap-1.5"
        style={{ color: 'var(--muted)' }}>
        {Icon && <Icon size={11} />}{label}
      </label>
      {children}
    </div>
  )
}

export default function AuthPage() {
  const { handleLogin } = useApp()
  const { lang } = useLang()
  const [tab,        setTab]      = useState('signin') // 'signin' | 'signup'
  const [show,       setShow]     = useState(false)
  const [loading,    setLoading]  = useState(false)
  const [error,      setError]    = useState('')
  const [success,    setSuccess]  = useState('')
  const [stateOpen,  setStateOpen]= useState(false)

  // Sign-in fields
  const [si, setSi] = useState({ email: '', password: '' })

  // Sign-up fields
  const [su, setSu] = useState({
    name: '', email: '', password: '', confirm: '', phone: '', state: ''
  })

  useEffect(() => { setError(''); setSuccess('') }, [tab])

  // ── Sign In ──────────────────────────────────────────────────────────────
  function handleSignIn(e) {
    e.preventDefault()
    setError('')
    if (!si.email || !si.password) { setError('Please fill all fields'); return }
    setLoading(true)
    setTimeout(() => {
      const res = loginUser(si.email, si.password)
      setLoading(false)
      if (res.ok) { handleLogin() }
      else setError(res.error)
    }, 600)
  }

  // ── Sign Up ──────────────────────────────────────────────────────────────
  function handleSignUp(e) {
    e.preventDefault()
    setError('')
    if (!su.name || !su.email || !su.password) { setError('Name, email and password are required'); return }
    if (su.password.length < 6) { setError('Password must be at least 6 characters'); return }
    if (su.password !== su.confirm) { setError('Passwords do not match'); return }
    setLoading(true)
    setTimeout(() => {
      const res = registerUser(su)
      setLoading(false)
      if (res.ok) { handleLogin() }
      else setError(res.error)
    }, 700)
  }

  const FEATURES = ['🌿 AI Leaf Diagnosis', '📊 Risk Analysis', '🏛️ Govt Schemes', '🗺️ Geo Intelligence']

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{ background: 'var(--bg)' }}>

      <div className="absolute top-5 right-5 z-10 flex items-center gap-2"><LangSwitcher /><ThemeToggle /></div>

      {/* Decorative */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] rounded-full opacity-[0.07]"
          style={{ background: 'radial-gradient(circle, var(--green), transparent)' }} />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full opacity-[0.06]"
          style={{ background: 'radial-gradient(circle, var(--green-dim), transparent)' }} />
        <div className="absolute inset-0 opacity-[0.025]" style={{
          backgroundImage: 'linear-gradient(var(--green) 1px,transparent 1px),linear-gradient(90deg,var(--green) 1px,transparent 1px)',
          backgroundSize: '48px 48px'
        }} />
      </div>

      <div className="relative z-10 w-full max-w-md px-4">
        {/* Logo */}
        <div className="text-center mb-7" style={{ animation: 'float 4s ease-in-out infinite' }}>
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-3"
            style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border-hi)' }}>
            <Leaf size={30} style={{ color: 'var(--green)' }} />
          </div>
          <h1 className="text-3xl font-bold font-display tracking-tight" style={{ color: 'var(--on-surface)' }}>
            AgroVision AI
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--muted)' }}>
            Intelligent Crop Disease Detection Platform
          </p>
        </div>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2 mb-6">
          {FEATURES.map(f => (
            <span key={f} className="text-xs px-2.5 py-1 rounded-full"
              style={{ background: 'var(--glass-bg2)', color: 'var(--muted)', border: '1px solid var(--border)' }}>
              {f}
            </span>
          ))}
        </div>

        {/* Card */}
        <div className="glass rounded-2xl p-8" style={{ boxShadow: '0 24px 64px var(--shadow)' }}>
          {/* Tab switcher */}
          <div className="flex gap-1 mb-6 rounded-xl p-1" style={{ background: 'var(--glass-bg2)' }}>
            {[['signin', t(lang,'sign_in')],['signup', t(lang,'sign_up')]].map(([id, label]) => (
              <button key={id} onClick={() => setTab(id)}
                className="flex-1 py-2 rounded-lg text-sm font-semibold transition-all"
                style={{
                  background: tab === id ? 'var(--green)' : 'transparent',
                  color: tab === id ? 'white' : 'var(--muted)'
                }}>
                {label}
              </button>
            ))}
          </div>

          {/* SIGN IN FORM */}
          {tab === 'signin' && (
            <form onSubmit={handleSignIn} className="space-y-4">
              <FloatingLabel label={t(lang,'email')} icon={Mail}>
                <input type="email" className="input-field" placeholder="farmer@example.com"
                  value={si.email} onChange={e => setSi(p => ({ ...p, email: e.target.value }))} />
              </FloatingLabel>

              <FloatingLabel label={t(lang,'password')} icon={Lock}>
                <div className="relative">
                  <input type={show ? 'text' : 'password'} className="input-field pr-10"
                    placeholder="••••••••"
                    value={si.password} onChange={e => setSi(p => ({ ...p, password: e.target.value }))} />
                  <button type="button" onClick={() => setShow(s => !s)}
                    className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--muted)' }}>
                    {show ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </FloatingLabel>

              {error && <p className="text-xs flex items-center gap-1.5" style={{ color: 'var(--danger)' }}>⚠️ {error}</p>}

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3.5 mt-1">
                {loading
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Signing in…</>
                  : t(lang,'sign_in')+' →'}
              </button>

              <p className="text-center text-xs" style={{ color: 'var(--muted)' }}>
                {t(lang,'no_account')}{' '}
                <button type="button" onClick={() => setTab('signup')} className="font-semibold"
                  style={{ color: 'var(--green)' }}>{t(lang,'create_one')}</button>
              </p>
            </form>
          )}

          {/* SIGN UP FORM */}
          {tab === 'signup' && (
            <form onSubmit={handleSignUp} className="space-y-3.5">
              <FloatingLabel label={t(lang,'full_name')} icon={User}>
                <input type="text" className="input-field" placeholder="Ravi Kumar"
                  value={su.name} onChange={e => setSu(p => ({ ...p, name: e.target.value }))} />
              </FloatingLabel>

              <FloatingLabel label="Email Address" icon={Mail}>
                <input type="email" className="input-field" placeholder="farmer@example.com"
                  value={su.email} onChange={e => setSu(p => ({ ...p, email: e.target.value }))} />
              </FloatingLabel>

              <div className="grid grid-cols-2 gap-3">
                <FloatingLabel label="Password" icon={Lock}>
                  <div className="relative">
                    <input type={show ? 'text' : 'password'} className="input-field pr-8" placeholder="Min 6 chars"
                      value={su.password} onChange={e => setSu(p => ({ ...p, password: e.target.value }))} />
                    <button type="button" onClick={() => setShow(s => !s)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--muted)' }}>
                      {show ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </FloatingLabel>
                <FloatingLabel label="Confirm" icon={Lock}>
                  <input type={show ? 'text' : 'password'} className="input-field" placeholder="Repeat"
                    value={su.confirm} onChange={e => setSu(p => ({ ...p, confirm: e.target.value }))} />
                </FloatingLabel>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <FloatingLabel label={t(lang,'phone')} icon={Phone}>
                  <input type="tel" className="input-field" placeholder="+91 98765…"
                    value={su.phone} onChange={e => setSu(p => ({ ...p, phone: e.target.value }))} />
                </FloatingLabel>
                <FloatingLabel label={t(lang,'state')} icon={MapPin}>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setStateOpen(o => !o)}
                      className="input-field flex items-center justify-between text-left w-full"
                      style={{ color: su.state ? 'var(--on-surface)' : 'var(--muted)' }}
                    >
                      <span className="truncate">{su.state || 'Select state'}</span>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                        style={{ flexShrink:0, transform: stateOpen ? 'rotate(180deg)' : 'none', transition:'transform 0.2s', color:'var(--muted)' }}>
                        <polyline points="6 9 12 15 18 9"/>
                      </svg>
                    </button>
                    {stateOpen && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setStateOpen(false)} />
                        <div className="absolute left-0 right-0 mt-1 z-50 rounded-xl overflow-hidden max-h-52 overflow-y-auto"
                          style={{
                            background: 'var(--surface)',
                            border: '1px solid var(--border-hi)',
                            boxShadow: '0 12px 32px var(--shadow)',
                          }}>
                          {['', ...INDIA_STATES].map((s, i) => (
                            <button
                              key={s || '__placeholder'}
                              type="button"
                              onClick={() => { setSu(p => ({ ...p, state: s })); setStateOpen(false) }}
                              className="w-full text-left px-3 py-2 text-xs transition-all"
                              style={{
                                color: s === su.state ? 'var(--green)' : s === '' ? 'var(--muted)' : 'var(--on-surface)',
                                background: s === su.state ? 'var(--glass-bg2)' : 'transparent',
                                fontWeight: s === su.state ? 600 : 400,
                                borderBottom: i < INDIA_STATES.length ? '1px solid var(--border)' : 'none',
                              }}
                              onMouseEnter={e => { if (s !== su.state) e.currentTarget.style.background = 'var(--glass-bg2)' }}
                              onMouseLeave={e => { if (s !== su.state) e.currentTarget.style.background = 'transparent' }}
                            >
                              {s || 'Select state'}
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                </FloatingLabel>
              </div>

              {error && <p className="text-xs" style={{ color: 'var(--danger)' }}>⚠️ {error}</p>}

              <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3.5">
                {loading
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Creating account…</>
                  : t(lang,'create_start')}
              </button>

              <p className="text-center text-xs" style={{ color: 'var(--muted)' }}>
                {t(lang,'have_account')}{' '}
                <button type="button" onClick={() => setTab('signin')} className="font-semibold"
                  style={{ color: 'var(--green)' }}>{t(lang,'sign_in')}</button>
              </p>
            </form>
          )}
        </div>

        <p className="text-center text-xs mt-4" style={{ color: 'var(--muted)' }}>
          AgroVision AI · Patent-Pending ML + Reinforcement Learning
        </p>
      </div>

      <style>{`@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}`}</style>
    </div>
  )
}
