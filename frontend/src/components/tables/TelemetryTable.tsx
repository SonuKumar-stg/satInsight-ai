// SatInsight AI — Paginated Telemetry Table

import { useState } from 'react'
import { useStore } from '../../store/dataStore'
import { NUMERIC_PARAMS, PARAM_LABELS, PARAM_UNITS } from '../../types/telemetry'

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

const COLUMNS = ['timestamp', ...NUMERIC_PARAMS]

export default function TelemetryTable() {
  const { records, currentPage, totalPages, totalRows, fetchPage, isLoading } = useStore()
  const [pageSize] = useState(50)

  if (!records.length && !isLoading) {
    return (
      <div style={{ padding: '32px', color: '#334155', textAlign: 'center', fontSize: 13 }}>
        Load a dataset to view telemetry records.
      </div>
    )
  }

  return (
    <div>
      {/* Pagination controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ color: '#475569', fontSize: 12 }}>
          {totalRows.toLocaleString()} total rows · page {currentPage} of {totalPages}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { label: '← Prev', disabled: currentPage <= 1,          action: () => fetchPage(currentPage - 1, pageSize) },
            { label: 'Next →', disabled: currentPage >= totalPages,  action: () => fetchPage(currentPage + 1, pageSize) },
          ].map(({ label, disabled, action }) => (
            <button
              key={label}
              onClick={action}
              disabled={disabled || isLoading}
              style={{
                padding: '5px 12px',
                fontSize: 12,
                borderRadius: 6,
                border: '1px solid #1e3a5f',
                background: disabled ? 'transparent' : '#0a1628',
                color: disabled ? '#334155' : '#94a3b8',
                cursor: disabled ? 'default' : 'pointer',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', border: '1px solid #1e3a5f', borderRadius: 8 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#0a1628' }}>
              {COLUMNS.map((col) => (
                <th key={col} style={TH_STYLE}>
                  {col === 'timestamp'
                    ? 'Timestamp'
                    : `${PARAM_LABELS[col as keyof typeof PARAM_LABELS] ?? col} (${PARAM_UNITS[col as keyof typeof PARAM_UNITS] ?? ''})`}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((row, i) => (
              <tr
                key={i}
                style={{ background: i % 2 === 0 ? 'transparent' : '#0a162820' }}
              >
                {COLUMNS.map((col) => (
                  <td key={col} style={TD_STYLE}>
                    {col === 'timestamp'
                      ? String(row[col] ?? '').replace('T', ' ').replace('Z', '')
                      : row[col] !== null && row[col] !== undefined
                      ? Number(row[col]).toFixed(col === 'velocity' ? 4 : 2)
                      : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
