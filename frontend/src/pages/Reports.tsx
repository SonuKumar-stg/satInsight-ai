// SatInsight AI — Reports Page

import Layout from '../components/layout/Layout'
import StatusBadge from '../components/ui/StatusBadge'
import { useStore } from '../store/dataStore'
import { PARAM_LABELS, PARAM_UNITS } from '../types/telemetry'

export default function Reports() {
  const {
    sessionId, datasetName, rowCount,
    riskCounts, paramAnomalyCounts, insights, stats,
    analyzed,
  } = useStore()

  const downloadJSON = () => {
    if (!sessionId) return
    const report = {
      generated_at: new Date().toISOString(),
      session_id: sessionId,
      dataset_name: datasetName,
      row_count: rowCount,
      analysis_run: analyzed,
      risk_counts: riskCounts,
      param_anomaly_counts: paramAnomalyCounts,
      statistics: stats?.parameters ?? {},
      insights: insights,
    }
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `satinsight_report_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadCSVInsights = () => {
    if (!insights.length) return
    const header = 'id,title,severity,parameter,value_range,row_start,row_end,event_rows,recommended_action\n'
    const rows = insights.map((c) =>
      [c.id, `"${c.title}"`, c.severity, c.parameter, `"${c.value_range}"`,
       c.row_start, c.row_end, c.event_rows, `"${c.recommended_action}"`].join(',')
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `satinsight_insights_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Layout title="Reports" subtitle="Export analysis results">
      {!sessionId ? (
        <p style={{ color: '#64748b', fontSize: 13 }}>Load a dataset from the Overview page first.</p>
      ) : (
        <>
          {/* Summary panel */}
          <div style={{
            background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10,
            padding: 20, marginBottom: 20,
          }}>
            <h3 style={{ color: '#e2e8f0', fontSize: 14, margin: '0 0 16px' }}>Session Summary</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              {[
                ['Dataset',     datasetName ?? '—'],
                ['Session ID',  sessionId?.slice(0, 8) + '…'],
                ['Total Rows',  rowCount.toLocaleString()],
                ['Analysis',    analyzed ? 'Complete' : 'Not run'],
                ['Anomalies',   analyzed ? riskCounts?.total_anomalies.toString() ?? '—' : '—'],
                ['Insights',    insights.length.toString()],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 8, fontSize: 13 }}>
                  <span style={{ color: '#475569', minWidth: 100 }}>{k}</span>
                  <span style={{ color: '#e2e8f0' }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Risk breakdown */}
          {riskCounts && (
            <div style={{
              background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10,
              padding: 20, marginBottom: 20,
            }}>
              <h3 style={{ color: '#e2e8f0', fontSize: 14, margin: '0 0 16px' }}>Risk Breakdown</h3>
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                {(['Normal', 'Warning', 'Critical'] as const).map((r) => (
                  <div key={r} style={{
                    padding: '12px 20px', background: '#0d1f3c',
                    border: '1px solid #1e3a5f', borderRadius: 8, textAlign: 'center',
                  }}>
                    <div style={{ marginBottom: 6 }}><StatusBadge value={r} /></div>
                    <div style={{ color: '#e2e8f0', fontSize: 22, fontWeight: 700 }}>
                      {riskCounts[r].toLocaleString()}
                    </div>
                    <div style={{ color: '#475569', fontSize: 11 }}>
                      {((riskCounts[r] / riskCounts.total_rows) * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Statistics table */}
          {stats && (
            <div style={{
              background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10,
              padding: 20, marginBottom: 20, overflowX: 'auto',
            }}>
              <h3 style={{ color: '#e2e8f0', fontSize: 14, margin: '0 0 16px' }}>Parameter Statistics</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr>
                    {['Parameter', 'Unit', 'Min', 'Max', 'Mean', 'Std', 'Median'].map((h) => (
                      <th key={h} style={{
                        padding: '6px 10px', color: '#475569', textAlign: 'left',
                        borderBottom: '1px solid #1e3a5f', fontSize: 11,
                        textTransform: 'uppercase', letterSpacing: '0.05em',
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(stats.parameters).map(([param, s]) => (
                    <tr key={param}>
                      <td style={{ padding: '6px 10px', color: '#e2e8f0', borderBottom: '1px solid #0d1f3c' }}>
                        {PARAM_LABELS[param as keyof typeof PARAM_LABELS] ?? param}
                      </td>
                      <td style={{ padding: '6px 10px', color: '#64748b', borderBottom: '1px solid #0d1f3c' }}>
                        {PARAM_UNITS[param as keyof typeof PARAM_UNITS] ?? ''}
                      </td>
                      {[s.min, s.max, s.mean, s.std, s.median].map((v, i) => (
                        <td key={i} style={{ padding: '6px 10px', color: '#94a3b8', borderBottom: '1px solid #0d1f3c', fontFamily: 'monospace' }}>
                          {v !== null ? Number(v).toFixed(3) : '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Download buttons */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button
              onClick={downloadJSON}
              style={{
                padding: '10px 24px', borderRadius: 8, fontSize: 13,
                background: '#1d4ed8', border: 'none', color: '#fff', cursor: 'pointer',
              }}
            >
              ⬇ Download Full Report (JSON)
            </button>
            <button
              onClick={downloadCSVInsights}
              disabled={!insights.length}
              style={{
                padding: '10px 24px', borderRadius: 8, fontSize: 13,
                background: insights.length ? '#0d1f3c' : 'transparent',
                border: '1px solid #1e3a5f',
                color: insights.length ? '#94a3b8' : '#334155',
                cursor: insights.length ? 'pointer' : 'default',
              }}
            >
              ⬇ Download Insights (CSV)
            </button>
          </div>
        </>
      )}
    </Layout>
  )
}
