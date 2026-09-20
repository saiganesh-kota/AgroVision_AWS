import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { isLoggedIn, getCurrentUser, getLastResult, logout as storageLogout } from './utils/storage'
import { ThemeProvider } from './utils/ThemeContext'
import { LangProvider } from './utils/LangContext'
import { getFields } from './api/api'

import AuthPage           from './pages/AuthPage'
import DashboardPage      from './pages/DashboardPage'
import ScanPage           from './pages/ScanPage'
import AnalysisPage       from './pages/AnalysisPage'
import RecommendationPage from './pages/RecommendationPage'
import HistoryPage        from './pages/HistoryPage'
import GeoMapPage         from './pages/GeoMapPage'
import ChatPage           from './pages/ChatPage'
import FieldsPage         from './pages/FieldsPage'
import SchemesPage        from './pages/SchemesPage'
import CropCalendarPage    from './pages/CropCalendarPage'
import YieldEstimatorPage  from './pages/YieldEstimatorPage'
import PestAlertsPage      from './pages/PestAlertsPage'
import ShopsPage           from './pages/ShopsPage'
import Layout             from './components/Layout'
import ChatBot from './components/ChatBot'

export const AppContext = createContext(null)
export const useApp = () => useContext(AppContext)

export default function App() {
  // ── Reactive auth state — single source of truth ──────────────────────────
  const [authed, setAuthed] = useState(() => isLoggedIn())

  const [lastResult,  setLastResult]  = useState(() => getLastResult())
  const [activeScan,  setActiveScan]  = useState(() => {
    const r = getLastResult()
    return r ? { result: r } : null
  })
  const [activeField, setActiveField] = useState(null)
  const [fields,      setFields]      = useState([])
  const [user,        setUser]        = useState(() => getCurrentUser() || { name: 'Farmer' })

  // Called by AuthPage after successful login/signup
  const handleLogin = useCallback(() => {
    setAuthed(true)
    const u = getCurrentUser()
    if (u) setUser(u)
  }, [])

  // Called by Layout sidebar logout button
  const handleLogout = useCallback(() => {
    storageLogout()
    setAuthed(false)
    setUser({ name: 'Farmer' })
    setActiveScan(null)
    setLastResult(null)
    setFields([])
    setActiveField(null)
  }, [])

  // Load user data when auth state becomes true
  useEffect(() => {
    if (authed) {
      const u = getCurrentUser()
      if (u) setUser(u)
      setActiveScan(null)
      setLastResult(null)
      setFields([])
      setActiveField(null)
      getFields().then(setFields).catch(() => {})
    }
  }, [authed])

  function addField(f)    { setFields(p => [...p, f]) }
  function updateField(f) { setFields(p => p.map(x => x.id === f.id ? f : x)) }
  function removeField(id){ setFields(p => p.filter(x => x.id !== id)) }

  return (
    <LangProvider>
    <ThemeProvider>
      <AppContext.Provider value={{
        lastResult,  setLastResult,
        activeScan,  setActiveScan,
        activeField, setActiveField,
        fields, setFields, addField, updateField, removeField,
        user, setUser,
        authed, handleLogin, handleLogout,
        currentField:    fields.find(f => f.id === activeField) || null,
        setCurrentField: (f) => setActiveField(f?.id || null),
      }}>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            {/* Auth page — redirect to dashboard if already logged in */}
            <Route path="/auth" element={authed ? <Navigate to="/" replace /> : <AuthPage />} />

            {/* Protected routes — redirect to auth if NOT logged in */}
            <Route path="/" element={authed ? <Layout /> : <Navigate to="/auth" replace />}>
              <Route index                 element={<DashboardPage />} />
              <Route path="scan"           element={<ScanPage />} />
              <Route path="analysis/:id"   element={<AnalysisPage />} />
              <Route path="analysis"       element={<AnalysisPage />} />
              <Route path="recommendation" element={<RecommendationPage />} />
              <Route path="history"        element={<HistoryPage />} />
              <Route path="map"            element={<GeoMapPage />} />
              <Route path="chat"           element={<ChatPage />} />
              <Route path="fields"         element={<FieldsPage />} />
              <Route path="schemes"        element={<SchemesPage />} />
              <Route path="calendar"        element={<CropCalendarPage />} />
              <Route path="yield"           element={<YieldEstimatorPage />} />
              <Route path="pest-alerts"     element={<PestAlertsPage />} />
              <Route path="shops"           element={<ShopsPage />} />
            </Route>

            {/* Catch-all: send to auth if not logged in, dashboard if logged in */}
            <Route path="*" element={<Navigate to={authed ? "/" : "/auth"} replace />} />
          </Routes>
        {/* Floating RaithuMitra chatbot — only shown when logged in */}
          {authed && <ChatBot />}
        </BrowserRouter>

        <Toaster position="top-right" toastOptions={{
          style: {
            background:'var(--glass-bg)', color:'var(--on-surface)',
            border:'1px solid var(--border)', borderRadius:'12px',
            fontFamily:'DM Sans, sans-serif', fontSize:'14px',
          },
          success: { iconTheme: { primary:'var(--green)', secondary:'white' } },
        }} />
      </AppContext.Provider>
    </ThemeProvider>
    </LangProvider>
  )
}

