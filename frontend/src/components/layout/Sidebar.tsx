// SatInsight AI — Sidebar Navigation

import { NavLink } from 'react-router-dom'
import { useStore } from '../../store/dataStore'

const NAV_ITEMS = [
  { to: '/',              label: 'Overview',         icon: '◈' },
  { to: '/data',          label: 'Satellite Data',   icon: '⊞' },
  { to: '/analysis',      label: 'Data Analysis',    icon: '∿' },
  { to: '/anomalies',     label: 'Anomaly Detection',icon: '⚠' },
  { to: '/insights',      label: 'AI Insights',      icon: '✦' },
  { to: '/reports',       label: 'Reports',          icon: '⊟' },
]

export default function Sidebar() {
  const { sessionId, analyzed } = useStore()

  return (
    <aside style={{
      width: 220,
      minHeight: '100vh',
      background: '#0a1628',
      borderRight: '1px solid #1e3a5f',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
    }}>
      {/* Branding */}
      <div style={{ padding: '20px 16px 16px', borderBottom: '1px solid #1e3a5f' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Satellite SVG */}
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="10" y="10" width="8" height="8" rx="1" fill="#3b82f6"/>
            <rect x="2" y="12" width="6" height="4" rx="1" fill="#06b6d4"/>
            <rect x="20" y="12" width="6" height="4" rx="1" fill="#06b6d4"/>
            <line x1="14" y1="10" x2="14" y2="5" stroke="#64748b" strokeWidth="1.5"/>
            <circle cx="14" cy="4" r="1.5" fill="#f59e0b"/>
          </svg>
          <div>
            <div style={{ color: '#e2e8f0', fontWeight: 700, fontSize: 14, letterSpacing: '-0.01em' }}>
              SatInsight AI
            </div>
            <div style={{ color: '#475569', fontSize: 10 }}>Space Data Platform</div>
          </div>
        </div>
      </div>

      {/* Session indicator */}
      {sessionId && (
        <div style={{
          margin: '10px 12px 0',
          padding: '6px 10px',
          background: '#0d1f3c',
          borderRadius: 6,
          border: '1px solid #1e3a5f',
          fontSize: 10,
          color: '#64748b',
        }}>
          <span style={{ color: '#22c55e', marginRight: 5 }}>●</span>
          Session active
          {analyzed && <span style={{ color: '#3b82f6', marginLeft: 6 }}>· Analyzed</span>}
        </div>
      )}

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 8px' }}>
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 10px',
              marginBottom: 2,
              borderRadius: 6,
              textDecoration: 'none',
              fontSize: 13,
              fontWeight: isActive ? 600 : 400,
              color: isActive ? '#e2e8f0' : '#64748b',
              background: isActive ? '#122347' : 'transparent',
              borderLeft: isActive ? '2px solid #3b82f6' : '2px solid transparent',
              transition: 'all 0.15s',
            })}
          >
            <span style={{ fontSize: 15, width: 18, textAlign: 'center', flexShrink: 0 }}>{icon}</span>
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid #1e3a5f',
        fontSize: 10,
        color: '#334155',
      }}>
        IBM AI Builders Challenge<br />August 2026
      </div>
    </aside>
  )
}
