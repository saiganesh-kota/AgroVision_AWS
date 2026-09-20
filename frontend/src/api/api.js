import axios from 'axios'
import { getCurrentUser } from '../utils/storage'

const BASE = import.meta.env.VITE_API_URL || ''
const api  = axios.create({ baseURL: BASE, timeout: 120000 })

// ── Attach X-User-Id to EVERY request so backend can isolate data per user ──
api.interceptors.request.use(config => {
  const user = getCurrentUser()
  if (user?.id) config.headers['X-User-Id'] = user.id
  return config
})

export const predict        = (fd)           => api.post('/predict', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
export const getDashboard   = (fieldId)      => api.get('/dashboard', { params: { field_id: fieldId } }).then(r => r.data)
export const getHealthTrend = (fieldId, days)=> api.get('/health-trend', { params: { field_id: fieldId, days } }).then(r => r.data)
export const getHistory     = (limit = 100, fieldId) => api.get('/history', { params: { limit, field_id: fieldId } }).then(r => r.data)
export const getScan        = (id)           => api.get(`/scan/${id}`).then(r => r.data)
export const getGeoPoints   = ()             => api.get('/geo-points').then(r => r.data)
export const fetchWeather   = (lat, lon)     => api.get('/weather', { params: { lat, lon } }).then(r => r.data)
export const chat           = (message, ctx, lang = 'en', history = []) => api.post('/chat', { message, context: ctx, lang, history }).then(r => r.data)
export const checkHealth    = ()             => api.get('/health').then(r => r.data)

export const getFields    = ()              => api.get('/fields').then(r => Array.isArray(r.data) ? r.data : [])
export const createField  = (data)          => api.post('/fields', data).then(r => r.data)
export const updateField  = (id, data)      => api.put(`/fields/${id}`, data).then(r => r.data)
export const deleteField  = (id)            => api.delete(`/fields/${id}`).then(r => r.data)
export const getFieldData = (id)            => api.get(`/fields/${id}/data`).then(r => r.data)

export const getSuppliers        = (lat, lon, radius = 15000) => api.get('/suppliers', { params: { lat, lon, radius } }).then(r => r.data)
export const getWeatherRisk      = (temp, humidity, rainfall, crop) => api.get('/weather-risk', { params: { temp, humidity, rainfall, crop } }).then(r => r.data)
export const getCarbonFootprint  = (action, acres) => api.get('/carbon-footprint', { params: { action, acres } }).then(r => r.data)
export const getCertificate      = (scanId) => api.get(`/certificate/${scanId}`).then(r => r.data)

export const getFeedbackStats   = ()             => api.get('/feedback/stats').then(r => r.data)
export const getPestAlerts      = (params)       => api.get('/pest-alerts', { params }).then(r => r.data)
export const getSoilParams      = (lat, lon)     => api.get('/soil-params', { params: { lat, lon } }).then(r => r.data)
export const getHealthBreakdown = (data)         => api.post('/health-breakdown', data).then(r => r.data)
export const submitFeedback     = (data)         => api.post('/feedback', data).then(r => r.data)

export const getSchemes         = (params)       => api.get('/schemes', { params }).then(r => r.data)
export const getSchemesMeta     = ()             => api.get('/schemes/meta').then(r => r.data)
export const getSchemesByCrop   = (crop, state)  => api.get('/schemes/for-crop', { params: { crop, state } }).then(r => r.data)
export const getContacts        = (params)       => api.get('/contacts', { params }).then(r => r.data)

// ── Geospatial Intelligence Engine (Patent XII-XIII) ──────────────────────
export const getSpatialRecord   = (lat, lon)                     => api.get('/geo/spatial-record', { params: { lat, lon } }).then(r => r.data)
export const getGeoHeatmap      = (lat, lon, radius = 500, days = 30) => api.get('/geo/heatmap', { params: { lat, lon, radius, days } }).then(r => r.data)
export const getGeoForecast     = (lat, lon, days = 7, humidity = 65, rainfall = 80) => api.get('/geo/forecast', { params: { lat, lon, days, humidity, rainfall } }).then(r => r.data)
export const getDiseaseHotspots = (top_n = 10)                   => api.get('/geo/disease-hotspots', { params: { top_n } }).then(r => r.data)
export const getZoneAlerts      = (lat, lon, radius = 300)       => api.get('/geo/zone-alerts', { params: { lat, lon, radius } }).then(r => r.data)
