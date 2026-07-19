import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import Logo from '@/components/layout/Logo.jsx'

// ── Typing Animation Hook ────────────────────────────────────────────
function useTypingAnimation(words, speed = 120) {
  const [index, setIndex] = useState(0)
  const [displayed, setDisplayed] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const word = words[index % words.length]
    let timer
    if (!deleting) {
      if (displayed.length < word.length) {
        timer = setTimeout(() => setDisplayed(word.slice(0, displayed.length + 1)), speed)
      } else {
        timer = setTimeout(() => setDeleting(true), 2200)
      }
    } else {
      if (displayed.length > 0) {
        timer = setTimeout(() => setDisplayed(displayed.slice(0, -1)), speed / 2)
      } else {
        setDeleting(false)
        setIndex((i) => i + 1)
      }
    }
    return () => clearTimeout(timer)
  }, [displayed, deleting, index, words, speed])

  return displayed
}

// ── Counter Animation ─────────────────────────────────────────────────
function AnimatedCounter({ target, prefix = '', suffix = '', duration = 2000 }) {
  const [value, setValue] = useState(0)
  const ref = useRef(null)
  const [started, setStarted] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !started) setStarted(true) },
      { threshold: 0.5 }
    )
    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [started])

  useEffect(() => {
    if (!started) return
    const start = Date.now()
    const frame = () => {
      const progress = Math.min((Date.now() - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.floor(eased * target))
      if (progress < 1) requestAnimationFrame(frame)
      else setValue(target)
    }
    requestAnimationFrame(frame)
  }, [started, target, duration])

  return <span ref={ref} className="mono-number">{prefix}{value.toLocaleString()}{suffix}</span>
}

// ── Premium SVG Icons ─────────────────────────────────────────────────
const IconChart = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3v18h18" />
    <path d="m19 9-5 5-4-4-3 3" />
  </svg>
)

const IconTarget = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
)

const IconIntelligence = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
    <path d="M2 12h20" />
  </svg>
)

const IconMessage = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
)

const IconBolt = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
)

const IconShield = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
)

// ── Floating Metric Card ─────────────────────────────────────────────
function FloatingCard({ title, value, change, color, delay, icon }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, duration: 0.7, ease: [0.34, 1.56, 0.64, 1] }}
      whileHover={{ y: -8, scale: 1.03 }}
      style={{
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.8)',
        borderRadius: 20,
        padding: '20px 24px',
        boxShadow: '0 16px 48px rgba(26,86,219,0.10), 0 4px 16px rgba(0,0,0,0.06)',
        minWidth: 160,
        textAlign: 'left',
      }}
    >
      <div style={{ color, marginBottom: 8, display: 'flex', alignItems: 'center' }}>{icon}</div>
      <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
        {title}
      </div>
      <div className="mono-number" style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', marginTop: 4 }}>
        {value}
      </div>
      <div style={{ fontSize: '0.75rem', color: change > 0 ? '#059669' : '#dc2626', fontWeight: 600, marginTop: 4 }}>
        {change > 0 ? '↑' : '↓'} {Math.abs(change)}% vs last month
      </div>
    </motion.div>
  )
}

// ── Feature Card ─────────────────────────────────────────────────────
function FeatureCard({ icon, title, description, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ delay, duration: 0.6 }}
      whileHover={{ y: -6, boxShadow: 'var(--glass-shadow-hover)' }}
      style={{
        background: 'rgba(255,255,255,0.7)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255,255,255,0.6)',
        borderRadius: 24,
        padding: 28,
        boxShadow: '0 8px 32px rgba(26,86,219,0.06)',
        cursor: 'default',
        textAlign: 'left',
      }}
    >
      <div style={{
        width: 48, height: 48,
        borderRadius: 14,
        background: 'linear-gradient(135deg, rgba(26,86,219,0.1), rgba(59,130,246,0.05))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#1a56db', marginBottom: 16,
      }}>
        {icon}
      </div>
      <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 8, fontFamily: 'Space Grotesk', color: '#0f172a' }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.875rem', color: '#64748b', lineHeight: 1.7 }}>
        {description}
      </p>
    </motion.div>
  )
}

// ── Main Landing Page ─────────────────────────────────────────────────
export default function Landing() {
  const navigate = useNavigate()
  const { scrollY } = useScroll()
  const heroY = useTransform(scrollY, [0, 500], [0, -100])
  const typed = useTypingAnimation(['Revenue', 'ROAS', 'Growth', 'Outcomes'], 110)

  const FEATURES = [
    {
      icon: <IconChart />, title: 'Revenue Forecasting',
      description: 'Prophet + LightGBM ensemble with P10/P50/P90 probabilistic intervals for 30, 60, and 90 day horizons.'
    },
    {
      icon: <IconTarget />, title: 'Budget Simulation',
      description: 'Monte Carlo simulation across 2,000 scenarios. Instantly see how budget reallocation affects ROAS.'
    },
    {
      icon: <IconIntelligence />, title: 'Decision Analysis',
      description: 'LLM-powered performance explanations, marketing risk assessments, and executive-ready reports.'
    },
    {
      icon: <IconMessage />, title: 'Marketing Copilot',
      description: 'Conversational assistant explaining channel trends and recommending optimized budget adjustments.'
    },
    {
      icon: <IconBolt />, title: 'Multi-Channel Ingestion',
      description: 'Import Google Ads, Meta Ads, Microsoft Ads, Shopify, and GA4 CSV data with automatic validation.'
    },
    {
      icon: <IconShield />, title: 'Risk Intelligence',
      description: 'Real-time marketing anomaly detection and statistical coverage-guaranteed prediction intervals.'
    },
  ]

  const STATS = [
    { label: 'Forecast Accuracy', value: 87, suffix: '%', prefix: '' },
    { label: 'Monte Carlo Runs', value: 2000, suffix: '', prefix: '' },
    { label: 'Channels Supported', value: 5, suffix: '', prefix: '' },
    { label: 'Day Horizons', value: 90, suffix: '', prefix: 'Up to ' },
  ]

  return (
    <div style={{ background: '#ffffff', minHeight: '100vh', overflow: 'hidden' }}>

      {/* ── NAVBAR ─────────────────────────────────────────────────── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
        background: 'rgba(255,255,255,0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(0,0,0,0.06)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 48px', height: 68,
      }}>
        <Logo.Horizontal />

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span className="badge badge-primary">AIgnition 3.0</span>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate('/dashboard')}
          >
            Open App
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => navigate('/dashboard')}
          >
            Try Demo
          </button>
        </div>
      </nav>

      {/* ── HERO ───────────────────────────────────────────────────── */}
      <section style={{
        minHeight: '100vh',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'radial-gradient(ellipse 120% 80% at 50% -10%, rgba(26,86,219,0.08) 0%, transparent 60%), #ffffff',
        padding: '80px 48px 60px',
        position: 'relative', overflow: 'hidden',
      }}>

        {/* Background floating orbs */}
        <div style={{
          position: 'absolute', top: '15%', right: '8%',
          width: 400, height: 400,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(26,86,219,0.05) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', bottom: '10%', left: '5%',
          width: 300, height: 300,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(5,150,105,0.04) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <motion.div style={{ y: heroY, maxWidth: 1200, width: '100%', textAlign: 'center', position: 'relative' }}>

          {/* Tagline badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            style={{ marginBottom: 32, display: 'flex', justifyContent: 'center' }}
          >
            <div style={{
              display: 'inline-flex', alignItems: 'center',
              padding: '8px 20px', borderRadius: 9999,
              background: 'rgba(26,86,219,0.06)',
              border: '1px solid rgba(26,86,219,0.12)',
              fontSize: '0.82rem', fontWeight: 600, color: '#1a56db',
              letterSpacing: '0.03em',
            }}>
              Marketing Decision Intelligence Platform
            </div>
          </motion.div>

          {/* Main headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            style={{
              fontFamily: 'Space Grotesk',
              fontSize: 'clamp(2.5rem, 6vw, 4.5rem)',
              fontWeight: 800,
              lineHeight: 1.1,
              color: '#0f172a',
              marginBottom: 24,
              letterSpacing: '-0.02em',
            }}
          >
            Predict Your <br />
            Marketing{' '}
            <span style={{
              background: 'linear-gradient(135deg, #1a56db 0%, #3b82f6 50%, #059669 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              display: 'inline-block',
              minWidth: '4ch',
            }}>
              {typed}
              <span style={{
                display: 'inline-block',
                width: 3, height: '0.9em',
                background: '#1a56db',
                marginLeft: 2,
                animation: 'blink 1s ease infinite',
                verticalAlign: 'text-bottom',
              }} />
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            style={{
              fontSize: '1.1rem',
              color: '#64748b',
              maxWidth: 600,
              margin: '0 auto 40px',
              lineHeight: 1.8,
              fontWeight: 400,
            }}
          >
            Integrate channel performance metrics to run multi-scenario forecasting,
            simulate budget adjustments, and access C-suite marketing recommendations.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            style={{ display: 'flex', justifyContent: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 60 }}
          >
            <button
              className="btn btn-primary btn-lg"
              onClick={() => navigate('/dashboard')}
            >
              Launch Dashboard
            </button>
            <button
              className="btn btn-secondary btn-lg"
              onClick={() => navigate('/dashboard')}
            >
              Explore Demo Data
            </button>
          </motion.div>

          {/* Floating Cards */}
          <div style={{
            display: 'flex', gap: 16, justifyContent: 'center',
            flexWrap: 'wrap', marginBottom: 20,
          }}>
            <FloatingCard title="Blended ROAS" value="3.8x" change={12} icon={<IconBolt />} color="#059669" delay={0.4} />
            <FloatingCard title="Revenue Forecast" value="$147K" change={8} icon={<IconChart />} color="#1a56db" delay={0.5} />
            <FloatingCard title="Meta ROAS" value="2.9x" change={-5} icon={<IconTarget />} color="#0ea5e9" delay={0.6} />
            <FloatingCard title="Confidence" value="87%" change={4} icon={<IconShield />} color="#f59e0b" delay={0.7} />
          </div>

        </motion.div>
      </section>

      {/* ── STATS ───────────────────────────────────────────────────── */}
      <section style={{
        padding: '60px 48px',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      }}>
        <div style={{
          maxWidth: 1100, margin: '0 auto',
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 32,
        }}>
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              style={{ textAlign: 'center' }}
            >
              <div style={{
                fontFamily: 'Space Grotesk', fontSize: '2.5rem', fontWeight: 800,
                color: '#ffffff', lineHeight: 1, marginBottom: 8,
              }}>
                <AnimatedCounter target={stat.value} prefix={stat.prefix} suffix={stat.suffix} />
              </div>
              <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.5)', fontWeight: 500 }}>
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── FEATURES ────────────────────────────────────────────────── */}
      <section style={{ padding: '100px 48px', background: '#f8fafc' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            style={{ textAlign: 'center', marginBottom: 64 }}
          >
            <div style={{
              display: 'inline-block', marginBottom: 16,
              padding: '6px 18px', borderRadius: 9999,
              background: 'rgba(26,86,219,0.08)', color: '#1a56db',
              fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.05em',
            }}>
              PLATFORM CAPABILITIES
            </div>
            <h2 style={{
              fontFamily: 'Space Grotesk', fontSize: '2.5rem', fontWeight: 800,
              color: '#0f172a', marginBottom: 16, letterSpacing: '-0.02em',
            }}>
              Marketing Decision Intelligence
            </h2>
            <p style={{ fontSize: '1rem', color: '#64748b', maxWidth: 500, margin: '0 auto', lineHeight: 1.8 }}>
              A unified performance intelligence system built for modern marketing agencies and brands.
            </p>
          </motion.div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: 24,
          }}>
            {FEATURES.map((feature, i) => (
              <FeatureCard key={feature.title} {...feature} delay={i * 0.1} />
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA SECTION ─────────────────────────────────────────────── */}
      <section style={{
        padding: '100px 48px',
        background: 'linear-gradient(135deg, #1a56db 0%, #2563eb 50%, #1d4ed8 100%)',
        textAlign: 'center',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: -100, left: '20%',
          width: 400, height: 400,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.05)',
          pointerEvents: 'none',
        }} />
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          style={{ position: 'relative', maxWidth: 700, margin: '0 auto' }}
        >
          <h2 style={{
            fontFamily: 'Space Grotesk', fontSize: '2.5rem', fontWeight: 800,
            color: 'white', marginBottom: 20, letterSpacing: '-0.02em',
          }}>
            Ready to optimize your marketing performance?
          </h2>
          <p style={{ fontSize: '1.05rem', color: 'rgba(255,255,255,0.75)', marginBottom: 40, lineHeight: 1.8 }}>
            Ingest your multi-channel performance data instantly and simulate budget outcomes with Monte Carlo confidence.
          </p>
          <button
            className="btn btn-lg"
            onClick={() => navigate('/dashboard')}
            style={{
              background: 'white', color: '#1a56db',
              fontWeight: 700, fontSize: '1rem',
              boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
            }}
          >
            Launch Workspaces — Ingest Demo Data
          </button>
        </motion.div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────── */}
      <footer style={{
        padding: '40px 48px',
        background: '#0f172a',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', stroke: 'currentColor',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Logo.Horizontal light={true} />
        </div>
        <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: '0.78rem' }}>
          AIgnition 3.0 Hackathon Submission
        </span>
      </footer>
    </div>
  )
}
