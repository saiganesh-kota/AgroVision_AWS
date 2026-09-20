import React, { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, ScanLine, FlaskConical, BookOpen,
  History, Map, MessageCircle, Layers, LogOut, Menu, X, Leaf,
  BookMarked, CalendarDays, TrendingUp, ShieldAlert, Store
} from 'lucide-react'
import { getCurrentUser } from '../utils/storage'
import { useApp } from '../App'
import ThemeToggle from './ThemeToggle'
import FieldSwitcher from './FieldSwitcher'
import LangSwitcher from './LangSwitcher'
import { useLang } from '../utils/LangContext'
import { t } from '../utils/i18n'

// NAV is now a function so it can use translations
function getNav(lang) {
  return [
    { to: '/',               icon: LayoutDashboard, key: 'dashboard'     },
    { to: '/scan',           icon: ScanLine,        key: 'scan_crop'     },
    { to: '/analysis',       icon: FlaskConical,    key: 'analysis'      },
    { to: '/recommendation', icon: BookOpen,        key: 'advice'        },
    { to: '/history',        icon: History,         key: 'history'       },
    { to: '/map',            icon: Map,             key: 'geo_map'       },
    { to: '/chat',           icon: MessageCircle,   key: 'raithu_mitra'  },
    { to: '/fields',         icon: Layers,          key: 'my_fields'     },
    { to: '/schemes',        icon: BookMarked,      key: 'govt_schemes'  },
    { to: '/calendar',       icon: CalendarDays,    key: 'crop_calendar' },
    { to: '/yield',          icon: TrendingUp,      key: 'yield_estimator'},
    { to: '/pest-alerts',    icon: ShieldAlert,     key: 'pest_alerts'    },
    { to: '/shops',          icon: Store,           key: 'nearby_shops'   },
  ]
}

export default function Layout() {
  const { handleLogout } = useApp()
  const [open, setOpen] = useState(false)
  const { lang } = useLang()

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg)' }}>
      {/* mobile overlay */}
      {open && <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={() => setOpen(false)} />}

      {/* ── Sidebar ── */}
      <aside className={`
        fixed lg:relative z-40 flex flex-col h-full w-64 border-r transition-transform duration-300
        ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `} style={{ borderColor: 'var(--border)', background: 'var(--glass-bg)' }}>

        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border-hi)' }}>
            <Leaf size={18} style={{ color: 'var(--green)' }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-display font-bold text-sm leading-tight" style={{ color: 'var(--on-surface)' }}>AgroVision AI</p>
            <p className="text-[10px] font-mono uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Crop Intelligence</p>
          </div>
          <LangSwitcher compact />
          <ThemeToggle />
          <button className="lg:hidden ml-1" onClick={() => setOpen(false)} style={{ color: 'var(--muted)' }}>
            <X size={16} />
          </button>
        </div>

        {/* User info */}
        {(() => { const u = getCurrentUser(); return u ? (
          <div className="px-5 py-2.5 border-b flex items-center gap-2" style={{ borderColor: 'var(--border)' }}>
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
              style={{ background:'var(--glass-bg2)', color:'var(--green)', border:'1px solid var(--border-hi)' }}>
              {u.name?.charAt(0)?.toUpperCase() || 'F'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold truncate" style={{ color:'var(--on-surface)' }}>{u.name}</p>
              {u.state && <p className="text-[10px] truncate" style={{ color:'var(--muted)' }}>📍 {u.state}</p>}
            </div>
          </div>
        ) : null })()}

        {/* Field switcher */}
        <div className="px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
          <FieldSwitcher />
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 flex flex-col gap-1 overflow-y-auto">
          {getNav(lang).map(({ to, icon: Icon, key }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
              onClick={() => setOpen(false)}>
              <Icon size={16} />{t(lang, key)}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 pb-6">
          <button onClick={() => { handleLogout() }}
            className="nav-link w-full" style={{ color: 'var(--danger)' }}>
            <LogOut size={16} /> {t(lang, 'sign_out')}
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile topbar */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-4 border-b glass"
          style={{ borderColor: 'var(--border)' }}>
          <button onClick={() => setOpen(true)} style={{ color: 'var(--muted)' }}><Menu size={22} /></button>
          <span className="font-display font-bold" style={{ color: 'var(--on-surface)' }}>AgroVision AI</span>
          <div className="ml-auto"><ThemeToggle /></div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
