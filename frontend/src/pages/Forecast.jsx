import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer
} from 'recharts'
import { useApp } from '@/App.jsx'
import { forecastApi, analystApi } from '@/services/api.js'
import { useNavigate } from 'react-router-dom'

function fmtCurrency(n) {
  if (!n) return '$0'
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

// ── Custom SVGs ──────────────────────────────────────────────────────────────
const IconForecast = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
)

const IconExplanation = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
)

const IconEmpty = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-neutral-300)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(12px)',
      border: '1px solid var(--color-neutral-200)', borderRadius: 12,
      padding: '12px 16px', boxShadow: 'var(--glass-shadow)',
      fontSize: '0.82rem',
    }}>
      <p style={{ fontWeight: 600, color: '#0f172a', marginBottom: 8, fontFamily: 'JetBrains Mono' }}>{label}</p>
      {payload.map((entry, i) => (
        <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: entry.color }} />
          <span style={{ color: '#64748b' }}>{entry.name}:</span>
          <span className="mono-number" style={{ fontWeight: 600, color: '#0f172a' }}>
            {typeof entry.value === 'number' ? fmtCurrency(entry.value) : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function Forecast() {
  const { sessionId } = useApp()
  const navigate = useNavigate()
  const [horizon, setHorizon] = useState(30)
  const [metric, setMetric] = useState('revenue')
  const [forecast, setForecast] = useState(null)
  const [contribution, setContribution] = useState(null)
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [explLoading, setExplLoading] = useState(false)

  const loadForecast = async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const [forecastData, contribData] = await Promise.all([
        forecastApi.generate(sessionId, horizon, metric),
        forecastApi.getChannelContribution(sessionId, horizon),
      ])
      setForecast(forecastData)
      setContribution(contribData)
    } catch (e) {
      console.error('Forecast error:', e)
    } finally {
      setLoading(false)
    }
  }

  const loadExplanation = async () => {
    if (!sessionId) return
    setExplLoading(true)
    try {
      const data = await analystApi.getForecastExplanation(sessionId, horizon)
      setExplanation(data)
    } catch (e) {
      console.error('Explanation error:', e)
    } finally {
      setExplLoading(false)
    }
  }

  useEffect(() => { loadForecast() }, [sessionId, horizon, metric])

  const forecastData = forecast?.forecast?.map(d => ({
    date: d.date?.slice(5),
    p10: d.p10, p50: d.p50, p90: d.p90,
  })) || []

  const summary = forecast?.summary || {}
  const confidence = forecast?.confidence || 0

  if (!sessionId) {
    return (
      <div className="page-container" style={{ textAlign: 'center', paddingTop: 80 }}>
        <div style={{ marginBottom: 16 }}><IconEmpty /></div>
        <h2 style={{ fontFamily: 'Space Grotesk', marginBottom: 12 }}>No Data Loaded</h2>
        <p style={{ color: '#64748b', marginBottom: 32, fontSize: '0.9rem' }}>Load your dataset on the Dashboard to access forecasts.</p>
        <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
          Go to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="page-container" style={{ paddingTop: 32 }}>

      {/* Header controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {['revenue', 'spend', 'roas'].map(m => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              style={{
                padding: '6px 16px', borderRadius: 9999,
                background: metric === m ? 'var(--color-primary-600)' : 'var(--color-neutral-0)',
                color: metric === m ? '#ffffff' : 'var(--color-neutral-500)',
                border: `1.5px solid ${metric === m ? 'var(--color-primary-600)' : 'var(--color-neutral-200)'}`,
                fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer',
                textTransform: 'uppercase', letterSpacing: '0.04em',
              }}
            >
              {m}
            </button>
          ))}
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
            >
              {h}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid-4" style={{ marginBottom: 32 }}>
        {[
          { label: `${horizon}d P10 (Risk)`, value: fmtCurrency(summary.total_p10), color: '#94a3b8' },
          { label: `${horizon}d P50 (Expected)`, value: fmtCurrency(summary.total_p50), color: 'var(--color-primary-600)' },
          { label: `${horizon}d P90 (Optimistic)`, value: fmtCurrency(summary.total_p90), color: '#059669' },
          { label: 'Model Confidence', value: `${Math.round(confidence * 100)}%`, color: '#f59e0b' },
        ].map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card"
            style={{ padding: 20 }}
          >
            <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {card.label}
            </div>
            {loading ? (
              <div className="skeleton" style={{ height: 36, marginTop: 8 }} />
            ) : (
              <div className="mono-number" style={{ fontSize: '1.75rem', fontWeight: 800, color: card.color, marginTop: 8 }}>
                {card.value}
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Main forecast chart */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700 }}>
            {horizon}-Day Forecast with Confidence Bands
          </h3>
          <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem', fontWeight: 500 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 24, height: 2, background: '#1a56db' }} />P50 (Median)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{ width: 24, height: 2, background: '#93c5fd', borderTop: '2px dashed' }} />P10-P90
            </div>
          </div>
        </div>

        {loading ? (
          <div className="skeleton" style={{ height: 350 }} />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={forecastData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
              <defs>
                <linearGradient id="p50g" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1a56db" stopOpacity={0.12} />
                  <stop offset="95%" stopColor="#1a56db" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="bandg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#dbeafe" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#dbeafe" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-neutral-100)" vertical={false} />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }} tickFormatter={v => fmtCurrency(v)} tickLine={false} axisLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="p90" stroke="#bfdbfe" fill="url(#bandg)" strokeDasharray="4 3" strokeWidth={1.5} name="P90" />
              <Area type="monotone" dataKey="p50" stroke="#1a56db" fill="url(#p50g)" strokeWidth={2.5} name="P50" />
              <Area type="monotone" dataKey="p10" stroke="#93c5fd" fill="none" strokeDasharray="4 3" strokeWidth={1.5} name="P10" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </motion.div>

      {/* Channel Contribution + AI Explanation */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>

        {/* Channel Contribution */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.2 } }} className="glass-card" style={{ padding: 24 }}>
          <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, marginBottom: 20 }}>
            Channel Revenue Contribution
          </h3>
          {Object.entries(contribution?.channel_contribution || {}).map(([ch, data]) => (
            <div key={ch} style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#0f172a' }}>
                  {ch.charAt(0).toUpperCase() + ch.slice(1)}
                </span>
                <span className="mono-number" style={{ fontSize: '0.82rem', color: '#64748b' }}>
                  {fmtCurrency(data.projected_revenue)} ({data.revenue_share_pct}%)
                </span>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${data.revenue_share_pct}%`,
                    background: `linear-gradient(90deg, ${['#1a56db','#0ea5e9','#8b5cf6','#059669','#f59e0b'][
                      Object.keys(contribution.channel_contribution).indexOf(ch)
                    ] || '#1a56db'}, ${['#3b82f6','#38bdf8','#a78bfa','#34d399','#fbbf24'][
                      Object.keys(contribution.channel_contribution).indexOf(ch)
                    ] || '#3b82f6'})`,
                  }}
                />
              </div>
            </div>
          ))}
        </motion.div>

        {/* AI Explanation */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.3 } }} className="glass-card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <IconExplanation />
              <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                AI Forecast Analysis
              </h3>
            </div>
            <button
              className="btn btn-secondary btn-sm"
              onClick={loadExplanation}
              disabled={explLoading}
            >
              {explLoading ? 'Explaining...' : 'Analyze'}
            </button>
          </div>

          {explLoading && (
            <div>
              <div className="skeleton" style={{ height: 16, marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 16, marginBottom: 8, width: '85%' }} />
              <div className="skeleton" style={{ height: 16, marginBottom: 8, width: '70%' }} />
            </div>
          )}

          {explanation && !explLoading && (
            <div style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.8, maxHeight: 240, overflowY: 'auto' }}>
              {explanation.explanation}
            </div>
          )}

          {!explanation && !explLoading && (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8' }}>
              <div style={{ color: 'var(--color-neutral-300)', marginBottom: 8 }}><IconExplanation /></div>
              <p style={{ fontSize: '0.85rem' }}>Click "Analyze" for AI-powered forecast interpretation</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Model info */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.4 } }}
        style={{ marginTop: 24, padding: '16px 24px', background: 'rgba(26,86,219,0.04)', borderRadius: 16, border: '1px solid rgba(26,86,219,0.1)' }}
      >
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>
          <div><strong>Model:</strong> Prophet + LightGBM Ensemble</div>
          <div><strong>MAPE:</strong> {((forecast?.training_stats?.lgbm_mape || 0) * 100).toFixed(1)}%</div>
          <div><strong>Method:</strong> Conformal Prediction (80% coverage)</div>
          <div><strong>Simulations:</strong> 2,000 Monte Carlo</div>
        </div>
      </motion.div>
    </div>
  )
}
