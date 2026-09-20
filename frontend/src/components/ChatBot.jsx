import React, { useState, useRef, useEffect, useCallback } from 'react'
import { MessageCircle, X, Send, Leaf, Mic, MicOff, Volume2, VolumeX, Loader, Globe } from 'lucide-react'
import { chat } from '../api/api'
import { getLastResult } from '../utils/storage'
import { useApp } from '../App'
import { useLang } from '../utils/LangContext'

// ── Language config ────────────────────────────────────────────────────────
// Maps app language code → { speechLang: BCP-47 for Web Speech API, label }
const LANG_CONFIG = {
  en: { speechLang: 'en-IN',  label: 'English',   placeholder: 'Ask about disease, treatment, crop care…',    listening: '🎤 Listening in English…',    greeting: 'Namaste! 🌿 I am RaithuMitra. Type or tap 🎤 to speak in English.' },
  te: { speechLang: 'te-IN',  label: 'తెలుగు',    placeholder: 'వ్యాధి, చికిత్స గురించి అడగండి…',             listening: '🎤 తెలుగులో వింటున్నాను…',       greeting: 'నమస్కారం! 🌿 నేను రైతుమిత్ర. తెలుగులో మాట్లాడండి లేదా టైప్ చేయండి.' },
  hi: { speechLang: 'hi-IN',  label: 'हिंदी',     placeholder: 'रोग, उपचार के बारे में पूछें…',               listening: '🎤 हिंदी में सुन रहा हूँ…',       greeting: 'नमस्ते! 🌿 मैं RaithuMitra हूँ। हिंदी में बोलें या टाइप करें।' },
  ta: { speechLang: 'ta-IN',  label: 'தமிழ்',     placeholder: 'நோய், சிகிச்சை பற்றி கேளுங்கள்…',            listening: '🎤 தமிழில் கேட்கிறேன்…',         greeting: 'வணக்கம்! 🌿 நான் RaithuMitra. தமிழில் பேசுங்கள் அல்லது தட்டச்சு செய்யுங்கள்.' },
  kn: { speechLang: 'kn-IN',  label: 'ಕನ್ನಡ',    placeholder: 'ರೋಗ, ಚಿಕಿತ್ಸೆ ಬಗ್ಗೆ ಕೇಳಿ…',                 listening: '🎤 ಕನ್ನಡದಲ್ಲಿ ಕೇಳುತ್ತಿದ್ದೇನೆ…',  greeting: 'ನಮಸ್ಕಾರ! 🌿 ನಾನು RaithuMitra. ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ.' },
  mr: { speechLang: 'mr-IN',  label: 'मराठी',     placeholder: 'रोग, उपचाराबद्दल विचारा…',                    listening: '🎤 मराठीत ऐकतोय…',              greeting: 'नमस्कार! 🌿 मी RaithuMitra आहे. मराठीत बोला किंवा टाइप करा.' },
}

const QUICK_PROMPTS = {
  en: ['Is my crop improving?',   'What should I spray?',             'How to apply treatment?',       'What is spread risk?',        'Nearest fungicide shop?'],
  te: ['పంట మెరుగుపడుతుందా?',    'ఏమి స్ప్రే చేయాలి?',              'చికిత్స ఎలా చేయాలి?',           'వ్యాప్తి ప్రమాదం ఎంత?',      'దగ్గర దుకాణం ఏది?'],
  hi: ['फसल ठीक हो रही है?',      'क्या स्प्रे करें?',                'इलाज कैसे करें?',               'फैलने का खतरा?',              'नजदीकी दुकान कहाँ?'],
  ta: ['பயிர் சரியாகிறதா?',       'என்ன தெளிக்க வேண்டும்?',          'சிகிச்சை எப்படி செய்வது?',     'பரவல் ஆபத்து என்ன?',        'அருகில் கடை எங்கே?'],
  kn: ['ಬೆಳೆ ಸುಧಾರಿಸುತ್ತಿದೆಯಾ?', 'ಏನನ್ನು ಸಿಂಪಡಿಸಬೇಕು?',           'ಚಿಕಿತ್ಸೆ ಹೇಗೆ ನೀಡುವುದು?',     'ಹರಡುವ ಅಪಾಯ ಏನು?',          'ಹತ್ತಿರದ ಅಂಗಡಿ ಎಲ್ಲಿ?'],
  mr: ['पीक सुधारत आहे का?',      'काय फवारावे?',                     'उपचार कसा करावा?',              'पसरण्याचा धोका काय?',        'जवळचे दुकान कुठे?'],
}

// ── Text-to-Speech ─────────────────────────────────────────────────────────
function speak(text, langCode = 'en') {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const cfg   = LANG_CONFIG[langCode] || LANG_CONFIG.en
  const utter = new SpeechSynthesisUtterance(text)
  utter.lang  = cfg.speechLang
  utter.rate  = 0.90
  utter.pitch = 1.05

  // Wait for voices to load (needed on first call)
  const trySpeak = () => {
    const voices   = window.speechSynthesis.getVoices()
    const preferred = voices.find(v => v.lang === cfg.speechLang) ||
                      voices.find(v => v.lang.startsWith(langCode)) ||
                      voices.find(v => v.lang.startsWith('en'))
    if (preferred) utter.voice = preferred
    window.speechSynthesis.speak(utter)
  }

  if (window.speechSynthesis.getVoices().length > 0) {
    trySpeak()
  } else {
    window.speechSynthesis.onvoiceschanged = () => { trySpeak(); window.speechSynthesis.onvoiceschanged = null }
  }
}

export default function ChatBot() {
  const { activeScan }  = useApp()
  const { lang }        = useLang()     // user's selected app language

  const cfg        = LANG_CONFIG[lang] || LANG_CONFIG.en
  const prompts    = QUICK_PROMPTS[lang] || QUICK_PROMPTS.en
  const greeting   = cfg.greeting

  const [open,        setOpen]       = useState(false)
  const [msgs,        setMsgs]       = useState([{ role: 'bot', text: greeting }])
  const [input,       setInput]      = useState('')
  const [loading,     setLoading]    = useState(false)
  const [voiceActive, setVoiceActive]= useState(false)
  const [voiceReply,  setVoiceReply] = useState(true)
  const [speaking,    setSpeaking]   = useState(false)

  const endRef         = useRef(null)
  const recognitionRef = useRef(null)
  const inputRef       = useRef(null)

  // Update greeting when language changes
  useEffect(() => {
    setMsgs([{ role: 'bot', text: (LANG_CONFIG[lang] || LANG_CONFIG.en).greeting }])
  }, [lang])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs])

  useEffect(() => {
    const interval = setInterval(() => {
      setSpeaking(window.speechSynthesis?.speaking || false)
    }, 300)
    return () => clearInterval(interval)
  }, [])

  // ── Send ─────────────────────────────────────────────────────────────────
  const send = useCallback(async (overrideText) => {
    const text = (overrideText || input).trim()
    if (!text || loading) return
    setInput('')
    setMsgs(m => [...m, { role: 'user', text }])
    setLoading(true)
    try {
      const r   = activeScan?.result || getLastResult() || {}
      const ctx = {
        crop: r.crop, disease: r.disease, severity: r.severity,
        risk: r.risk, geo_risk: r.geo_risk, recommendation: r.recommendation,
        future: r.future, spread_trend: r.spread_trend, health_score: r.health_score,
      }
      const { reply } = await chat(text, ctx, lang, msgs.slice(-6))
      setMsgs(m => [...m, { role: 'bot', text: reply }])
      if (voiceReply) speak(reply, lang)
    } catch (e) {
      const serverErr = e?.response?.data?.error || ''
      let errMsg = '⚠️ Could not get a reply.'
      if (serverErr.includes('API_KEY_INVALID') || serverErr.includes('invalid')) {
        errMsg = '⚠️ Gemini API key is invalid. Please check GEMINI_API_KEY in backend/.env and restart the server.'
      } else if (serverErr.includes('quota') || serverErr.includes('RESOURCE_EXHAUSTED')) {
        errMsg = '⚠️ Gemini API quota exceeded. Try again after a minute.'
      } else if (serverErr.includes('not set')) {
        errMsg = '⚠️ GEMINI_API_KEY not set in backend/.env'
      } else if (serverErr) {
        errMsg = `⚠️ ${serverErr}`
      }
      setMsgs(m => [...m, { role: 'bot', text: errMsg }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, activeScan, voiceReply, lang])

  // ── Voice input ───────────────────────────────────────────────────────────
  const startVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      setMsgs(m => [...m, { role: 'bot', text: '⚠️ Voice not supported in this browser. Please use Chrome.' }])
      return
    }
    window.speechSynthesis?.cancel()

    const rec           = new SR()
    rec.lang            = cfg.speechLang   // use user's language for listening too
    rec.interimResults  = false
    rec.maxAlternatives = 3

    rec.onstart  = () => setVoiceActive(true)
    rec.onend    = () => setVoiceActive(false)
    rec.onerror  = () => {
      setVoiceActive(false)
      setMsgs(m => [...m, { role: 'bot', text: '⚠️ Could not hear clearly. Try again.' }])
    }
    rec.onresult = (e) => {
      const heard = e.results[0][0].transcript.trim()
      setInput(heard)
      setTimeout(() => send(heard), 350)
    }

    recognitionRef.current = rec
    rec.start()
  }, [cfg.speechLang, send])

  const stopVoice    = useCallback(() => { recognitionRef.current?.stop(); setVoiceActive(false) }, [])
  const stopSpeaking = () => window.speechSynthesis?.cancel()
  const hasContext   = !!(activeScan?.result || getLastResult())

  return (
    <>
      {/* ── Floating button ──────────────────────────────────────────────── */}
      <button onClick={() => setOpen(o => !o)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 active:scale-95"
        style={{ background: 'var(--green)', boxShadow: '0 4px 24px var(--green-glow)' }}
        title="RaithuMitra AI">
        {open ? <X size={22} className="text-white" /> : <MessageCircle size={22} className="text-white" />}
        {hasContext && !open && (
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white"
            style={{ background: 'var(--amber)' }}>AI</span>
        )}
      </button>

      {/* ── Chat window ──────────────────────────────────────────────────── */}
      {open && (
        <div className="fixed bottom-24 right-6 z-50 w-80 h-[560px] glass rounded-2xl flex flex-col overflow-hidden page-enter"
          style={{ boxShadow: '0 8px 40px var(--shadow), 0 0 0 1px var(--border-hi)' }}>

          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
            <div className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border-hi)' }}>
              <Leaf size={14} style={{ color: 'var(--green)' }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold font-display" style={{ color: 'var(--on-surface)' }}>RaithuMitra</p>
              <p className="text-[10px] flex items-center gap-1" style={{ color: 'var(--green)' }}>
                <Globe size={9} /> {cfg.label} · {hasContext ? 'Scan loaded' : 'AI Farming Assistant'}
              </p>
            </div>

            {/* Voice reply toggle */}
            <button onClick={() => { setVoiceReply(v => !v); stopSpeaking() }}
              title={voiceReply ? 'Voice replies ON' : 'Voice replies OFF'}
              className="w-7 h-7 rounded-lg flex items-center justify-center transition-all"
              style={{
                background: voiceReply ? 'rgba(34,197,94,0.15)' : 'var(--glass-bg2)',
                border: `1px solid ${voiceReply ? 'rgba(34,197,94,0.35)' : 'var(--border)'}`,
                color: voiceReply ? 'var(--green)' : 'var(--muted)',
              }}>
              {speaking ? <Volume2 size={12} className="animate-pulse" /> : voiceReply ? <Volume2 size={12} /> : <VolumeX size={12} />}
            </button>

            <div className="w-2 h-2 rounded-full animate-pulse-soft" style={{ background: 'var(--green)' }} />
          </div>

          {/* Scan context pill */}
          {hasContext && (() => {
            const r = activeScan?.result || getLastResult()
            return r ? (
              <div className="mx-3 mt-2 px-3 py-2 rounded-xl text-[10px]"
                style={{ background: 'var(--glass-bg2)', border: '1px solid var(--border)' }}>
                <span className="text-agro-600">Crop: </span><span className="text-agro-300">{r.crop}</span>
                {r.disease && r.disease !== 'Healthy' && <>
                  <span className="text-agro-800 mx-1">·</span>
                  <span className="text-agro-600">Disease: </span><span className="text-agro-300">{r.disease}</span>
                </>}
                <span className="text-agro-800 mx-1">·</span>
                <span className="text-agro-600">Risk: </span><span className="text-agro-300">{r.risk}</span>
              </div>
            ) : null
          })()}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} gap-2`}>
                {m.role === 'bot' && (
                  <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-1"
                    style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.2)' }}>
                    <Leaf size={10} style={{ color: 'var(--green)' }} />
                  </div>
                )}
                <div className="flex flex-col gap-1 max-w-[82%]">
                  <div style={{
                    background: m.role === 'user' ? 'rgba(34,197,94,0.18)' : 'var(--glass-bg2)',
                    color: 'var(--on-surface)',
                    borderRadius: m.role === 'user' ? '1rem 1rem 0.25rem 1rem' : '1rem 1rem 1rem 0.25rem',
                    border: '1px solid var(--border)',
                  }} className="px-3 py-2 text-sm leading-relaxed">
                    {m.text}
                  </div>
                  {/* Replay button for bot messages */}
                  {m.role === 'bot' && (
                    <button onClick={() => speak(m.text, lang)}
                      className="self-start flex items-center gap-1 text-[10px] text-agro-700 hover:text-agro-400 transition-colors ml-1">
                      <Volume2 size={9} /> {lang === 'en' ? 'Replay' : lang === 'te' ? 'మళ్ళీ వినండి' : lang === 'hi' ? 'फिर सुनें' : lang === 'ta' ? 'மீண்டும் கேளுங்கள்' : 'Replay'}
                    </button>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex justify-start gap-2">
                <div className="w-6 h-6 rounded-full flex items-center justify-center shrink-0"
                  style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.2)' }}>
                  <Leaf size={10} style={{ color: 'var(--green)' }} />
                </div>
                <div className="px-4 py-2.5 rounded-2xl rounded-bl-sm" style={{ background: 'var(--glass-bg2)' }}>
                  <div className="flex gap-1">
                    {[0,1,2].map(i => (
                      <div key={i} className="w-1.5 h-1.5 rounded-full animate-bounce"
                        style={{ background: 'var(--green)', animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Quick prompts */}
          <div className="px-3 py-2 flex gap-1.5 overflow-x-auto border-t scrollbar-none"
            style={{ borderColor: 'var(--border)' }}>
            {prompts.map(q => (
              <button key={q} onClick={() => send(q)}
                className="text-[10px] whitespace-nowrap px-2.5 py-1 rounded-full shrink-0 transition-colors glass-light"
                style={{ color: 'var(--green)' }}>
                {q}
              </button>
            ))}
          </div>

          {/* Input row */}
          <div className="flex items-center gap-2 px-3 pb-3 pt-2">
            {/* Mic */}
            <button
              onClick={voiceActive ? stopVoice : startVoice}
              disabled={loading}
              title={voiceActive ? 'Stop' : `Speak in ${cfg.label}`}
              className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-all border ${
                voiceActive ? 'border-red-500/60 animate-pulse' : 'border-agro-700 hover:border-agro-500'
              }`}
              style={{
                background: voiceActive ? 'rgba(239,68,68,0.15)' : 'var(--glass-bg2)',
                color: voiceActive ? '#f87171' : 'var(--muted)',
              }}>
              {voiceActive ? <MicOff size={14} /> : <Mic size={14} />}
            </button>

            {/* Text input */}
            <input
              ref={inputRef}
              className="input-field text-sm flex-1"
              placeholder={voiceActive ? cfg.listening : cfg.placeholder}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
              disabled={voiceActive}
            />

            {/* Stop / Send */}
            {speaking ? (
              <button onClick={stopSpeaking}
                className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171' }}
                title="Stop speaking">
                <VolumeX size={15} />
              </button>
            ) : (
              <button onClick={() => send()} disabled={!input.trim() || loading}
                className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors disabled:opacity-40"
                style={{ background: 'var(--green)' }}>
                {loading ? <Loader size={14} className="text-white animate-spin" /> : <Send size={15} className="text-white" />}
              </button>
            )}
          </div>

          {/* Voice status bar */}
          {voiceActive && (
            <div className="px-3 pb-3 flex items-center gap-2">
              <div className="flex gap-0.5 items-center">
                {[1,2,3,4,5].map(i => (
                  <div key={i} className="w-1 rounded-full animate-bounce"
                    style={{ height: `${8 + i * 4}px`, background: 'var(--green)', animationDelay: `${i * 0.1}s`, opacity: 0.8 }} />
                ))}
              </div>
              <span className="text-[10px] text-agro-400">
                {cfg.listening} ({cfg.speechLang})
              </span>
            </div>
          )}
        </div>
      )}
    </>
  )
}
