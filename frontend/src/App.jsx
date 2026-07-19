import React, { createContext, useContext, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/layout/Layout.jsx'
import Landing from '@/pages/Landing.jsx'
import Dashboard from '@/pages/Dashboard.jsx'
import Forecast from '@/pages/Forecast.jsx'
import BudgetSimulator from '@/pages/BudgetSimulator.jsx'
import Copilot from '@/pages/Copilot.jsx'
import Reports from '@/pages/Reports.jsx'
import Settings from '@/pages/Settings.jsx'
import Auth from '@/pages/Auth.jsx'

// ── App State Context ────────────────────────────────────────────────
export const AppContext = createContext(null)

export function useApp() {
  return useContext(AppContext)
}

function AppProvider({ children }) {
  const [sessionId, setSessionId] = useState(
    localStorage.getItem('netelixiq_session') || ''
  )
  const [chatId, setChatId] = useState('')
  const [dataLoaded, setDataLoaded] = useState(false)
  const [theme, setTheme] = useState(
    localStorage.getItem('netelixiq_theme') || 'light'
  )

  const setSession = (id) => {
    setSessionId(id)
    setDataLoaded(!!id)
    if (id) localStorage.setItem('netelixiq_session', id)
    else localStorage.removeItem('netelixiq_session')
  }

  const toggleTheme = () => {
    const nextTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(nextTheme)
    localStorage.setItem('netelixiq_theme', nextTheme)
  }

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <AppContext.Provider value={{
      sessionId,
      setSession,
      chatId,
      setChatId,
      dataLoaded,
      setDataLoaded,
      theme,
      toggleTheme
    }}>
      {children}
    </AppContext.Provider>
  )
}

// ── Protected Route Helper ───────────────────────────────────────────
function ProtectedRoute({ children }) {
  const { sessionId } = useApp()
  if (!sessionId) {
    return <Navigate to="/auth" replace />
  }
  return children
}

// ── App Router ───────────────────────────────────────────────────────
export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          {/* Public landing page */}
          <Route path="/" element={<Landing />} />

          {/* Public Auth page */}
          <Route path="/auth" element={<Auth />} />

          {/* Protected App pages (with sidebar layout) */}
          <Route element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/simulate" element={<BudgetSimulator />} />
            <Route path="/copilot" element={<Copilot />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  )
}
