/**
 * NetElixIQ AI — useCopilot hook
 * Manages Marketing Copilot chat state, message history, and API calls.
 */
import { useState, useCallback, useRef } from 'react'
import { copilotApi } from '@/services/api.js'

const WELCOME_MESSAGE = {
  role: 'model',
  content:
    "👋 Hi! I'm your **NetElixIQ Marketing Copilot**. Ask me anything about your campaign performance, ROAS trends, budget optimization, or forecast interpretation.",
  timestamp: new Date().toISOString(),
}

export function useCopilot(sessionId, horizon = 30) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE])
  const [chatId, setChatId] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const send = useCallback(
    async (text) => {
      const trimmed = text?.trim()
      if (!trimmed || sending) return

      // Optimistically add user message
      const userMsg = { role: 'user', content: trimmed, timestamp: new Date().toISOString() }
      setMessages((prev) => [...prev, userMsg])
      setSending(true)
      setError(null)

      try {
        const response = await copilotApi.chat({
          session_id: sessionId || 'demo',
          chat_id: chatId,
          message: trimmed,
          horizon,
        })

        if (response.chat_id && !chatId) setChatId(response.chat_id)

        setMessages((prev) => [
          ...prev,
          { role: 'model', content: response.response, timestamp: response.timestamp },
        ])
      } catch (err) {
        setError(err.message || 'Message failed')
        setMessages((prev) => [
          ...prev,
          {
            role: 'model',
            content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
            timestamp: new Date().toISOString(),
          },
        ])
      } finally {
        setSending(false)
      }
    },
    [sessionId, chatId, horizon, sending]
  )

  const clear = useCallback(async () => {
    if (chatId) {
      try { await copilotApi.clearHistory(chatId) } catch {}
    }
    setChatId('')
    setMessages([WELCOME_MESSAGE])
  }, [chatId])

  const loadHistory = useCallback(async (id) => {
    if (!id) return
    try {
      const data = await copilotApi.getHistory(id)
      if (data.messages?.length) {
        setMessages(data.messages.map((m) => ({ ...m, timestamp: new Date().toISOString() })))
        setChatId(id)
      }
    } catch {}
  }, [])

  return { messages, chatId, sending, error, send, clear, loadHistory }
}
