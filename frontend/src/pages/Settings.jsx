import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { useApp } from '@/App.jsx'
import { ingestApi } from '@/services/api.js'
import { useNavigate } from 'react-router-dom'

// ── Custom SVGs ──────────────────────────────────────────────────────────────
const IconUpload = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
)

const IconCheck = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

const IconSpinner = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="spinner">
    <circle cx="12" cy="12" r="10" stroke="var(--color-primary-100)" />
    <path d="M12 2a10 10 0 0 1 10 10" stroke="var(--color-primary-600)" />
  </svg>
)

const IconSettings = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
)

const IconQuickStart = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 2 7 12 12 22 7 12 2" />
    <polyline points="2 17 12 22 22 17" />
    <polyline points="2 12 12 17 22 12" />
  </svg>
)

function UploadZone({ channel, onSuccess }) {
  const [uploading, setUploading] = useState(false)
  const [done, setDone] = useState(false)
  const [rows, setRows] = useState(0)

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
    onDrop: async ([file]) => {
      if (!file) return
      setUploading(true)
      try {
        const result = await ingestApi.upload(file, channel)
        setRows(result.rows_ingested)
        setDone(true)
        onSuccess(result.session_id)
      } catch (e) {
        alert(`Upload failed: ${e.message}`)
      } finally {
        setUploading(false)
      }
    },
  })

  const CHANNEL_INFO = {
    google: { label: 'Google Ads', color: '#1a56db' },
    meta: { label: 'Meta Ads', color: '#0ea5e9' },
    microsoft: { label: 'Microsoft Ads', color: '#8b5cf6' },
    shopify: { label: 'Shopify', color: '#059669' },
    ga4: { label: 'Google Analytics 4', color: '#f59e0b' },
  }

  const info = CHANNEL_INFO[channel] || { label: channel, color: '#64748b' }

  return (
    <motion.div
      whileHover={{ y: -3, boxShadow: 'var(--glass-shadow-hover)' }}
      {...getRootProps()}
      style={{
        border: `2px dashed ${done ? info.color : isDragActive ? info.color : 'var(--color-neutral-200)'}`,
        borderRadius: 16, padding: '24px 20px',
        cursor: 'pointer', textAlign: 'center',
        background: isDragActive ? `${info.color}08` : done ? `${info.color}05` : 'var(--glass-bg)',
        transition: 'all 0.2s',
        backdropFilter: 'blur(8px)',
      }}
    >
      <input {...getInputProps()} />
      <div style={{
        width: 40, height: 40,
        borderRadius: '50%',
        background: `${info.color}12`,
        color: done ? 'var(--color-success)' : info.color,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        margin: '0 auto 12px',
      }}>
        {done ? <IconCheck /> : uploading ? <IconSpinner /> : <IconUpload />}
      </div>
      <div style={{ fontFamily: 'Space Grotesk', fontWeight: 600, color: '#0f172a', fontSize: '0.9rem', marginBottom: 4 }}>
        {info.label}
      </div>
      {done ? (
        <div className="mono-number" style={{ fontSize: '0.72rem', color: info.color, fontWeight: 700 }}>
          {rows} rows ingested
        </div>
      ) : uploading ? (
        <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 500 }}>Uploading...</div>
      ) : (
        <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 500 }}>
          {isDragActive ? 'Drop CSV here' : 'Drop CSV file'}
        </div>
      )}
    </motion.div>
  )
}

export default function Settings() {
  const { sessionId, setSession } = useApp()
  const navigate = useNavigate()
  const [geminiKey, setGeminiKey] = useState('')
  const [demoLoading, setDemoLoading] = useState(false)
  const [keySaved, setKeySaved] = useState(false)

  const handleDemoLoad = async () => {
    setDemoLoading(true)
    try {
      const result = await ingestApi.loadDemo()
      setSession(result.session_id)
      alert(`Demo data loaded successfully: ${result.total_rows} rows across ${result.channels?.join(', ')}`)
    } catch (e) {
      alert('Demo load failed: ' + e.message)
    } finally {
      setDemoLoading(false)
    }
  }

  const handleSessionSuccess = (sid) => {
    setSession(sid)
  }

  const handleSaveKey = () => {
    localStorage.setItem('netelixiq_gemini_key', geminiKey)
    setKeySaved(true)
    setTimeout(() => setKeySaved(false), 2000)
  }

  return (
    <div className="page-container" style={{ paddingTop: 32, maxWidth: 900 }}>

      <h2 className="section-title" style={{ marginBottom: 4 }}>Settings & Workspace</h2>
      <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: 32 }}>
        Upload your performance data or configure your workspace properties
      </p>

      {/* Current Session */}
      {sessionId && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="glass-card"
          style={{ padding: 20, marginBottom: 24, borderLeft: '4px solid var(--color-success)' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="status-dot green" />
              <div>
                <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '0.9rem' }}>Active Session</div>
                <div className="mono-number" style={{ fontSize: '0.75rem', color: '#64748b' }}>{sessionId}</div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-secondary btn-sm" onClick={() => navigate('/dashboard')}>
                View Dashboard
              </button>
              <button
                className="btn btn-sm"
                style={{ background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}
                onClick={() => setSession('')}
              >
                Clear Session
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Quick Demo */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <IconQuickStart />
          <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Demo Data Loader
          </h3>
        </div>
        <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: 16 }}>
          Load 120 days of multi-channel performance data across Google, Meta, Microsoft, Shopify, and GA4 to explore the platform capabilities.
        </p>
        <button
          className="btn btn-primary"
          onClick={handleDemoLoad}
          disabled={demoLoading}
        >
          {demoLoading ? 'Generating demo data...' : 'Load Demo Dataset'}
        </button>
        {demoLoading && (
          <p style={{ marginTop: 12, color: '#64748b', fontSize: '0.78rem' }}>
            Synthesizing 5 CSV campaign files. Please wait...
          </p>
        )}
      </motion.div>

      {/* Upload CSV Files */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.1 } }} className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <IconUpload />
          <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Upload CSV Datasets
          </h3>
        </div>
        <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: 20 }}>
          Ingest raw CSV reports from your advertising channels. Drag and drop or browse to upload.
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
          {['google', 'meta', 'microsoft', 'shopify', 'ga4'].map(ch => (
            <UploadZone key={ch} channel={ch} onSuccess={handleSessionSuccess} />
          ))}
        </div>
        <div style={{ marginTop: 16, padding: '12px 16px', background: 'rgba(26,86,219,0.04)', borderRadius: 12, border: '1px solid rgba(26,86,219,0.08)', fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>
          Tip: Column mappings are dynamically resolved. Supports Google Ads, Meta Ads Manager, Microsoft Ads, Shopify reports, and GA4 datasets.
        </div>
      </motion.div>

      {/* Gemini API Key */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0, transition: { delay: 0.2 } }} className="glass-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <IconSettings />
          <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
            Gemini API Key Configuration
          </h3>
        </div>
        <p style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: 16 }}>
          Set your personal Gemini API key to activate the Marketing Copilot and custom forecast explanations.
        </p>
        <div style={{ display: 'flex', gap: 12 }}>
          <input
            type="password"
            className="input"
            placeholder="AIza..."
            value={geminiKey}
            onChange={e => setGeminiKey(e.target.value)}
          />
          <button
            className="btn btn-primary"
            onClick={handleSaveKey}
            disabled={!geminiKey}
          >
            {keySaved ? 'Saved!' : 'Save Key'}
          </button>
        </div>
        <p style={{ marginTop: 10, fontSize: '0.72rem', color: '#94a3b8', fontWeight: 500 }}>
          Register for a free key at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" style={{ color: '#1a56db', textDecoration: 'underline' }}>aistudio.google.com</a>. 
          If not provided, the workspace uses preset mock recommendations.
        </p>
      </motion.div>
    </div>
  )
}
