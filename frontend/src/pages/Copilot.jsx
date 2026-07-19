import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { useApp } from '@/App.jsx'
import { copilotApi } from '@/services/api.js'
import { useNavigate } from 'react-router-dom'

const SUGGESTED_QUESTIONS = [
  "Why is Meta ROAS decreasing?",
  "Which channel should receive more budget?",
  "How much revenue will I lose if Google budget drops by 20%?",
  "What's the biggest risk in my marketing mix?",
  "Give me an executive summary of performance",
  "What actions should I take this week?",
]

// ── Custom SVGs ──────────────────────────────────────────────────────────────
const IconChatBubble = ({ size = 14, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
)

const IconClear = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
)

const IconLightning = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
)

function MessageBubble({ role, content, timestamp }) {
  const isUser = role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
      }}
    >
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: 10, flexShrink: 0,
          background: 'linear-gradient(135deg, #1a56db, #3b82f6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', marginRight: 10, marginTop: 4,
        }}>
          <IconChatBubble size={14} />
        </div>
      )}
      <div style={{ maxWidth: '78%' }}>
        <div
          className={`message-bubble ${isUser ? 'user' : 'assistant'}`}
          style={{ maxWidth: '100%' }}
        >
          {isUser ? (
            <span>{content}</span>
          ) : (
            <div style={{ fontSize: '0.88rem', lineHeight: 1.75 }}>
              <ReactMarkdown
                components={{
                  strong: ({ children }) => <strong style={{ fontWeight: 700, color: '#0f172a' }}>{children}</strong>,
                  p: ({ children }) => <p style={{ marginBottom: 8 }}>{children}</p>,
                  li: ({ children }) => <li style={{ marginLeft: 16, marginBottom: 4 }}>• {children}</li>,
                  ul: ({ children }) => <ul style={{ padding: 0, margin: '8px 0' }}>{children}</ul>,
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>
        <div style={{
          fontSize: '0.68rem', color: '#94a3b8', marginTop: 4,
          textAlign: isUser ? 'right' : 'left',
          fontFamily: 'JetBrains Mono',
        }}>
          {timestamp ? new Date(timestamp).toLocaleTimeString() : ''}
        </div>
      </div>
    </motion.div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
      <div style={{
        width: 32, height: 32, borderRadius: 10, flexShrink: 0,
        background: 'linear-gradient(135deg, #1a56db, #3b82f6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'white',
      }}>
        <IconChatBubble size={14} />
      </div>
      <div style={{
        background: 'rgba(255,255,255,0.9)', border: '1px solid rgba(255,255,255,0.8)',
        borderRadius: '18px 18px 18px 4px',
        padding: '12px 16px',
        display: 'flex', gap: 4, alignItems: 'center',
      }}>
        {[0, 0.2, 0.4].map((delay, i) => (
          <motion.div
            key={i}
            style={{ width: 7, height: 7, borderRadius: '50%', background: '#94a3b8' }}
            animate={{ y: [0, -6, 0] }}
            transition={{ repeat: Infinity, duration: 0.8, delay, ease: 'easeInOut' }}
          />
        ))}
      </div>
    </div>
  )
}

export default function Copilot() {
  const { sessionId, chatId, setChatId } = useApp()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        role: 'model',
        content: sessionId
          ? "Hi! I'm your **NetElixIQ Marketing Copilot**. I've analyzed your campaign data and I'm ready to help.\n\nAsk me anything about your marketing performance, forecast, or budget optimization. Try one of the suggested questions below, or type your own."
          : "Hi! I'm your **NetElixIQ Marketing Copilot**. Please load your data from the Dashboard first, then I can provide personalized marketing insights.\n\nI can answer questions about ROAS, revenue forecasts, budget allocation, anomalies, and much more.",
        timestamp: new Date().toISOString(),
      }])
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg || sending) return
    setInput('')

    const userMsg = { role: 'user', content: msg, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setSending(true)

    try {
      const response = await copilotApi.chat({
        session_id: sessionId || 'demo',
        chat_id: chatId,
        message: msg,
        horizon: 30,
      })

      if (response.chat_id && !chatId) setChatId(response.chat_id)

      setMessages(prev => [...prev, {
        role: 'model',
        content: response.response,
        timestamp: response.timestamp,
      }])
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'model',
        content: `Sorry, I encountered an error: ${e.message}. Please try again.`,
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = async () => {
    if (chatId) {
      try { await copilotApi.clearHistory(chatId) } catch {}
    }
    setMessages([])
    setChatId('')
    setTimeout(() => {
      setMessages([{
        role: 'model',
        content: "Chat cleared! How can I help you with your marketing data?",
        timestamp: new Date().toISOString(),
      }])
    }, 100)
  }

  return (
    <div className="page-container" style={{ paddingTop: 32 }}>

      <div style={{ display: 'flex', gap: 24, height: 'calc(100vh - 140px)' }}>

        {/* Chat Area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>

          {/* Chat header */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 40, height: 40, borderRadius: 12,
                background: 'linear-gradient(135deg, #1a56db, #3b82f6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'white',
              }}>
                <IconChatBubble size={18} />
              </div>
              <div>
                <div style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'Space Grotesk', color: '#0f172a' }}>
                  Marketing Copilot
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div className="status-dot green" />
                  {sessionId ? 'Data context loaded' : 'No data loaded'}
                </div>
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={clearChat} style={{ gap: 6 }}>
              <IconClear />
              Clear Chat
            </button>
          </motion.div>

          {/* Messages */}
          <div style={{
            flex: 1,
            background: 'var(--glass-bg-strong)',
            border: '1px solid var(--color-neutral-200)',
            borderRadius: 20,
            padding: '20px',
            overflowY: 'auto',
            marginBottom: 12,
          }}>
            {messages.map((msg, i) => (
              <MessageBubble key={i} {...msg} />
            ))}
            {sending && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <div style={{
            display: 'flex', gap: 10,
            background: 'var(--color-neutral-0)',
            border: '1.5px solid var(--color-neutral-200)',
            borderRadius: 16, padding: '10px 14px',
            boxShadow: 'var(--glass-shadow)',
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your marketing data... (Enter to send)"
              rows={1}
              style={{
                flex: 1, border: 'none', outline: 'none', resize: 'none',
                background: 'transparent', fontSize: '0.9rem', color: 'var(--color-neutral-900)',
                fontFamily: 'Inter', lineHeight: 1.6, padding: '4px 0',
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || sending}
              style={{
                width: 36, height: 36,
                background: input.trim() && !sending ? 'linear-gradient(135deg, #1a56db, #3b82f6)' : '#e2e8f0',
                borderRadius: 10, border: 'none', cursor: input.trim() && !sending ? 'pointer' : 'default',
                color: input.trim() && !sending ? 'white' : '#94a3b8',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.2s', flexShrink: 0,
              }}
            >
              {sending ? <div className="spinner" style={{ width: 14, height: 14, borderTopColor: '#1a56db' }} /> : '↑'}
            </button>
          </div>
        </div>

        {/* Sidebar: Suggestions */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          style={{ width: 260, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 16 }}
        >
          <div className="glass-card" style={{ padding: 20 }}>
            <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '0.9rem', fontWeight: 700, marginBottom: 16, color: '#0f172a' }}>
              Suggested Questions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <motion.button
                  key={i}
                  whileHover={{ x: 4 }}
                  onClick={() => sendMessage(q)}
                  disabled={sending}
                  style={{
                    background: 'rgba(26,86,219,0.04)',
                    border: '1px solid rgba(26,86,219,0.1)',
                    borderRadius: 12, padding: '10px 14px',
                    fontSize: '0.78rem', color: '#334155',
                    textAlign: 'left', cursor: 'pointer',
                    transition: 'all 0.2s', lineHeight: 1.5,
                    fontFamily: 'Inter',
                  }}
                >
                  {q}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="glass-card" style={{ padding: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
              <IconLightning />
              <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '0.9rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                Powered by
              </h3>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.8 }}>
              <div>• Google Gemini 2.5 Flash</div>
              <div>• Live forecast context</div>
              <div>• Channel data analysis</div>
              <div>• Multi-turn conversation</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
