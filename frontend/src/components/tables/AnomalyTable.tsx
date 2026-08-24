// SatInsight AI — Anomaly Table with risk badges

import StatusBadge from '../ui/StatusBadge'
import type { AnomalyRow } from '../../types/anomaly'
import { PARAM_LABELS } from '../../types/telemetry'

interface AnomalyTableProps {
  anomalies: AnomalyRow[]
  maxRows?: number
}

const TH_STYLE: React.CSSProperties = {
  padding: '8px 12px',
  color: '#475569',
  fontSize: 11,
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  textAlign: 'left',
  borderBottom: '1px solid #1e3a5f',
  whiteSpace: 'nowrap',
}

const TD_STYLE: React.CSSProperties = {
  padding: '7px 12px',
  color: '#94a3b8',
  fontSize: 12,
  borderBottom: '1px solid #0d1f3c',
  whiteSpace: 'nowrap',
}

export default function AnomalyTable({ anomalies, maxRows = 100 }: AnomalyTableProps) {
  if (!anomalies.length) {
    return (
      <div style={{ padding: '32px', color: '#334155', textAlign: 'center', fontSize: 13 }}>
        No anomalies to display. Run analysis first.
      </div>
    )
  }

  const rows = anomalies.slice(0, maxRows)

  return (
    <div style={{ overflowX: 'auto', border: '1px solid #1e3a5f', borderRadius: 8 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: '#0a1628' }}>
            {['Row', 'Timestamp', 'Risk', 'IF Score', 'Z-Score', 'Flagged Parameters'].map((h) => (
              <th key={h} style={TH_STYLE}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : '#0a162820' }}>
              <td style={{ ...TD_STYLE, color: '#64748b' }}>{row.row_index}</td>
              <td style={TD_STYLE}>
                {String(row.timestamp ?? '').replace('T', ' ').replace('Z', '')}
              </td>
              <td style={TD_STYLE}>
                <StatusBadge value={row.risk_level} size="sm" />
              </td>
              <td style={{ ...TD_STYLE, fontFamily: 'monospace', fontSize: 11 }}>
                {row.if_score.toFixed(4)}
              </td>
              <td style={{ ...TD_STYLE, fontFamily: 'monospace', fontSize: 11 }}>
                {row.max_zscore.toFixed(2)}
              </td>
              <td style={TD_STYLE}>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {row.anomaly_params.length > 0
                    ? row.anomaly_params.map((p) => (
                        <span
                          key={p}
                          style={{
                            padding: '1px 6px',
                            background: '#0d1f3c',
                            border: '1px solid #1e3a5f',
                            borderRadius: 4,
                            fontSize: 10,
                            color: '#64748b',
                          }}
                        >
                          {PARAM_LABELS[p as keyof typeof PARAM_LABELS] ?? p}
                        </span>
                      ))
                    : <span style={{ color: '#334155', fontSize: 11 }}>—</span>}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
