import React from 'react'

export default function Logo() {
  return <Logo.Horizontal />
}

// ── Icon-only Geometric Node Logo ──────────────────────────────────────────
Logo.Icon = function LogoIcon({ size = 32, className }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    >
      {/* Dynamic abstract geometric data flow: three interconnected nodes forming a growth trend */}
      <path
        d="M6 24C6 24 9.5 15.5 13 15.5C16.5 15.5 18 20 21.5 20C25 20 26.5 12 26.5 12"
        stroke="url(#logo-grad-primary)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="6" cy="24" r="3.5" fill="#1a56db" stroke="#ffffff" strokeWidth="1.5" />
      <circle cx="13" cy="15.5" r="3.5" fill="#3b82f6" stroke="#ffffff" strokeWidth="1.5" />
      <circle cx="21.5" cy="20" r="3.5" fill="#0ea5e9" stroke="#ffffff" strokeWidth="1.5" />
      <circle cx="26.5" cy="12" r="3.5" fill="#059669" stroke="#ffffff" strokeWidth="1.5" />
      
      <defs>
        <linearGradient id="logo-grad-primary" x1="6" y1="24" x2="26.5" y2="12" gradientUnits="userSpaceOnUse">
          <stop stopColor="#1a56db" />
          <stop offset="0.5" stopColor="#3b82f6" />
          <stop offset="1" stopColor="#059669" />
        </linearGradient>
      </defs>
    </svg>
  )
}

// ── Horizontal Enterprise Logo ──────────────────────────────────────────────
Logo.Horizontal = function LogoHorizontal({ size = 32, light = false, className }) {
  const textColor = light ? '#ffffff' : 'var(--color-neutral-900)'
  
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        userSelect: 'none',
      }}
    >
      <Logo.Icon size={size} />
      <div>
        <div style={{
          fontSize: '1.05rem',
          fontWeight: 700,
          color: textColor,
          fontFamily: 'Space Grotesk',
          lineHeight: 1.1,
          letterSpacing: '-0.02em',
        }}>
          NetElixIQ<span style={{ color: '#1a56db', fontWeight: 800, marginLeft: 2 }}>AI</span>
        </div>
        <div style={{
          fontSize: '0.62rem',
          fontWeight: 600,
          color: light ? 'rgba(255,255,255,0.45)' : 'var(--color-neutral-400)',
          letterSpacing: '0.09em',
          textTransform: 'uppercase',
          marginTop: 1,
        }}>
          Decision Intelligence
        </div>
      </div>
    </div>
  )
}
