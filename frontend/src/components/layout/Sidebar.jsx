import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '@/App.jsx'
import Logo from '@/components/layout/Logo.jsx'

// ── Lucide-style SVG Icons ──────────────────────────────────────────────────
const IconDashboard = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="9" />
    <rect x="14" y="3" width="7" height="5" />
    <rect x="14" y="12" width="7" height="9" />
    <rect x="3" y="16" width="7" height="5" />
  </svg>
)

const IconForecast = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
)

const IconBudgetSim = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
)

const IconCopilot = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
)

const IconReports = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
  </svg>
)

const IconSettings = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
)

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: <IconDashboard /> },
  { path: '/forecast', label: 'Forecast', icon: <IconForecast /> },
  { path: '/simulate', label: 'Budget Sim', icon: <IconBudgetSim /> },
  { path: '/copilot', label: 'AI Copilot', icon: <IconCopilot /> },
  { path: '/reports', label: 'Reports', icon: <IconReports /> },
  { path: '/settings', label: 'Settings', icon: <IconSettings /> },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { dataLoaded } = useApp()

  return (
    <div className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          onClick={() => navigate('/')}
          style={{ cursor: 'pointer' }}
        >
          <Logo.Horizontal light={true} />
        </motion.div>
      </div>

      {/* Session indicator */}
      {dataLoaded && (
        <div style={{
          margin: '0 12px 16px',
          padding: '8px 12px',
          background: 'rgba(5,150,105,0.15)',
          borderRadius: 10,
          border: '1px solid rgba(5,150,105,0.25)',
          fontSize: '0.72rem',
          color: '#34d399',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <div className="status-dot green" />
          Data Loaded
        </div>
      )}

      {/* Navigation */}
      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item, i) => {
          const isActive = location.pathname === item.path
          return (
            <motion.div
              key={item.path}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span className="nav-icon" style={{ display: 'flex', alignItems: 'center' }}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {isActive && (
                <div style={{
                  marginLeft: 'auto',
                  width: 4, height: 4,
                  borderRadius: '50%',
                  background: '#60a5fa',
                }} />
              )}
            </motion.div>
          )
        })}
      </nav>

      {/* Bottom */}
      <div style={{ padding: '16px 12px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{
          padding: '12px', borderRadius: 12,
          background: 'rgba(255,255,255,0.04)',
          fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)',
          textAlign: 'center',
          lineHeight: 1.4,
        }}>
          AIgnition 3.0 Hackathon<br />
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.65rem' }}>Predict. Simulate. Optimize.</span>
        </div>
      </div>
    </div>
  )
}
