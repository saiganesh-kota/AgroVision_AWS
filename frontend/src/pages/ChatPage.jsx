import React, { useState, useRef, useEffect } from 'react'
import { useApp } from "../App";
import { chat } from '../api/api'
import { Send, Bot, User, Loader, Scan, Leaf, MessageCircle } from 'lucide-react'
import clsx from 'clsx'
import { useNavigate } from 'react-router-dom'

const QUICK_PROMPTS = [
  'How severe is this disease?',
  'What should I spray?',
  'What is the spread risk?',
  'Show me organic options',
  'What does the future trend look like?',
  'How much will treatment cost?',
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={clsx('flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row')}>
      <div className={clsx(
        'w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-1',
        isUser ? 'bg-agro-700/50 border border-agro-600/30' : 'bg-surface-200 border border-surface-border'
      )}>
        {isUser
          ? <User size={13} className="text-agro-300" />
          : <Bot size={13} className="text-agro-400" />
        }
      </div>
      <div className={clsx(
        'max-w-xs lg:max-w-md px-4 py-2.5 text-sm leading-relaxed',
        isUser
          ? 'chat-bubble-user'
          : 'chat-bubble-ai'
      )}>
        {msg.content.split('\n').map((line, i) => (
          line.startsWith('**') && line.endsWith('**')
            ? <div key={i} className="font-semibold text-agro-200 mb-1">{line.replace(/\*\*/g, '')}</div>
            : line.startsWith('•') || line.startsWith('*')
              ? <div key={i} className="flex items-start gap-1.5 mb-0.5"><span className="text-agro-500 mt-0.5">·</span><span>{line.replace(/^[•*]\s*/, '')}</span></div>
              : line ? <div key={i} className="mb-1">{line}</div>
              : <div key={i} className="h-1" />
        ))}
        <div className={clsx('text-[10px] mt-1.5', isUser ? 'text-agro-500 text-right' : 'text-agro-700')}>
          {msg.time}
        </div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { activeScan } = useApp()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: activeScan?.result
        ? `Namaste! 🌿 I'm your AgroVision AI assistant. I can see you have a scan loaded for ${activeScan.result.crop || 'your crop'}. Ask me about disease risk, treatments, spread trends, or best practices.`
        : `Namaste! 🌿 I'm your AgroVision AI assistant. Run a scan first for context-aware answers, or ask me general farming questions.`,
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = {
      role: 'user',
      content: msg,
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const context = activeScan?.result
        ? {
            crop: activeScan.result.crop,
            severity: activeScan.result.severity_level || activeScan.result.severity,
            risk: activeScan.result.risk,
            geo_risk: activeScan.result.geo_risk,
            recommendation: activeScan.result.recommendation,
          }
        : {}

      const history = messages.slice(-6).map(m => ({ role: m.role === 'user' ? 'user' : 'bot', text: m.content || '' }))
      const data = await chat(msg, context, 'en', history)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply || 'Sorry, I could not process that.',
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection error. Please make sure the backend is running on port 5000.',
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const r = activeScan?.result

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex-shrink-0 p-6 pb-4 border-b border-surface-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-agro-900/40 border border-agro-700/30 flex items-center justify-center">
              <Bot size={18} className="text-agro-400" />
            </div>
            <div>
              <div className="text-sm font-semibold text-agro-200">RaithuMitra AI</div>
              <div className="flex items-center gap-1.5 text-xs text-agro-600">
                <div className="w-1.5 h-1.5 rounded-full bg-agro-500" />
                Context-aware farming assistant
              </div>
            </div>
          </div>
          {!r && (
            <button onClick={() => navigate('/scan')} className="btn-ghost text-xs gap-1.5">
              <Scan size={12} /> Run Scan for Context
            </button>
          )}
        </div>

        {/* Scan context pill */}
        {r && (
          <div className="mt-3 p-3 bg-agro-950/30 border border-agro-800/30 rounded-xl">
            <div className="text-xs font-medium text-agro-400 mb-1.5 flex items-center gap-1.5">
              <Leaf size={11} /> Active scan context
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              {[
                { label: 'Crop', value: r.crop },
                { label: 'Severity', value: r.severity_level || r.severity },
                { label: 'Risk', value: r.risk },
                { label: 'Geo Risk', value: r.geo_risk },
              ].filter(i => i.value).map(item => (
                <div key={item.label} className="flex items-center gap-1 text-xs">
                  <span className="text-agro-700">{item.label}:</span>
                  <span className="text-agro-400 font-medium">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-surface-200 border border-surface-border flex items-center justify-center flex-shrink-0 mt-1">
              <Bot size={13} className="text-agro-400" />
            </div>
            <div className="chat-bubble-ai flex items-center gap-2">
              <Loader size={13} className="animate-spin text-agro-500" />
              <span className="text-agro-600 text-xs">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      <div className="flex-shrink-0 px-6 pb-2">
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {QUICK_PROMPTS.map(p => (
            <button
              key={p}
              onClick={() => sendMessage(p)}
              disabled={loading}
              className="flex-shrink-0 px-3 py-1.5 text-xs rounded-full bg-surface-200 border border-surface-border text-agro-500 hover:text-agro-300 hover:border-agro-700/50 transition-colors whitespace-nowrap"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t border-surface-border">
        <div className="flex items-center gap-3 bg-surface-100 border border-surface-border rounded-2xl px-4 py-3 focus-within:border-agro-600/50 transition-colors">
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-sm text-agro-200 placeholder-agro-800 outline-none"
            placeholder="Ask about disease, treatment, spread risk..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            disabled={loading}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className={clsx(
              'w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 transition-all',
              input.trim() && !loading
                ? 'bg-agro-600 hover:bg-agro-500 text-white'
                : 'bg-surface-200 text-agro-700 cursor-not-allowed'
            )}
          >
            {loading ? <Loader size={14} className="animate-spin" /> : <Send size={14} />}
          </button>
        </div>
        <p className="text-[10px] text-agro-800 text-center mt-2">
          Powered by your backend AI · Responses based on scan context
        </p>
      </div>
    </div>
  )
}