export const markerColor = (geo_risk) =>
  geo_risk === 'High' ? '#ef4444' : geo_risk === 'Medium' ? '#f59e0b' : '#22c55e'

export const riskBadgeClass = (risk = '') => {
  const r = risk.toLowerCase()
  if (r === 'high' || r === 'critical') return 'badge-high'
  if (r === 'medium' || r === 'moderate') return 'badge-medium'
  return 'badge-low'
}

export const sevBadgeClass = (sev = '') => {
  const s = sev.toLowerCase()
  if (s === 'critical') return 'badge-critical'
  if (s === 'high')     return 'badge-high'
  if (s === 'moderate') return 'badge-medium'
  return 'badge-low'
}

export const formatDate = (iso) => {
  try {
    return new Date(iso).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
    })
  } catch { return iso }
}

export const normConf = (v) => {
  if (v == null) return 0
  return v > 1 ? v : v * 100
}

export const normSev = (v) => {
  if (v == null) return 0
  return v > 1 ? v : v * 100
}
