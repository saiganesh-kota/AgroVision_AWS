import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../App'
import { getSchemes, getSchemesMeta, getContacts } from '../api/api'
import { useLang } from '../utils/LangContext'
import { t } from '../utils/i18n'
import clsx from 'clsx'
import {
  Search, Filter, Phone, Mail, Clock, ExternalLink, MapPin,
  ChevronDown, ChevronUp, Globe, BookOpen, X, Building2
} from 'lucide-react'

const LANG_OPTIONS = [
  { code:'en', label:'English' },
  { code:'te', label:'తెలుగు (Telugu)' },
  { code:'hi', label:'हिंदी (Hindi)' },
]

const CATEGORY_ICONS = {
  'Income Support':   '💰',
  'Crop Insurance':   '🛡️',
  'Credit & Loans':   '💳',
  'Organic Farming':  '🌱',
  'Infrastructure':   '🏗️',
  'Equipment Subsidy':'🚜',
  'Soil Health':      '🧪',
}

// ── Scheme Card ───────────────────────────────────────────────────────────────
function SchemeCard({ s, lang, uiLang }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={clsx('card p-5 transition-all duration-300', expanded && 'border')}
      style={{ borderColor: expanded ? 'var(--border-hi)' : 'var(--border)' }}>
      <div className="flex items-start gap-4">
        <div className="text-3xl shrink-0">{s.icon || '📋'}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-bold text-agro-100">{s.name}</h3>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                  style={{ background:'var(--glass-bg2)', color:'var(--green)', border:'1px solid var(--border-hi)' }}>
                  {CATEGORY_ICONS[s.category] || '📋'} {s.category}
                </span>
              </div>
              <p className="text-xs text-agro-500 mt-0.5">{s.full_name}</p>
            </div>
            {s.deadline && (
              <span className="text-[10px] text-agro-600 flex items-center gap-1 shrink-0">
                <Clock size={10} /> {s.deadline}
              </span>
            )}
          </div>

          {/* Local language description */}
          {lang !== 'en' && s.local_description && (
            <div className="mt-2 px-3 py-1.5 rounded-lg text-xs font-medium"
              style={{ background:'rgba(139,92,246,0.08)', color:'#a78bfa', border:'1px solid rgba(139,92,246,0.2)' }}>
              🌐 {s.local_description}
            </div>
          )}

          <div className="mt-2 p-2.5 rounded-lg text-xs text-agro-300 font-medium"
            style={{ background:'var(--glass-bg2)', border:'1px solid var(--border)' }}>
            💡 {s.benefit}
          </div>
        </div>
      </div>

      {/* Expandable details */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full mt-3 flex items-center justify-center gap-1.5 text-xs text-agro-500 hover:text-agro-300 transition-colors py-1.5"
      >
        {expanded ? <><ChevronUp size={13} /> {t(uiLang,'hide_details')}</> : <><ChevronDown size={13} /> {t(uiLang,'view_eligibility')}</>}
      </button>

      {expanded && (
        <div className="mt-3 pt-3 border-t space-y-3" style={{ borderColor:'var(--border)' }}>
          <div>
            <p className="text-[10px] font-semibold text-agro-600 uppercase tracking-wider mb-1.5">{t(uiLang,'eligibility')}</p>
            <p className="text-xs text-agro-400 leading-relaxed">{s.eligibility}</p>
          </div>

          <div>
            <p className="text-[10px] font-semibold text-agro-600 uppercase tracking-wider mb-1.5">{t(uiLang,'documents')}</p>
            <div className="flex flex-wrap gap-1.5">
              {s.documents?.map((d, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full"
                  style={{ background:'var(--glass-bg2)', color:'var(--muted)', border:'1px solid var(--border)' }}>
                  {d}
                </span>
              ))}
            </div>
          </div>

          <div>
            <p className="text-[10px] font-semibold text-agro-600 uppercase tracking-wider mb-1.5">{t(uiLang,'how_to_apply')}</p>
            <p className="text-xs text-agro-400 leading-relaxed">{s.how_to_apply}</p>
          </div>

          <div className="flex items-center gap-3">
            {s.link && (
              <a href={s.link} target="_blank" rel="noopener noreferrer"
                className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5">
                <ExternalLink size={12} /> Apply Online
              </a>
            )}
            <div className="flex flex-wrap gap-1.5">
              {s.crops?.filter(c => c !== 'All Crops').slice(0, 4).map(c => (
                <span key={c} className="text-[10px] px-2 py-0.5 rounded-full badge-low">{c}</span>
              ))}
              {s.crops?.includes('All Crops') && <span className="badge-low text-[10px]">All Crops</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Contact Card ──────────────────────────────────────────────────────────────
function ContactCard({ c }) {
  return (
    <div className="card p-4 hover:border-agro-700/40 transition-all">
      <div className="flex items-start gap-3">
        <div className="text-2xl shrink-0">{c.icon || '📞'}</div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-agro-200">{c.name}</p>
          <span className="text-[10px] px-2 py-0.5 rounded-full mt-1 inline-block"
            style={{ background:'var(--glass-bg2)', color:'var(--muted)', border:'1px solid var(--border)' }}>
            {c.type}
          </span>
          <div className="mt-2 space-y-1">
            {c.phone && (
              <a href={`tel:${c.phone}`} className="flex items-center gap-2 text-xs text-agro-400 hover:text-agro-200 transition-colors">
                <Phone size={11} style={{ color:'var(--green)' }} />
                <span className="font-mono font-semibold">{c.phone}</span>
              </a>
            )}
            {c.email && (
              <a href={`mailto:${c.email}`} className="flex items-center gap-2 text-xs text-agro-500 hover:text-agro-300 transition-colors">
                <Mail size={11} /> {c.email}
              </a>
            )}
            {c.hours && (
              <div className="flex items-center gap-2 text-xs text-agro-600">
                <Clock size={11} /> {c.hours}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function SchemesPage() {
  const navigate = useNavigate()
  const { currentField } = useApp()
  const { lang: uiLang } = useLang()

  const [schemes,    setSchemes]    = useState([])
  const [contacts,   setContacts]   = useState([])
  const [meta,       setMeta]       = useState({ categories:[], states:[] })
  const [loading,    setLoading]    = useState(true)
  const [tab,        setTab]        = useState('schemes')

  // Filters
  const [search,   setSearch]   = useState('')
  const [crop,     setCrop]     = useState('')
  const [state,    setState_]   = useState('')
  const [category, setCategory] = useState('')
  const [lang,     setLang]     = useState('en')

  const CROPS = ['Wheat','Rice','Maize','Cotton','Sugarcane','Tomato','Potato','Soybean','Groundnut']

  useEffect(() => {
    getSchemesMeta().then(setMeta).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getSchemes({ crop: crop || undefined, state: state || undefined, category: category || undefined, lang }).catch(() => []),
      getContacts({ state: state || undefined }).catch(() => []),
    ]).then(([s, c]) => {
      setSchemes(s)
      setContacts(c)
      setLoading(false)
    })
  }, [crop, state, category, lang])

  const filteredSchemes = schemes.filter(s =>
    !search || s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.full_name.toLowerCase().includes(search.toLowerCase()) ||
    s.benefit.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-agro-100 flex items-center gap-2">
            🏛️ Govt Schemes & Support
          </h1>
          <p className="text-agro-600 text-sm mt-0.5">
            Agricultural subsidies, insurance, loans &amp; local contacts
          </p>
        </div>
        {/* Language switcher */}
        <div className="flex items-center gap-1.5 glass-light rounded-xl p-1">
          {LANG_OPTIONS.map(l => (
            <button key={l.code} onClick={() => setLang(l.code)}
              className={clsx('text-xs px-3 py-1.5 rounded-lg transition-all', lang === l.code ? 'text-white' : 'text-agro-500 hover:text-agro-300')}
              style={{ background: lang === l.code ? 'var(--green)' : 'transparent' }}>
              {l.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 glass-light rounded-2xl p-1.5">
        {[
          { id:'schemes',  label:`📋 Schemes (${filteredSchemes.length})` },
          { id:'contacts', label:`📞 Contacts (${contacts.length})` },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={clsx('flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all', tab === t.id ? 'text-white' : 'text-agro-500 hover:text-agro-300')}
            style={{ background: tab === t.id ? 'var(--green)' : 'transparent' }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-3">
          {/* Search */}
          <div className="flex-1 min-w-48 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-agro-600" />
            <input className="input pl-9 text-sm py-2" placeholder={t(uiLang,'search_schemes')}
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>

          {/* Crop filter */}
          <div className="relative">
            <select className="input text-xs py-2 appearance-none pr-8 min-w-36"
              value={crop} onChange={e => setCrop(e.target.value)}>
              <option value="">{t(uiLang,'all_crops')}</option>
              {CROPS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <ChevronDown size={11} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-agro-600 pointer-events-none" />
          </div>

          {/* State filter */}
          <div className="relative">
            <select className="input text-xs py-2 appearance-none pr-8 min-w-40"
              value={state} onChange={e => setState_(e.target.value)}>
              <option value="">{t(uiLang,'all_states')}</option>
              {meta.states.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <ChevronDown size={11} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-agro-600 pointer-events-none" />
          </div>

          {/* Category filter */}
          {tab === 'schemes' && (
            <div className="relative">
              <select className="input text-xs py-2 appearance-none pr-8 min-w-44"
                value={category} onChange={e => setCategory(e.target.value)}>
                <option value="">All Categories</option>
                {meta.categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <ChevronDown size={11} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-agro-600 pointer-events-none" />
            </div>
          )}

          {(search || crop || state || category) && (
            <button onClick={() => { setSearch(''); setCrop(''); setState_(''); setCategory('') }}
              className="btn-ghost text-xs py-2 flex items-center gap-1 text-agro-500">
              <X size={12} /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Category quick filters */}
      {tab === 'schemes' && (
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          <button onClick={() => setCategory('')}
            className={clsx('text-xs whitespace-nowrap px-3 py-1.5 rounded-full shrink-0 transition-all border',
              !category ? 'text-white border-transparent' : 'text-agro-500 border-agro-800')}
            style={{ background: !category ? 'var(--green)' : 'var(--glass-bg2)' }}>
            All
          </button>
          {meta.categories.map(cat => (
            <button key={cat} onClick={() => setCategory(cat === category ? '' : cat)}
              className={clsx('text-xs whitespace-nowrap px-3 py-1.5 rounded-full shrink-0 transition-all border',
                category === cat ? 'text-white border-transparent' : 'text-agro-500 border-agro-800')}
              style={{ background: category === cat ? 'var(--green)' : 'var(--glass-bg2)' }}>
              {CATEGORY_ICONS[cat] || '📋'} {cat}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_,i) => (
            <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background:'var(--glass-bg2)' }} />
          ))}
        </div>
      ) : tab === 'schemes' ? (
        filteredSchemes.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-3 text-agro-700">
            <BookOpen size={40} strokeWidth={1} />
            <p className="text-base font-medium text-agro-500">No schemes found</p>
            <p className="text-sm">Try adjusting your filters</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredSchemes.map(s => <SchemeCard key={s.id} s={s} lang={lang} uiLang={uiLang} />)}
          </div>
        )
      ) : (
        /* Contacts tab */
        contacts.length === 0 ? (
          <div className="flex flex-col items-center py-16 gap-3 text-agro-700">
            <Phone size={40} strokeWidth={1} />
            <p className="text-base font-medium text-agro-500">No contacts found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {contacts.map(c => <ContactCard key={c.id} c={c} />)}

            {/* Emergency helpline banner */}
            <div className="sm:col-span-2 p-4 rounded-2xl border"
              style={{ background:'rgba(34,197,94,0.06)', borderColor:'var(--border-hi)' }}>
              <div className="flex items-center gap-3">
                <div className="text-3xl">🆘</div>
                <div>
                  <p className="text-sm font-bold text-agro-100">Kisan Call Centre — 24×7 Helpline</p>
                  <p className="text-xs text-agro-500 mt-0.5">Free advisory service in 21 languages</p>
                </div>
                <a href="tel:1800-180-1551"
                  className="ml-auto btn-primary text-sm flex items-center gap-2 shrink-0">
                  <Phone size={14} /> 1800-180-1551
                </a>
              </div>
            </div>
          </div>
        )
      )}
    </div>
  )
}
