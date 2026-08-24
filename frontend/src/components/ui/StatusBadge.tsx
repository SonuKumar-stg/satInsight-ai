// SatInsight AI — StatusBadge UI Primitive

import type { RiskLevel, Severity } from '../../types/anomaly'

type BadgeVariant = RiskLevel | Severity | string

const STYLES: Record<string, { bg: string; color: string; border: string }> = {
  Normal:   { bg: 'rgba(34,197,94,0.12)',  color: '#4ade80', border: '#166534' },
  Warning:  { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: '#78350f' },
  Critical: { bg: 'rgba(239,68,68,0.12)',  color: '#f87171', border: '#7f1d1d' },
  info:     { bg: 'rgba(59,130,246,0.12)', color: '#60a5fa', border: '#1e3a5f' },
  warning:  { bg: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: '#78350f' },
  critical: { bg: 'rgba(239,68,68,0.12)',  color: '#f87171', border: '#7f1d1d' },
}

interface StatusBadgeProps {
  value: BadgeVariant
  size?: 'sm' | 'md'
}

export default function StatusBadge({ value, size = 'md' }: StatusBadgeProps) {
  const style = STYLES[value] ?? STYLES.info
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      padding: size === 'sm' ? '1px 7px' : '3px 10px',
      borderRadius: 20,
      background: style.bg,
      border: `1px solid ${style.border}`,
      color: style.color,
      fontSize: size === 'sm' ? 10 : 11,
      fontWeight: 600,
      letterSpacing: '0.02em',
      whiteSpace: 'nowrap',
    }}>
      <span style={{ fontSize: 7 }}>●</span>
      {value.charAt(0).toUpperCase() + value.slice(1)}
    </span>
  )
}
