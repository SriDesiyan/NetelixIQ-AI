import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '@/App.jsx'

const PAGE_TITLES = {
  '/dashboard': { title: 'Executive Dashboard', subtitle: 'Real-time marketing intelligence' },
  '/forecast': { title: 'Revenue Forecast', subtitle: 'P10/P50/P90 probabilistic predictions' },
  '/simulate': { title: 'Budget Simulator', subtitle: 'Monte Carlo allocation optimization' },
  '/copilot': { title: 'Marketing Copilot', subtitle: 'AI-powered marketing assistant' },
  '/reports': { title: 'Reports & Exports', subtitle: 'Export and share insights' },
  '/settings': { title: 'Settings & Workspace', subtitle: 'Configure your workspace parameters' },
}

// ── Sun and Moon SVGs ────────────────────────────────────────────────────────
const MoonIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
)

const SunIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="5" />
    <line x1="12" y1="1" x2="12" y2="3" />
    <line x1="12" y1="21" x2="12" y2="23" />
    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
    <line x1="1" y1="12" x2="3" y2="12" />
    <line x1="21" y1="12" x2="23" y2="12" />
    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
  </svg>
)

export default function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { sessionId, theme, toggleTheme } = useApp()
  const pageInfo = PAGE_TITLES[location.pathname] || { title: 'NetElixIQ AI', subtitle: '' }

  return (
    <div className="navbar">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        key={location.pathname}
        transition={{ duration: 0.3 }}
        style={{ flex: 1 }}
      >
        <h1 style={{
          fontFamily: 'Space Grotesk',
          fontSize: '1.15rem',
          fontWeight: 700,
          color: 'var(--color-neutral-900)',
          lineHeight: 1.2,
        }}>
          {pageInfo.title}
        </h1>
        <p style={{ fontSize: '0.78rem', color: 'var(--color-neutral-500)', marginTop: 2 }}>
          {pageInfo.subtitle}
        </p>
      </motion.div>

      {/* Theme Toggle & Session Info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={toggleTheme}
          style={{
            background: 'var(--color-primary-50)',
            border: '1px solid var(--color-primary-100)',
            borderRadius: '50%',
            width: 32,
            height: 32,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'var(--color-primary-700)',
            transition: 'all 0.2s',
          }}
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
        >
          {theme === 'light' ? <MoonIcon /> : <SunIcon />}
        </button>

        {sessionId && (
          <div style={{
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--color-primary-50)',
            border: '1px solid var(--color-primary-100)',
            fontSize: '0.78rem',
            color: 'var(--color-primary-700)',
            fontWeight: 500,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <div className="status-dot green" />
            Session: {sessionId.slice(0, 8)}
          </div>
        )}
      </div>

      {/* Get Started Button (If no session info) */}
      {!sessionId && (
        <button
          className="btn btn-primary btn-sm"
          onClick={() => navigate('/auth')}
        >
          Get Started
        </button>
      )}
    </div>
  )
}
