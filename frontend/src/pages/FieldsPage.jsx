import React, { useState } from 'react'
import { useApp } from "../App";
import { createField, updateField as apiUpdate, deleteField as apiDelete, getFieldData } from '../api/api'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, Edit2, MapPin, Leaf, Layers, X, Check, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const CROP_TYPES = ['Wheat', 'Rice', 'Maize', 'Cotton', 'Sugarcane', 'Tomato', 'Potato', 'Soybean', 'Groundnut', 'Mixed']

function FieldForm({ initial = {}, onSave, onCancel, saving }) {
  const [form, setForm] = useState({
    name: initial.name || '',
    crop_type: initial.crop_type || '',
    location: initial.location || '',
    area_acres: initial.area_acres || '',
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="card p-5 border-agro-700/40 space-y-4">
      <div className="text-sm font-semibold text-agro-200">{initial.id ? 'Edit Field' : 'New Field'}</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-agro-500 mb-1 block">Field Name *</label>
          <input className="input text-sm" placeholder="e.g. North Field" value={form.name} onChange={e => set('name', e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-agro-500 mb-1 block">Crop Type</label>
          <select className="input text-sm" value={form.crop_type} onChange={e => set('crop_type', e.target.value)}>
            <option value="">Select crop...</option>
            {CROP_TYPES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-agro-500 mb-1 block">Location</label>
          <input className="input text-sm" placeholder="e.g. Village, District" value={form.location} onChange={e => set('location', e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-agro-500 mb-1 block">Area (acres)</label>
          <input className="input text-sm" type="number" min="0" step="0.5" placeholder="e.g. 5.5" value={form.area_acres} onChange={e => set('area_acres', e.target.value)} />
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={() => onSave(form)}
          disabled={!form.name.trim() || saving}
          className={clsx('btn-primary text-sm', (!form.name.trim() || saving) && 'opacity-50 cursor-not-allowed')}
        >
          <Check size={14} /> {saving ? 'Saving...' : initial.id ? 'Update' : 'Create Field'}
        </button>
        <button onClick={onCancel} className="btn-ghost text-sm">
          <X size={14} /> Cancel
        </button>
      </div>
    </div>
  )
}

export default function FieldsPage() {
  const { fields, addField, updateField, removeField, setActiveField, activeField } = useApp()
  const navigate = useNavigate()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [fieldScans, setFieldScans] = useState({})
  const [loadingScans, setLoadingScans] = useState({})

  const handleCreate = async (form) => {
    if (!form.name.trim()) return toast.error('Field name required')
    setSaving(true)
    try {
      const field = await createField({
        name: form.name,
        location: form.location,
        crop_type: form.crop_type,
        area_acres: parseFloat(form.area_acres) || 0,
      })
      addField(field)
      setShowForm(false)
      toast.success(`Field "${field.name}" created!`)
    } catch (e) {
      toast.error('Failed to create field')
    } finally {
      setSaving(false)
    }
  }

  const handleUpdate = async (form, id) => {
    setSaving(true)
    try {
      const field = await apiUpdate(id, {
        name: form.name,
        location: form.location,
        crop_type: form.crop_type,
        area_acres: parseFloat(form.area_acres) || 0,
      })
      updateField(field)
      setEditingId(null)
      toast.success('Field updated!')
    } catch (e) {
      toast.error('Failed to update field')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (field) => {
    if (!window.confirm(`Delete field "${field.name}"? This won't delete its scans.`)) return
    try {
      await apiDelete(field.id)
      removeField(field.id)
      if (activeField === field.id) setActiveField(null)
      toast.success('Field deleted')
    } catch (e) {
      toast.error('Failed to delete field')
    }
  }

  const loadFieldScans = async (fieldId) => {
    if (fieldScans[fieldId]) return
    setLoadingScans(p => ({ ...p, [fieldId]: true }))
    try {
      const data = await getFieldData(fieldId)
      setFieldScans(p => ({ ...p, [fieldId]: data.scans || [] }))
    } catch {}
    setLoadingScans(p => ({ ...p, [fieldId]: false }))
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-agro-100">My Fields</h1>
          <p className="text-agro-600 text-sm mt-0.5">{fields.length} field{fields.length !== 1 ? 's' : ''} registered</p>
        </div>
        <button onClick={() => { setShowForm(true); setEditingId(null) }} className="btn-primary">
          <Plus size={15} /> Add Field
        </button>
      </div>

      {showForm && (
        <FieldForm
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
          saving={saving}
        />
      )}

      {fields.length === 0 && !showForm ? (
        <div className="flex flex-col items-center py-16 text-agro-700 gap-3">
          <Layers size={48} strokeWidth={1} />
          <div className="text-base font-medium text-agro-500">No fields yet</div>
          <div className="text-sm text-center max-w-xs">
            Create fields to organize your scans, track crop health per field, and compare trends.
          </div>
          <button onClick={() => setShowForm(true)} className="btn-primary mt-2">
            <Plus size={14} /> Create First Field
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {fields.map(field => (
            <div key={field.id}>
              {editingId === field.id ? (
                <FieldForm
                  initial={field}
                  onSave={form => handleUpdate(form, field.id)}
                  onCancel={() => setEditingId(null)}
                  saving={saving}
                />
              ) : (
                <div className={clsx('card p-5 transition-all', activeField === field.id && 'border-agro-600/40 shadow-agro')}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-agro-900/40 border border-agro-800/30 flex items-center justify-center flex-shrink-0">
                        <Leaf size={18} className="text-agro-400" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-base font-semibold text-agro-100">{field.name}</h3>
                          {activeField === field.id && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-agro-700/40 border border-agro-600/30 text-agro-300">Active</span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 mt-1 flex-wrap">
                          {field.crop_type && (
                            <div className="flex items-center gap-1.5 text-xs text-agro-500">
                              <Leaf size={10} /> {field.crop_type}
                            </div>
                          )}
                          {field.location && (
                            <div className="flex items-center gap-1.5 text-xs text-agro-600">
                              <MapPin size={10} /> {field.location}
                            </div>
                          )}
                          {field.area_acres > 0 && (
                            <div className="text-xs text-agro-700">{field.area_acres} acres</div>
                          )}
                          <div className="text-xs text-agro-700">
                            Created {new Date(field.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        onClick={() => { setActiveField(field.id); toast.success(`Switched to ${field.name}`) }}
                        className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                          activeField === field.id
                            ? 'bg-agro-700/40 text-agro-300 border border-agro-600/40'
                            : 'bg-surface-200 text-agro-600 hover:text-agro-300 border border-surface-border'
                        )}
                      >
                        {activeField === field.id ? 'Selected' : 'Select'}
                      </button>
                      <button
                        onClick={() => { setEditingId(field.id); setShowForm(false) }}
                        className="btn-ghost p-2"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button onClick={() => handleDelete(field)} className="btn-danger p-2">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  {/* Field scans summary */}
                  <div className="mt-4 pt-4 border-t border-surface-border flex items-center justify-between">
                    <button
                      onClick={() => loadFieldScans(field.id)}
                      className="text-xs text-agro-600 hover:text-agro-400 transition-colors flex items-center gap-1.5"
                    >
                      {loadingScans[field.id] ? 'Loading...' : fieldScans[field.id] ? `${fieldScans[field.id].length} scans` : 'Load scan count'}
                    </button>
                    <button
                      onClick={() => { setActiveField(field.id); navigate('/history') }}
                      className="text-xs text-agro-500 hover:text-agro-300 flex items-center gap-1 transition-colors"
                    >
                      View scans <ChevronRight size={12} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}