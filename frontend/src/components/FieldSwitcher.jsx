import React, { useState } from 'react'
import { ChevronDown, Plus, X, Check } from 'lucide-react'
import { useApp } from '../App'
import { createField } from '../api/api'
import toast from 'react-hot-toast'

export default function FieldSwitcher() {
  const { fields, activeField, setActiveField, addField } = useApp()
  const [open, setOpen]     = useState(false)
  const [adding, setAdding] = useState(false)
  const [name, setName]     = useState('')
  const [saving, setSaving] = useState(false)

  const selected = fields.find(f => f.id === activeField) || null
  const label    = selected?.name || 'All Fields'

  async function handleAdd() {
    if (!name.trim()) return
    setSaving(true)
    try {
      const f = await createField({ name: name.trim() })
      addField(f)
      setActiveField(f.id)
      setName('')
      setAdding(false)
      toast.success(`Field "${f.name}" created!`)
    } catch { toast.error('Failed to create field') }
    finally { setSaving(false) }
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between glass-light rounded-xl px-3 py-2 text-sm font-medium"
        style={{ color: 'var(--green)' }}>
        <span className="truncate">{label}</span>
        <ChevronDown size={14} className={`ml-2 transition-transform shrink-0 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute top-full mt-1 w-full glass rounded-xl z-50 overflow-hidden"
          style={{ boxShadow: '0 8px 32px var(--shadow)' }}>

          {/* All fields option */}
          <div onClick={() => { setActiveField(null); setOpen(false) }}
            className="flex items-center justify-between px-3 py-2 text-sm cursor-pointer transition-colors"
            style={{ color: !activeField ? 'var(--green)' : 'var(--on-surface)' }}
            onMouseEnter={e => e.currentTarget.style.background = 'var(--glass-bg2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
            <span>All Fields</span>
            {!activeField && <Check size={12} style={{ color: 'var(--green)' }} />}
          </div>

          {fields.map(f => (
            <div key={f.id} onClick={() => { setActiveField(f.id); setOpen(false) }}
              className="flex items-center justify-between px-3 py-2 text-sm cursor-pointer transition-colors"
              style={{ color: activeField === f.id ? 'var(--green)' : 'var(--on-surface)' }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--glass-bg2)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <span className="truncate">{f.name}</span>
              {activeField === f.id && <Check size={12} style={{ color: 'var(--green)' }} />}
            </div>
          ))}

          {adding ? (
            <div className="p-2 border-t" style={{ borderColor: 'var(--border)' }}>
              <input className="input-field text-xs py-1.5 mb-2" placeholder="Field name"
                value={name} onChange={e => setName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAdd()} autoFocus />
              <div className="flex gap-1">
                <button onClick={handleAdd} disabled={saving || !name.trim()} className="btn-primary text-xs py-1.5 px-3 flex-1">
                  {saving ? 'Saving…' : 'Create'}
                </button>
                <button onClick={() => { setAdding(false); setName('') }} className="btn-secondary text-xs py-1.5 px-3">
                  <X size={12} />
                </button>
              </div>
            </div>
          ) : (
            <button onClick={() => setAdding(true)}
              className="w-full flex items-center gap-2 px-3 py-2 text-xs border-t transition-colors"
              style={{ borderColor: 'var(--border)', color: 'var(--muted)' }}
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--green)'; e.currentTarget.style.background = 'var(--glass-bg2)' }}
              onMouseLeave={e => { e.currentTarget.style.color = 'var(--muted)';  e.currentTarget.style.background = 'transparent' }}>
              <Plus size={12} /> Add Field
            </button>
          )}
        </div>
      )}
    </div>
  )
}
