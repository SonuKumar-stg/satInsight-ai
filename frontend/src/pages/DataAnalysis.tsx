// SatInsight AI — Data Analysis Page

import Layout from '../components/layout/Layout'
import TelemetryChart from '../components/charts/TelemetryChart'
import { useStore } from '../store/dataStore'
import { NUMERIC_PARAMS, PARAM_LABELS, PARAM_UNITS } from '../types/telemetry'

export default function DataAnalysis() {
  const { sessionId, records, stats, isLoading } = useStore()

  return (
    <Layout title="Data Analysis" subtitle="Parameter trends and descriptive statistics">
      {!sessionId ? (
        <p style={{ color: '#64748b', fontSize: 13 }}>Load a dataset from the Overview page first.</p>
      ) : (
        <>
          {/* Multi-parameter chart */}
          <div style={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10, padding: 20, marginBottom: 24 }}>
            <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>
              Multi-Parameter Time Series — {records.length.toLocaleString()} points
            </h3>
            <TelemetryChart data={records} height={320} />
          </div>

          {/* Stats grid */}
          {stats ? (
            <div>
              <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>Parameter Statistics</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
                {NUMERIC_PARAMS.map((p) => {
                  const s = stats.parameters[p]
                  if (!s) return null
                  return (
                    <div key={p} style={{
                      background: '#0a1628', border: '1px solid #1e3a5f',
                      borderRadius: 10, padding: '14px 18px',
                    }}>
                      <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600, marginBottom: 12 }}>
                        {PARAM_LABELS[p]} <span style={{ color: '#475569', fontWeight: 400 }}>({PARAM_UNITS[p]})</span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                        {[
                          ['Min',    s.min],
                          ['Max',    s.max],
                          ['Mean',   s.mean],
                          ['Median', s.median],
                          ['Std',    s.std],
                          ['IQR',    s.iqr],
                        ].map(([label, val]) => (
                          <div key={String(label)}>
                            <div style={{ color: '#475569', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
                            <div style={{ color: '#94a3b8', fontSize: 13, fontWeight: 600 }}>
                              {val !== null && val !== undefined ? Number(val).toFixed(3) : '—'}
                            </div>
                          </div>
                        ))}
                      </div>
                      {s.missing_count > 0 && (
                        <div style={{ marginTop: 8, color: '#f59e0b', fontSize: 11 }}>
                          ⚠ {s.missing_count} missing value(s) imputed
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ) : (
            isLoading
              ? <p style={{ color: '#475569', fontSize: 13 }}>Loading statistics…</p>
              : <p style={{ color: '#475569', fontSize: 13 }}>Statistics not available.</p>
          )}
        </>
      )}
    </Layout>
  )
}
