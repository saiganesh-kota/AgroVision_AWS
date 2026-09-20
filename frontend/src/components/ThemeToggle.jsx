import React from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../utils/ThemeContext'

export default function ThemeToggle({ className = '' }) {
  const { dark, toggle } = useTheme()
  return (
    <button
      onClick={toggle}
      title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      className={`w-9 h-9 rounded-xl glass flex items-center justify-center transition-all duration-200 active:scale-90 ${className}`}
      style={{ borderColor: 'var(--border)' }}
    >
      {dark
        ? <Sun  size={15} style={{ color: 'var(--amber)' }} />
        : <Moon size={15} style={{ color: 'var(--green)' }} />
      }
    </button>
  )
}
