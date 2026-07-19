import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '@/App.jsx'
import { reportsApi, analystApi } from '@/services/api.js'
import { useNavigate } from 'react-router-dom'

// ── Custom SVGs ──────────────────────────────────────────────────────────────
const IconEmpty = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-neutral-300)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
  </svg>
)

const IconSparkles = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
)

const IconPdf = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
)

const IconCsv = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3h18v18H3z" />
    <path d="M21 9H3" />
    <path d="M21 15H3" />
    <path d="M12 3v18" />
  </svg>
)

export default function Reports() {
  const { sessionId } = useApp()
  const navigate = useNavigate()
  const [horizon, setHorizon] = useState(30)
  const [loading, setLoading] = useState({})
  const [summary, setSummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const setItemLoading = (key, val) => setLoading(prev => ({ ...prev, [key]: val }))

  const handleDownloadPdf = async () => {
    setItemLoading('pdf', true)
    try {
      await reportsApi.downloadPdf(sessionId, horizon)
    } catch (e) {
      alert('PDF export failed: ' + e.message)
    } finally {
      setItemLoading('pdf', false)
    }
  }

  const handleDownloadCsv = async () => {
    setItemLoading('csv', true)
    try {
      await reportsApi.downloadCsv(sessionId, horizon)
    } catch (e) {
      alert('CSV export failed: ' + e.message)
    } finally {
      setItemLoading('csv', false)
    }
  }

  const handleGenerateSummary = async () => {
    setSummaryLoading(true)
    try {
      const data = await analystApi.getExecutiveSummary(sessionId, horizon)
      setSummary(data)
    } catch (e) {
      alert('Summary generation failed: ' + e.message)
    } finally {
      setSummaryLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div className="page-container" style={{ textAlign: 'center', paddingTop: 80 }}>
        <div style={{ marginBottom: 16 }}><IconEmpty /></div>
        <h2 style={{ fontFamily: 'Space Grotesk', marginBottom: 12 }}>No Data Loaded</h2>
        <p style={{ color: '#64748b', marginBottom: 32, fontSize: '0.9rem' }}>Load your dataset on the Dashboard to generate intelligence reports.</p>
        <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>Go to Dashboard</button>
      </div>
    )
  }

  return (
    <div className="page-container" style={{ paddingTop: 32 }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2 className="section-title" style={{ marginBottom: 4 }}>Reports & Exports</h2>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Generate and download marketing intelligence reports</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {[30, 60, 90].map(h => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              style={{
                padding: '6px 16px', borderRadius: 9999,
                background: horizon === h ? 'var(--color-primary-600)' : 'var(--color-neutral-0)',
                color: horizon === h ? '#ffffff' : 'var(--color-neutral-500)',
                border: `1.5px solid ${horizon === h ? 'var(--color-primary-600)' : 'var(--color-neutral-200)'}`,
                fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer',
              }}
            >{h}d</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24, marginBottom: 32 }}>

        {/* Export Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {[
            {
              key: 'summary', icon: <IconSparkles />, title: 'Executive Summary',
              desc: 'C-suite report with forecast metrics, risk assessments, and strategic budget recommendations.',
              action: handleGenerateSummary, label: 'Generate Summary', color: '#1a56db',
            },
            {
              key: 'pdf', icon: <IconPdf />, title: 'PDF Intelligence Report',
              desc: 'Comprehensive performance report detailing KPIs, forecast bands, and LLM-powered channel insights.',
              action: handleDownloadPdf, label: 'Download PDF', color: '#8b5cf6',
            },
            {
              key: 'csv', icon: <IconCsv />, title: 'Forecast Data CSV',
              desc: 'Raw probabilistic forecast data containing P10, P50, and P90 values grouped by channel and date.',
              action: handleDownloadCsv, label: 'Download CSV', color: '#059669',
            },
          ].map(item => (
            <motion.div
              key={item.key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              whileHover={{ y: -3 }}
              className="glass-card"
              style={{ padding: 24 }}
            >
              <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                  background: `${item.color}12`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: item.color,
                }}>
                  {item.icon}
                </div>
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '0.95rem', fontWeight: 700, marginBottom: 6 }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.6, marginBottom: 16 }}>
                    {item.desc}
                  </p>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={item.action}
                    disabled={loading[item.key] || summaryLoading}
                    style={{ background: `linear-gradient(135deg, ${item.color}, ${item.color}cc)` }}
                  >
                    {(loading[item.key] || (item.key === 'summary' && summaryLoading))
                      ? 'Generating...'
                      : item.label}
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Summary Display */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-card"
          style={{ padding: 28 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <IconSparkles />
              <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                Executive Intelligence Report
              </h3>
            </div>
            {summary && (
              <button
                className="btn btn-secondary btn-sm"
                onClick={handleDownloadPdf}
                disabled={loading.pdf}
                style={{ gap: 6 }}
              >
                <IconPdf />
                Export PDF
              </button>
            )}
          </div>

          {summaryLoading && (
            <div>
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="skeleton" style={{ height: 16, marginBottom: 10, width: `${100 - i * 5}%` }} />
              ))}
              <p style={{ color: '#64748b', fontSize: '0.8rem', marginTop: 16 }}>
                Synthesizing executive summary...
              </p>
            </div>
          )}

          {summary && !summaryLoading && (
            <div style={{
              fontSize: '0.88rem', color: '#334155', lineHeight: 1.9,
              whiteSpace: 'pre-wrap', maxHeight: 440, overflowY: 'auto',
            }}>
              {summary.summary}
            </div>
          )}

          {!summary && !summaryLoading && (
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              height: 300, color: '#94a3b8', textAlign: 'center',
            }}>
              <div style={{ color: 'var(--color-neutral-300)', marginBottom: 16 }}><IconEmpty /></div>
              <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: 8, color: 'var(--color-neutral-800)' }}>
                No report generated yet
              </p>
              <p style={{ fontSize: '0.78rem', maxWidth: 280, lineHeight: 1.7 }}>
                Click "Generate Summary" to create an executive intelligence report for your {horizon}-day horizon.
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
