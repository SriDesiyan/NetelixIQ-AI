import React, { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useApp } from '@/App.jsx'
import { simulateApi } from '@/services/api.js'
import { useNavigate } from 'react-router-dom'

function fmtCurrency(n) {
  if (!n) return '$0'
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`
  return `$${n.toFixed(0)}`
}

// ── Custom SVGs ──────────────────────────────────────────────────────────────
const IconEmpty = () => (
  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-neutral-300)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
)

const IconDollar = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
)

const IconSliders = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="4" y1="21" x2="4" y2="14" />
    <line x1="4" y1="10" x2="4" y2="3" />
    <line x1="12" y1="21" x2="12" y2="12" />
    <line x1="12" y1="8" x2="12" y2="3" />
    <line x1="20" y1="21" x2="20" y2="16" />
    <line x1="20" y1="12" x2="20" y2="3" />
    <line x1="2" y1="14" x2="6" y2="14" />
    <line x1="10" y1="8" x2="14" y2="8" />
    <line x1="18" y1="16" x2="22" y2="16" />
  </svg>
)

function BudgetSlider({ label, value, min = 0, max = 30000, step = 500, onChange, color }) {
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: color }} />
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#0f172a' }}>{label}</span>
        </div>
        <div className="mono-number" style={{
          background: color + '12', color, fontWeight: 700,
          padding: '4px 14px', borderRadius: 9999, fontSize: '0.9rem',
        }}>
          {fmtCurrency(value)}
        </div>
      </div>

      <div style={{ position: 'relative' }}>
        <input
          type="range"
          className="slider"
          min={min} max={max} step={step}
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{
            '--thumb-color': color,
            background: `linear-gradient(to right, ${color} ${pct}%, var(--color-neutral-200) ${pct}%)`,
          }}
        />
      </div>

      <div className="mono-number" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#94a3b8', marginTop: 4 }}>
        <span>{fmtCurrency(min)}</span>
        <span>{fmtCurrency(max)}</span>
      </div>
    </div>
  )
}

function SimResultCard({ label, p10, p50, p90, unit = '$', color }) {
  return (
    <motion.div
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="glass-card"
      style={{ padding: 20 }}
    >
      <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 12 }}>
        {label}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, textAlign: 'center' }}>
        {[['P10', p10, '#94a3b8'], ['P50', p50, color], ['P90', p90, 'var(--color-success)']].map(([pct, val, c]) => (
          <div key={pct}>
            <div style={{ fontSize: '0.68rem', color: '#94a3b8', marginBottom: 4 }}>{pct}</div>
            <div className="mono-number" style={{ fontSize: '1.15rem', fontWeight: 800, color: c }}>
              {unit === '$' ? '$' : ''}{typeof val === 'number' ? (unit === '$' ? val.toLocaleString('en', { maximumFractionDigits: 0 }) : val.toFixed(2)) : '—'}{unit !== '$' ? unit : ''}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

export default function BudgetSimulator() {
  const { sessionId } = useApp()
  const navigate = useNavigate()
  const [horizon, setHorizon] = useState(30)
  const [google, setGoogle] = useState(15000)
  const [meta, setMeta] = useState(8000)
  const [microsoft, setMicrosoft] = useState(3000)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)

  const totalBudget = google + meta + microsoft

  const runSimulation = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    try {
      const data = await simulateApi.runBudget({
        session_id: sessionId,
        google_budget: google,
        meta_budget: meta,
        microsoft_budget: microsoft,
        horizon_days: horizon,
      })
      setResult(data)
    } catch (e) {
      console.error('Simulation error:', e)
    } finally {
      setLoading(false)
    }
  }, [sessionId, google, meta, microsoft, horizon])

  // Debounced simulation on slider change
  useEffect(() => {
    if (!sessionId) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(runSimulation, 600)
    return () => clearTimeout(debounceRef.current)
  }, [google, meta, microsoft, horizon, sessionId, runSimulation])

  if (!sessionId) {
    return (
      <div className="page-container" style={{ textAlign: 'center', paddingTop: 80 }}>
        <div style={{ marginBottom: 16 }}><IconEmpty /></div>
        <h2 style={{ fontFamily: 'Space Grotesk', marginBottom: 12 }}>No Data Loaded</h2>
        <p style={{ color: '#64748b', marginBottom: 32, fontSize: '0.9rem' }}>Load your dataset on the Dashboard to simulate budget reallocations.</p>
        <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>Go to Dashboard</button>
      </div>
    )
  }

  const channelMix = result?.channel_mix || {}
  const chartData = Object.entries(channelMix).map(([ch, v]) => ({
    name: ch.charAt(0).toUpperCase() + ch.slice(1),
    budget: v.budget,
    revenue: v.expected_revenue,
    roas: v.expected_roas,
  }))

  const COLORS = { Google: '#1a56db', Meta: '#0ea5e9', Microsoft: '#8b5cf6' }

  return (
    <div className="page-container" style={{ paddingTop: 32 }}>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h2 className="section-title" style={{ marginBottom: 4 }}>Monte Carlo Budget Simulator</h2>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
            Adjust budgets dynamically — 2,000 scenarios evaluated instantly to predict channel revenue impact
          </p>
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 24, marginBottom: 32 }}>

        {/* Budget Controls */}
        <div>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="glass-card" style={{ padding: 28, marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24 }}>
              <IconSliders />
              <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                Budget Allocation
              </h3>
            </div>

            <BudgetSlider label="Google Ads" value={google} onChange={setGoogle} color="#1a56db" max={50000} />
            <BudgetSlider label="Meta Ads" value={meta} onChange={setMeta} color="#0ea5e9" max={30000} />
            <BudgetSlider label="Microsoft Ads" value={microsoft} onChange={setMicrosoft} color="#8b5cf6" max={15000} />

            <div style={{
              borderTop: '1px solid var(--color-neutral-100)', paddingTop: 16, marginTop: 8,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#64748b' }}>Total Budget</span>
              <span className="mono-number" style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
                {fmtCurrency(totalBudget)}
              </span>
            </div>
          </motion.div>

          {/* Channel shares */}
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="glass-card" style={{ padding: 20 }}>
            <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '0.9rem', fontWeight: 700, marginBottom: 16 }}>
              Budget Distribution
            </h3>
            {[['Google', google, '#1a56db'], ['Meta', meta, '#0ea5e9'], ['Microsoft', microsoft, '#8b5cf6']].map(([name, budget, color]) => (
              <div key={name} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.8rem' }}>
                  <span style={{ color: '#64748b', fontWeight: 500 }}>{name}</span>
                  <span className="mono-number" style={{ fontWeight: 600, color: '#0f172a' }}>
                    {totalBudget > 0 ? ((budget / totalBudget) * 100).toFixed(0) : 0}%
                  </span>
                </div>
                <div className="progress-bar">
                  <motion.div
                    className="progress-fill"
                    style={{ width: `${totalBudget > 0 ? (budget / totalBudget) * 100 : 0}%`, background: `linear-gradient(90deg, ${color}, ${color}aa)` }}
                    layout
                  />
                </div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Results */}
        <div>

          {/* Revenue & ROAS */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <SimResultCard
              label="Projected Revenue"
              p10={result?.revenue?.p10}
              p50={result?.revenue?.p50}
              p90={result?.revenue?.p90}
              unit="$"
              color="#1a56db"
            />
            <SimResultCard
              label="Blended ROAS"
              p10={result?.roas?.p10}
              p50={result?.roas?.p50}
              p90={result?.roas?.p90}
              unit="x"
              color="#059669"
            />
          </div>

          {/* Confidence */}
          <motion.div className="glass-card" style={{ padding: 20, marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0f172a' }}>Forecast Confidence</span>
              <span className="mono-number" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1a56db' }}>
                {result ? `${Math.round(result.confidence * 100)}%` : '—'}
              </span>
            </div>
            <div className="progress-bar" style={{ height: 8 }}>
              <motion.div
                className="progress-fill"
                style={{ width: result ? `${result.confidence * 100}%` : '0%' }}
                layout
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 12, fontSize: '0.78rem', color: '#64748b', fontWeight: 500 }}>
                <div className="spinner" style={{ width: 12, height: 12 }} />
                Evaluating 2,000 Monte Carlo scenarios...
              </div>
            )}
          </motion.div>

          {/* Channel comparison bar chart */}
          <motion.div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, marginBottom: 20 }}>
              Channel Revenue vs Budget
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} barGap={4} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-neutral-100)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }} tickFormatter={v => fmtCurrency(v)} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid var(--color-neutral-200)',
                    borderRadius: 12,
                    fontFamily: 'JetBrains Mono',
                    fontSize: '0.78rem',
                  }}
                  formatter={(v, n) => [n === 'roas' ? `${v?.toFixed(2)}x` : fmtCurrency(v), n.toUpperCase()]}
                />
                <Bar dataKey="budget" name="Budget" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={`${Object.values(COLORS)[i]}40`} />
                  ))}
                </Bar>
                <Bar dataKey="revenue" name="Revenue" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={Object.values(COLORS)[i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
