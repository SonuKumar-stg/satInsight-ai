// SatInsight AI — Overview Dashboard Page

import { useEffect } from 'react'
import Layout from '../components/layout/Layout'
import MetricCard from '../components/ui/MetricCard'
import StatusBadge from '../components/ui/StatusBadge'
import TelemetryChart from '../components/charts/TelemetryChart'
import FileUpload from '../components/ui/FileUpload'
import { useStore } from '../store/dataStore'

export default function Overview() {
  const {
    sessionId, rowCount, records,
    riskCounts, insights, analyzed,
    isLoading, isAnalyzing, error,
    loadSample, runAnalysis, checkBackend, clearError,
  } = useStore()

  useEffect(() => { checkBackend() }, [])

  return (
    <Layout title="Overview Dashboard" subtitle="Mission telemetry at a glance">
      {/* Error banner */}
      {error && (
        <div style={{
          marginBottom: 16, padding: '10px 16px',
          background: 'rgba(239,68,68,0.12)', border: '1px solid #7f1d1d',
          borderRadius: 8, color: '#f87171', fontSize: 13,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          {error}
          <button onClick={clearError} style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: 16 }}>×</button>
        </div>
      )}

      {/* No session — show onboarding */}
      {!sessionId ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, maxWidth: 800 }}>
          <div style={{ padding: 24, background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10 }}>
            <h2 style={{ color: '#e2e8f0', margin: '0 0 8px', fontSize: 15 }}>Load Sample Dataset</h2>
            <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 16px' }}>
              600 rows of realistic satellite telemetry with 10 injected anomaly events.
            </p>
            <button
              onClick={loadSample}
              disabled={isLoading}
              style={{
                padding: '8px 20px', borderRadius: 8, fontSize: 13,
                background: '#1d4ed8', border: 'none', color: '#fff', cursor: isLoading ? 'wait' : 'pointer',
              }}
            >
              {isLoading ? 'Loading…' : '▶  Load Sample Data'}
            </button>
          </div>
          <div style={{ padding: 24, background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10 }}>
            <h2 style={{ color: '#e2e8f0', margin: '0 0 8px', fontSize: 15 }}>Upload Your CSV</h2>
            <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 16px' }}>Upload satellite telemetry CSV with the required columns.</p>
            <FileUpload />
          </div>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
            <MetricCard label="Total Records"   value={rowCount}  icon="⊞" accent="#1e3a5f" />
            <MetricCard
              label="Total Anomalies"
              value={riskCounts ? riskCounts.total_anomalies : '—'}
              sub={riskCounts ? `${((riskCounts.total_anomalies / rowCount) * 100).toFixed(1)}% of rows` : 'Run analysis'}
              icon="⚠"
              accent={riskCounts?.total_anomalies ? '#78350f' : '#1e3a5f'}
            />
            <MetricCard
              label="Critical Events"
              value={riskCounts ? riskCounts.Critical : '—'}
              icon="🔴"
              accent={riskCounts?.Critical ? '#7f1d1d' : '#1e3a5f'}
            />
            <MetricCard label="AI Insights"  value={insights.length || '—'} icon="✦" accent="#1e3a5f" />
            <MetricCard label="Parameters"   value={7}  icon="∿" accent="#1e3a5f" sub="Monitored" />
          </div>

          {/* Analyze CTA */}
          {!analyzed && (
            <div style={{
              marginBottom: 24, padding: '14px 20px',
              background: 'rgba(59,130,246,0.08)', border: '1px solid #1e3a5f',
              borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div>
                <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>Dataset loaded — ready to analyze</span>
                <p style={{ color: '#475569', fontSize: 12, margin: '2px 0 0' }}>
                  Run AI/ML anomaly detection to detect patterns and generate insights.
                </p>
              </div>
              <button
                onClick={runAnalysis}
                disabled={isAnalyzing}
                style={{
                  padding: '8px 20px', borderRadius: 8, fontSize: 13,
                  background: '#1d4ed8', border: 'none', color: '#fff', cursor: isAnalyzing ? 'wait' : 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                {isAnalyzing ? 'Analyzing…' : '⚡ Run Analysis'}
              </button>
            </div>
          )}

          {/* Risk breakdown */}
          {riskCounts && (
            <div style={{
              marginBottom: 24, padding: '14px 20px',
              background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 8,
              display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap',
            }}>
              <span style={{ color: '#64748b', fontSize: 12 }}>Risk breakdown:</span>
              {(['Normal', 'Warning', 'Critical'] as const).map((r) => (
                <span key={r} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <StatusBadge value={r} size="sm" />
                  <span style={{ color: '#94a3b8', fontSize: 12 }}>
                    {riskCounts[r].toLocaleString()}
                  </span>
                </span>
              ))}
            </div>
          )}

          {/* Chart */}
          <div style={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10, padding: 20, marginBottom: 20 }}>
            <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>Telemetry Overview</h3>
            <TelemetryChart data={records} defaultParams={['temperature', 'battery_level', 'altitude']} height={260} />
          </div>

          {/* Recent insights preview */}
          {insights.length > 0 && (
            <div style={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10, padding: 20 }}>
              <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>
                Top AI Insights ({insights.length} total)
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {insights.slice(0, 3).map((c) => (
                  <div key={c.id} style={{
                    padding: '12px 16px', background: '#0d1f3c', borderRadius: 8,
                    border: '1px solid #1e3a5f', display: 'flex', gap: 12, alignItems: 'flex-start',
                  }}>
                    <StatusBadge value={c.severity} size="sm" />
                    <div>
                      <div style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{c.title}</div>
                      <div style={{ color: '#64748b', fontSize: 12, marginTop: 3 }}>{c.description.slice(0, 120)}…</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </Layout>
  )
}
