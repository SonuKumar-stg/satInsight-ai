// SatInsight AI — MetricCard KPI Component

interface MetricCardProps {
  label: string
  value: string | number
  sub?: string
  accent?: string   // border colour
  icon?: string
}

export default function MetricCard({ label, value, sub, accent = '#1e3a5f', icon }: MetricCardProps) {
  return (
    <div style={{
      background: '#0a1628',
      border: `1px solid ${accent}`,
      borderRadius: 10,
      padding: '16px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      minWidth: 160,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {icon && <span style={{ fontSize: 18 }}>{icon}</span>}
        <span style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {label}
        </span>
      </div>
      <div style={{ color: '#e2e8f0', fontSize: 26, fontWeight: 700, lineHeight: 1 }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {sub && <div style={{ color: '#475569', fontSize: 11 }}>{sub}</div>}
    </div>
  )
}
