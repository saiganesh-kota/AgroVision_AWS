/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Syne"', 'sans-serif'],
        body:    ['"DM Sans"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      // ── CSS-variable based colours ─────────────────────────────────────
      // These work with Tailwind's opacity modifier (bg-agro-900/40 etc.)
      // because we use the `<alpha-value>` placeholder with RGB channels.
      // The actual RGB values are defined in index.css per theme.
      colors: {
        agro: {
          100: 'rgb(var(--agro-100) / <alpha-value>)',
          200: 'rgb(var(--agro-200) / <alpha-value>)',
          300: 'rgb(var(--agro-300) / <alpha-value>)',
          400: 'rgb(var(--agro-400) / <alpha-value>)',
          500: 'rgb(var(--agro-500) / <alpha-value>)',
          600: 'rgb(var(--agro-600) / <alpha-value>)',
          700: 'rgb(var(--agro-700) / <alpha-value>)',
          800: 'rgb(var(--agro-800) / <alpha-value>)',
          900: 'rgb(var(--agro-900) / <alpha-value>)',
          950: 'rgb(var(--agro-950) / <alpha-value>)',
        },
        surface: {
          100:    'rgb(var(--surface-100) / <alpha-value>)',
          200:    'rgb(var(--surface-200) / <alpha-value>)',
          300:    'rgb(var(--surface-300) / <alpha-value>)',
          // border uses CSS var directly (no opacity modifier needed)
          border: 'var(--surface-border)',
        },
      },
      borderColor: {
        'surface-border': 'var(--surface-border)',
      },
      animation: {
        'slide-up':   'slideUp 0.4s ease-out forwards',
        'fade-in':    'fadeIn 0.3s ease-out forwards',
        'float':      'float 3s ease-in-out infinite',
        'pulse-soft': 'pulse 3s ease-in-out infinite',
        'scan-line':  'scanLine 1.5s ease-in-out infinite',
      },
      keyframes: {
        slideUp:  { '0%': { opacity:0, transform:'translateY(20px)' }, '100%': { opacity:1, transform:'translateY(0)' } },
        fadeIn:   { '0%': { opacity:0 }, '100%': { opacity:1 } },
        float:    { '0%,100%': { transform:'translateY(0)' }, '50%': { transform:'translateY(-8px)' } },
        scanLine: { '0%': { top:'0%' }, '100%': { top:'100%' } },
      },
      boxShadow: {
        agro:   '0 0 24px rgba(34,197,94,0.15)',
        'agro-lg': '0 0 48px rgba(34,197,94,0.25)',
      },
    },
  },
  plugins: [],
}
