// SatInsight AI — Top Header Bar

import { useStore } from '../../store/dataStore'

interface HeaderProps {
  title: string
  subtitle?: string
}

export default function Header({ title, subtitle }: HeaderProps) {
  const { backendOnline, datasetName, rowCount, isLoading, isAnalyzing } = useStore()

  return (
    <header style={{
      height: 56,
      background: '#0a1628',
      borderBottom: '1px solid #1e3a5f',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      flexShrink: 0,
    }}>
      {/* Left: page title */}
      <div>
        <h1 style={{ color: '#e2e8f0', fontSize: 15, fontWeight: 600, margin: 0 }}>{title}</h1>
        {subtitle && <p style={{ color: '#475569', fontSize: 11, margin: 0 }}>{subtitle}</p>}
      </div>

      {/* Right: status chips */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Spinner */}
        {(isLoading || isAnalyzing) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#3b82f6', fontSize: 12 }}>
            <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⟳</span>
            {isAnalyzing ? 'Analyzing…' : 'Loading…'}
          </div>
        )}

        {/* Dataset chip */}
        {datasetName && (
          <div style={{
            padding: '3px 10px',
            background: '#0d1f3c',
            border: '1px solid #1e3a5f',
            borderRadius: 20,
            fontSize: 11,
            color: '#94a3b8',
          }}>
            {datasetName} · {rowCount.toLocaleString()} rows
          </div>
        )}

        {/* Backend status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 5,
          padding: '3px 10px',
          background: '#0d1f3c',
          border: `1px solid ${backendOnline ? '#166534' : '#7f1d1d'}`,
          borderRadius: 20,
          fontSize: 11,
          color: backendOnline ? '#4ade80' : '#f87171',
        }}>
          <span>{backendOnline ? '●' : '○'}</span>
          {backendOnline ? 'Backend online' : 'Backend offline'}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </header>
  )
}
