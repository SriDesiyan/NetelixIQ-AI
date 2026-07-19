import React, { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import {
  AreaChart, Area, ResponsiveContainer, PieChart, Pie, Cell, Tooltip,
  CartesianGrid, XAxis, YAxis
} from 'recharts'
import { useApp } from '@/App.jsx'
import { ingestApi, forecastApi, analystApi } from '@/services/api.js'

// ── Helpers ────────────────────────────────────────────────────────
function fmtCurrency(n) {
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}K`
  return `$${n?.toFixed(0) || 0}`
}

function fmtNum(n, decimals = 2) {
  return (n || 0).toFixed(decimals)
}

// ── Premium SVG Icons ──────────────────────────────────────────────
const IconDollar = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
)

const IconROAS = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
    <polyline points="17 6 23 6 23 12" />
  </svg>
)

const IconForecast = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
  </svg>
)

const IconConfidence = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
)

const IconTable = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3h18v18H3z" />
    <path d="M21 9H3" />
    <path d="M21 15H3" />
    <path d="M12 3v18" />
  </svg>
)

const IconRisk = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

// ── Metric Card Component with Sparkline & Hover Animation ────────
function MetricCard({ label, value, sub, icon, color = '#1a56db', change, sparkPoints, loading }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, boxShadow: 'var(--glass-shadow-hover)' }}
      className="glass-card metric-card"
      style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div className="metric-label" style={{ fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</div>
          <div style={{
            width: 32, height: 32,
            borderRadius: 8,
            background: `${color}12`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: color,
          }}>{icon}</div>
        </div>
        {loading ? (
          <div className="skeleton" style={{ height: 36, width: '140px', borderRadius: 6 }} />
        ) : (
          <div className="metric-value mono-number" style={{ fontSize: '2rem', fontWeight: 700, margin: 0, letterSpacing: '-0.03em' }}>{value}</div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginTop: 16 }}>
        <div>
          {change !== undefined && (
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              fontSize: '0.78rem',
              fontWeight: 700,
              color: change >= 0 ? 'var(--color-success)' : 'var(--color-error)',
              background: change >= 0 ? 'rgba(5,150,105,0.08)' : 'rgba(220,38,38,0.08)',
              padding: '3px 8px',
              borderRadius: 6,
            }}>
              {change >= 0 ? '+' : ''}{change.toFixed(1)}%
            </div>
          )}
          {sub && <div style={{ fontSize: '0.72rem', color: 'var(--color-neutral-400)', marginTop: 6, fontWeight: 500 }}>{sub}</div>}
        </div>

        {/* Premium Mini SVG Sparkline */}
        {sparkPoints && !loading && (
          <svg width="68" height="28" viewBox="0 0 50 20" style={{ overflow: 'visible' }}>
            <defs>
              <linearGradient id={`spark-grad-${label.replace(/\s+/g, '')}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <path
              d={`M ${sparkPoints.map((p, i) => `${(i / (sparkPoints.length - 1)) * 50} ${20 - p * 18}`).join(' L ')}`}
              fill="none"
              stroke={color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d={`M 0 20 L ${sparkPoints.map((p, i) => `${(i / (sparkPoints.length - 1)) * 50} ${20 - p * 18}`).join(' L ')} L 50 20 Z`}
              fill={`url(#spark-grad-${label.replace(/\s+/g, '')})`}
            />
          </svg>
        )}
      </div>
    </motion.div>
  )
}

// ── Handcrafted Marketing Dashboard SVG Illustration ────────────────
function HandcraftedIllustration() {
  return (
    <svg width="220" height="150" viewBox="0 0 220 150" fill="none" style={{ margin: '0 auto 24px', display: 'block' }}>
      {/* Background Panel mockup */}
      <rect x="10" y="10" width="200" height="130" rx="16" fill="var(--color-neutral-50)" stroke="var(--color-neutral-200)" strokeWidth="1.5" />
      
      {/* Mini metric cards mockups */}
      <rect x="24" y="24" width="50" height="26" rx="6" fill="#ffffff" stroke="var(--color-neutral-200)" strokeWidth="1" />
      <line x1="30" y1="32" x2="54" y2="32" stroke="var(--color-neutral-300)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="30" y1="40" x2="64" y2="40" stroke="#1a56db" strokeWidth="2.5" strokeLinecap="round" />

      <rect x="82" y="24" width="50" height="26" rx="6" fill="#ffffff" stroke="var(--color-neutral-200)" strokeWidth="1" />
      <line x1="88" y1="32" x2="112" y2="32" stroke="var(--color-neutral-300)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="88" y1="40" x2="118" y2="40" stroke="#059669" strokeWidth="2.5" strokeLinecap="round" />

      <rect x="140" y="24" width="56" height="26" rx="6" fill="#ffffff" stroke="var(--color-neutral-200)" strokeWidth="1" />
      <line x1="146" y1="32" x2="176" y2="32" stroke="var(--color-neutral-300)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="146" y1="40" x2="182" y2="40" stroke="#8b5cf6" strokeWidth="2.5" strokeLinecap="round" />

      {/* Main Chart mockup */}
      <rect x="24" y="62" width="172" height="64" rx="8" fill="#ffffff" stroke="var(--color-neutral-200)" strokeWidth="1" />
      <path
        d="M 32 110 Q 52 82 72 96 T 112 76 T 152 88 T 188 70"
        fill="none"
        stroke="#1a56db"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <circle cx="112" cy="76" r="3" fill="#1a56db" />
      <line x1="112" y1="76" x2="112" y2="116" stroke="var(--color-neutral-200)" strokeWidth="1" strokeDasharray="3 3" />
    </svg>
  )
}

// ── Risk Score Gauge ───────────────────────────────────────────────
function RiskGauge({ score = 5 }) {
  const color = score >= 7 ? '#dc2626' : score >= 4.5 ? '#d97706' : '#059669'
  const label = score >= 7 ? 'HIGH' : score >= 4.5 ? 'MEDIUM' : 'LOW'
  const angle = (score / 10) * 180 - 90

  return (
    <div style={{ textAlign: 'center', padding: '16px 0' }}>
      <svg width="160" height="90" viewBox="0 0 160 90">
        {/* Background arc */}
        <path d="M 15 80 A 65 65 0 0 1 145 80" fill="none" stroke="#e2e8f0" strokeWidth="10" strokeLinecap="round" />
        {/* Colored arc */}
        <path
          d="M 15 80 A 65 65 0 0 1 145 80"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${(score / 10) * 204} 204`}
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
        {/* Needle */}
        <line
          x1="80" y1="80"
          x2={80 + 50 * Math.cos((angle * Math.PI) / 180)}
          y2={80 - 50 * Math.sin((Math.PI - (angle * Math.PI) / 180))}
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ transition: 'all 1s ease' }}
        />
        <circle cx="80" cy="80" r="4" fill={color} />
      </svg>
      <div className="mono-number" style={{ fontSize: '1.75rem', fontWeight: 800, color, lineHeight: 1 }}>
        {score}/10
      </div>
      <div style={{
        display: 'inline-block', marginTop: 8,
        padding: '3px 12px', borderRadius: 9999,
        background: `${color}12`,
        color, fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em',
      }}>
        {label} RISK
      </div>
    </div>
  )
}

// ── Channel Colors & Labels ─────────────────────────────────────────
const CHANNEL_COLORS = {
  google: '#1a56db',
  meta: '#0ea5e9',
  microsoft: '#8b5cf6',
  shopify: '#059669',
  ga4: '#f59e0b',
}

const CHANNEL_LABELS = { google: 'Google', meta: 'Meta', microsoft: 'Microsoft', shopify: 'Shopify', ga4: 'GA4' }

// ── Main Dashboard Component ───────────────────────────────────────
export default function Dashboard() {
  const { sessionId, setSession } = useApp()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [demoLoading, setDemoLoading] = useState(false)
  const [summary, setSummary] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [risk, setRisk] = useState(null)
  const [horizon, setHorizon] = useState(30)

  const loadData = useCallback(async (sid) => {
    if (!sid) return
    setLoading(true)
    try {
      const [summaryData, forecastData] = await Promise.all([
        ingestApi.getSessionSummary(sid),
        forecastApi.generate(sid, horizon),
      ])
      setSummary(summaryData)
      setForecast(forecastData)

      // Load risk in background
      analystApi.getRisk(sid, horizon)
        .then(setRisk)
        .catch(() => {})
    } catch (e) {
      console.error('Load error:', e)
    } finally {
      setLoading(false)
    }
  }, [horizon])

  useEffect(() => {
    if (sessionId) loadData(sessionId)
  }, [sessionId, loadData])

  const handleLoadDemo = useCallback(async () => {
    setDemoLoading(true)
    try {
      const result = await ingestApi.loadDemo()
      setSession(result.session_id)
    } catch (e) {
      alert('Demo load failed: ' + e.message)
    } finally {
      setDemoLoading(false)
    }
  }, [setSession])

  // Build forecast chart data
  const forecastChartData = forecast?.forecast?.slice(0, horizon).map(d => ({
    date: d.date?.slice(5),
    p10: d.p10, p50: d.p50, p90: d.p90,
  })) || []

  // Build channel pie data
  const channelPieData = summary ? Object.entries(summary.channel_breakdown || {}).map(([ch, v]) => ({
    name: CHANNEL_LABELS[ch] || ch,
    value: v.revenue,
    color: CHANNEL_COLORS[ch] || '#64748b',
  })) : []

  const totalRevenue = summary?.total_revenue || 0
  const totalSpend = summary?.total_spend || 0
  const blendedROAS = summary?.blended_roas || 0
  const forecastP50 = forecast?.summary?.total_p50 || 0
  const confidence = forecast?.confidence || 0

  return (
    <div className="page-container" style={{ paddingTop: 32 }}>

      {/* ── No Data State ────────────────────────────────────── */}
      {!sessionId && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            textAlign: 'center', padding: '60px 40px',
          }}
        >
          <HandcraftedIllustration />
          <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '2rem', marginBottom: 12, color: 'var(--color-neutral-900)' }}>
            NetElixIQ AI Workspace
          </h2>
          <p style={{ color: 'var(--color-neutral-500)', fontSize: '0.92rem', marginBottom: 36, maxWidth: 480, margin: '0 auto 36px', lineHeight: 1.6 }}>
            Load the demo dataset to analyze multi-channel metrics, run Monte Carlo simulations, and forecast revenue.
          </p>
          <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              className="btn btn-primary btn-lg"
              onClick={handleLoadDemo}
              disabled={demoLoading}
            >
              {demoLoading ? 'Loading Demo Data...' : 'Load Demo Data'}
            </button>
            <button
              className="btn btn-secondary btn-lg"
              onClick={() => navigate('/settings')}
            >
              Upload CSV Data
            </button>
          </div>
          {demoLoading && (
            <p style={{ marginTop: 20, color: 'var(--color-neutral-400)', fontSize: '0.82rem' }}>
              Synthesizing 120 days of multi-channel data. Please wait...
            </p>
          )}
        </motion.div>
      )}

      {/* ── Dashboard Content ────────────────────────────────── */}
      {sessionId && (
        <>
          {/* Horizon selector */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
            <div>
              <h2 className="section-title" style={{ marginBottom: 4 }}>Executive Overview</h2>
              <p style={{ color: 'var(--color-neutral-500)', fontSize: '0.85rem' }}>
                {summary?.date_from} — {summary?.date_to} · {summary?.total_rows || 0} performance records
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
                    transition: 'all 0.2s',
                  }}
                >
                  {h}d
                </button>
              ))}
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid-4" style={{ marginBottom: 32 }}>
            <MetricCard
              label="Total Revenue"
              value={fmtCurrency(totalRevenue)}
              icon={<IconDollar />}
              color="#1a56db"
              change={8.4}
              sparkPoints={[0.2, 0.35, 0.3, 0.5, 0.45, 0.65, 0.8, 0.75, 0.9]}
              loading={loading}
            />
            <MetricCard
              label="Blended ROAS"
              value={`${fmtNum(blendedROAS, 2)}x`}
              icon={<IconROAS />}
              color="#059669"
              change={4.2}
              sparkPoints={[0.4, 0.5, 0.45, 0.6, 0.55, 0.7, 0.65, 0.8, 0.85]}
              loading={loading}
            />
            <MetricCard
              label={`${horizon}d Forecast`}
              value={fmtCurrency(forecastP50)}
              icon={<IconForecast />}
              color="#8b5cf6"
              change={12.1}
              sparkPoints={[0.3, 0.4, 0.5, 0.45, 0.6, 0.7, 0.8, 0.75, 0.92]}
              loading={loading}
            />
            <MetricCard
              label="Confidence"
              value={`${Math.round(confidence * 100)}%`}
              icon={<IconConfidence />}
              color="#f59e0b"
              change={0.5}
              sparkPoints={[0.8, 0.82, 0.79, 0.83, 0.81, 0.85, 0.84, 0.86, 0.88]}
              loading={loading}
            />
          </div>

          {/* Charts row */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, marginBottom: 24 }}>

            {/* Revenue Forecast Chart */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                <IconForecast />
                <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                  {horizon}-Day Revenue Forecast — P10 / P50 / P90
                </h3>
              </div>
              {loading ? (
                <div className="skeleton" style={{ height: 260 }} />
              ) : (
                <ResponsiveContainer width="100%" height={230}>
                  <AreaChart data={forecastChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="p50grad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#1a56db" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#1a56db" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-neutral-100)" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8', fontFamily: 'JetBrains Mono' }} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                    <Tooltip
                      contentStyle={{
                        background: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(12px)',
                        border: '1px solid var(--color-neutral-200)',
                        borderRadius: 12,
                        boxShadow: 'var(--glass-shadow)',
                        fontFamily: 'JetBrains Mono',
                        fontSize: '0.78rem',
                      }}
                      formatter={(v, n) => [`$${v?.toLocaleString('en', { maximumFractionDigits: 0 })}`, n.toUpperCase()]}
                    />
                    <Area type="monotone" dataKey="p90" stroke="#bfdbfe" fill="none" strokeDasharray="4 2" strokeWidth={1.5} name="P90" />
                    <Area type="monotone" dataKey="p50" stroke="#1a56db" fill="url(#p50grad)" strokeWidth={2.5} name="P50" />
                    <Area type="monotone" dataKey="p10" stroke="#93c5fd" fill="none" strokeDasharray="4 2" strokeWidth={1.5} name="P10" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </motion.div>

            {/* Channel Mix Pie */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="glass-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                  <IconROAS />
                  <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                    Revenue by Channel
                  </h3>
                </div>
                {loading ? (
                  <div className="skeleton" style={{ height: 160 }} />
                ) : (
                  <ResponsiveContainer width="100%" height={150}>
                    <PieChart>
                      <Pie data={channelPieData} cx="50%" cy="50%" outerRadius={70} innerRadius={42} dataKey="value" paddingAngle={4}>
                        {channelPieData.map((entry, i) => (
                          <Cell key={i} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: 'rgba(255, 255, 255, 0.95)',
                          backdropFilter: 'blur(12px)',
                          border: '1px solid var(--color-neutral-200)',
                          borderRadius: 12,
                          fontFamily: 'JetBrains Mono',
                          fontSize: '0.78rem',
                        }}
                        formatter={v => `$${v?.toLocaleString('en', { maximumFractionDigits: 0 })}`}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
              {/* Legend */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 12px', marginTop: 12 }}>
                {channelPieData.map(d => (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', fontWeight: 500 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: d.color }} />
                    <span style={{ color: 'var(--color-neutral-500)' }}>{d.name}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Bottom row: Channel table + Risk */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, marginBottom: 32 }}>

            {/* Channel Performance Table */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.2 } }} className="glass-card" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                <IconTable />
                <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                  Channel Performance
                </h3>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Channel</th>
                    <th>Spend</th>
                    <th>Revenue</th>
                    <th>ROAS</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody className="mono-number" style={{ fontSize: '0.85rem' }}>
                  {Object.entries(summary?.channel_breakdown || {}).map(([ch, v]) => (
                    <tr key={ch}>
                      <td style={{ fontFamily: 'var(--font-body)', fontWeight: 600 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{ width: 8, height: 8, borderRadius: '50%', background: CHANNEL_COLORS[ch] || '#64748b' }} />
                          {CHANNEL_LABELS[ch] || ch}
                        </div>
                      </td>
                      <td>{fmtCurrency(v.spend)}</td>
                      <td>{fmtCurrency(v.revenue)}</td>
                      <td style={{ fontWeight: 700, color: v.roas >= 3 ? 'var(--color-success)' : v.roas >= 2 ? 'var(--color-warning)' : 'var(--color-error)' }}>
                        {fmtNum(v.roas, 2)}x
                      </td>
                      <td>
                        <span className={`badge ${v.roas >= 3 ? 'badge-success' : v.roas >= 2 ? 'badge-warning' : 'badge-error'}`} style={{ fontFamily: 'var(--font-body)' }}>
                          {v.roas >= 3 ? 'Healthy' : v.roas >= 2 ? 'Watch' : 'Alert'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </motion.div>

            {/* Risk Score */}
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1, transition: { delay: 0.3 } }} className="glass-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
                  <IconRisk />
                  <h3 style={{ fontFamily: 'Space Grotesk', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                    Risk Assessment
                  </h3>
                </div>
                <RiskGauge score={risk?.risk_score || 3.4} />
                {risk?.explanation && (
                  <p style={{ fontSize: '0.78rem', color: 'var(--color-neutral-500)', lineHeight: 1.6, marginTop: 12 }}>
                    {risk.explanation.split('\n')[0]}
                  </p>
                )}
              </div>
              <button
                className="btn btn-secondary btn-sm"
                style={{ width: '100%', marginTop: 20 }}
                onClick={() => navigate('/forecast')}
              >
                View Full Analysis
              </button>
            </motion.div>
          </div>
        </>
      )}
    </div>
  )
}
