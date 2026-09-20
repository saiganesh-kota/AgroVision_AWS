import React, { useState } from 'react'
import { useLang } from '../utils/LangContext'
import { LANGUAGES } from '../utils/i18n'
import { Globe } from 'lucide-react'

export default function LangSwitcher({ compact = false }) {
  const { lang, setLang } = useLang()
  const [open, setOpen] = useState(false)
  const current = LANGUAGES.find(l => l.code === lang) || LANGUAGES[0]

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all"
        style={{ background: 'var(--glass-bg2)', color: 'var(--muted)', border: '1px solid var(--border)' }}
        title="Change language">
        <Globe size={13} />
        {!compact && <span>{current.flag} {current.label}</span>}
        {compact && <span>{current.flag}</span>}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 z-50 rounded-xl shadow-xl overflow-hidden min-w-40"
            style={{ background: 'var(--glass-bg)', border: '1px solid var(--border)', backdropFilter: 'blur(16px)' }}>
            {LANGUAGES.map(l => (
              <button key={l.code}
                onClick={() => { setLang(l.code); setOpen(false) }}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 text-xs font-medium transition-colors text-left"
                style={{
                  background: l.code === lang ? 'var(--glass-bg2)' : 'transparent',
                  color: l.code === lang ? 'var(--on-surface)' : 'var(--muted)',
                  borderBottom: '1px solid var(--border)',
                }}>
                <span className="text-base">{l.flag}</span>
                <span>{l.label}</span>
                {l.code === lang && <span className="ml-auto text-[10px]" style={{ color: 'var(--green)' }}>✓</span>}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
