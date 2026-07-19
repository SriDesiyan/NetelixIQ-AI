import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useApp } from '@/App.jsx'
import Logo from '@/components/layout/Logo.jsx'

export default function Auth() {
  const navigate = useNavigate()
  const { setSession } = useApp()
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Simulate network latency
    setTimeout(() => {
      setLoading(false)
      if (isLogin) {
        if (email === 'demo@netelix.ai' && password === 'demo123') {
          const randomSession = 'sess_' + Math.random().toString(36).substr(2, 9)
          setSession(randomSession)
          navigate('/dashboard')
        } else if (email && password) {
          const randomSession = 'sess_' + Math.random().toString(36).substr(2, 9)
          setSession(randomSession)
          navigate('/dashboard')
        } else {
          setError('Please fill in all fields.')
        }
      } else {
        if (name && email && password) {
          const randomSession = 'sess_' + Math.random().toString(36).substr(2, 9)
          setSession(randomSession)
          navigate('/dashboard')
        } else {
          setError('Please fill in all fields.')
        }
      }
    }, 1200)
  }

  const handleQuickDemo = () => {
    setLoading(true)
    setTimeout(() => {
      setSession('demo_session_id_12345')
      setLoading(false)
      navigate('/dashboard')
    }, 800)
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(ellipse 120% 80% at 50% -20%, rgba(26,86,219,0.12) 0%, transparent 60%), #f8fafc',
      padding: '24px',
      fontFamily: 'Inter, sans-serif'
    }}>
      <div style={{ position: 'absolute', top: 32, left: 32, cursor: 'pointer' }} onClick={() => navigate('/')}>
        <Logo.Horizontal />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '40px',
          background: 'var(--glass-bg)',
          backdropFilter: 'blur(20px)',
          border: '1px solid var(--color-neutral-200)',
          borderRadius: '24px',
          boxShadow: '0 24px 64px rgba(26, 86, 219, 0.08), 0 8px 24px rgba(0, 0, 0, 0.04)'
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h2 style={{ fontFamily: 'Space Grotesk', fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', marginBottom: '8px' }}>
            {isLogin ? 'Welcome back' : 'Create account'}
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>
            {isLogin ? 'Enter your details to access your platform' : 'Get started with NetElixIQ AI today'}
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {!isLogin && (
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Full Name</label>
              <input
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input"
                required
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Email address</label>
            <input
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
            />
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{ fontSize: '0.8rem', color: 'var(--color-error)', fontWeight: 600 }}
            >
              {error}
            </motion.div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ justifyContent: 'center', width: '100%', padding: '12px', marginTop: '8px' }}
            disabled={loading}
          >
            {loading ? <div className="spinner" style={{ width: 18, height: 18 }} /> : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div style={{ margin: '24px 0', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ flex: 1, height: '1px', background: '#e2e8f0' }} />
          <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Or</span>
          <div style={{ flex: 1, height: '1px', background: '#e2e8f0' }} />
        </div>

        <button
          onClick={handleQuickDemo}
          className="btn btn-secondary"
          style={{ justifyContent: 'center', width: '100%', padding: '12px' }}
          disabled={loading}
        >
          Launch Demo Mode Instantly
        </button>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.85rem', color: '#64748b' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <span
            onClick={() => setIsLogin(!isLogin)}
            style={{ color: '#1a56db', fontWeight: 600, cursor: 'pointer' }}
          >
            {isLogin ? 'Sign up' : 'Sign in'}
          </span>
        </div>

        <div style={{ marginTop: '20px', padding: '10px', background: 'rgba(26,86,219,0.05)', borderRadius: '10px', border: '1px solid rgba(26,86,219,0.1)', fontSize: '0.72rem', color: '#1a56db', textAlign: 'center' }}>
          <strong>Demo Creds:</strong> demo@netelix.ai / demo123
        </div>
      </motion.div>
    </div>
  )
}
