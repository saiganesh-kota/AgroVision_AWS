import React, { createContext, useContext, useState, useEffect } from 'react'

const LangContext = createContext(null)

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('agrovision_lang') || 'en')

  useEffect(() => {
    localStorage.setItem('agrovision_lang', lang)
    // Set html lang attribute for accessibility
    document.documentElement.lang = lang

    // Manage Google Translate cookie for full page translation
    if (lang === 'en') {
      // Clear the cookie to revert to original
      document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`
      document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`
      
      // Force reload to completely clear Google Translate's DOM mutations
      if (document.documentElement.classList.contains('translated-ltr') || document.documentElement.classList.contains('translated-rtl')) {
        window.location.reload()
      }
    } else {
      const googTransCookie = `/en/${lang}`
      document.cookie = `googtrans=${googTransCookie}; path=/`
      document.cookie = `googtrans=${googTransCookie}; path=/; domain=${window.location.hostname}`

      // Try to trigger the Google Translate dropdown if it exists
      const select = document.querySelector('.goog-te-combo')
      if (select) {
        select.value = lang
        select.dispatchEvent(new Event('change'))
      } else {
        // If the script hasn't loaded yet, it will read the cookie when it does
        setTimeout(() => {
          const delayedSelect = document.querySelector('.goog-te-combo')
          if (delayedSelect) {
            delayedSelect.value = lang
            delayedSelect.dispatchEvent(new Event('change'))
          }
        }, 500)
      }
    }
  }, [lang])

  return (
    <LangContext.Provider value={{ lang, setLang }}>
      {children}
    </LangContext.Provider>
  )
}

export function useLang() {
  return useContext(LangContext)
}
