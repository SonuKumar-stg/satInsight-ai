// SatInsight AI — AI Insights Page

import Layout from '../components/layout/Layout'
import StatusBadge from '../components/ui/StatusBadge'
import { useStore } from '../store/dataStore'
import { PARAM_LABELS } from '../types/telemetry'

const SEVERITY_ICONS: Record<string, string> = {
  critical: '🔴',
  warning:  '🟡',
  info:     '🔵',
}

export default function AIInsights() {
  const {
    sessionId, analyzed, insights,
    isAnalyzing, runAnalysis,
  } = useStore()

  return (
    <Layout title="AI Insights" subtitle="Rule-based AI explanations and recommended actions">
      {!sessionId ? (
        <p style={{ color: '#64748b', fontSize: 13 }}>Load a dataset from the Overview page first.</p>
      ) : !analyzed ? (
        <div style={{
          padding: 32, background: '#0a1628', border: '1px solid #1e3a5f',
          borderRadius: 10, maxWidth: 480, textAlign: 'center',
        }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>✦</div>
          <h3 style={{ color: '#e2e8f0', fontSize: 15, margin: '0 0 8px' }}>No insights yet</h3>
          <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 20px' }}>
            Run analysis to generate AI-powered insight cards with recommended actions.
          </p>
          <button
            onClick={runAnalysis}
            disabled={isAnalyzing}
            style={{
              padding: '9px 24px', borderRadius: 8, fontSize: 13,
              background: '#1d4ed8', border: 'none', color: '#fff', cursor: isAnalyzing ? 'wait' : 'pointer',
            }}
          >
            {isAnalyzing ? 'Analyzing…' : 'Generate Insights'}
          </button>
        </div>
      ) : insights.length === 0 ? (
        <p style={{ color: '#64748b', fontSize: 13 }}>No significant patterns detected. Try uploading a dataset with anomalies.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <p style={{ color: '#475569', fontSize: 12, margin: 0 }}>
            {insights.length} insight{insights.length !== 1 ? 's' : ''} generated · ordered by severity
          </p>
          {insights.map((card) => (
            <div
              key={card.id}
              style={{
                background: '#0a1628',
                border: `1px solid ${card.severity === 'critical' ? '#7f1d1d' : card.severity === 'warning' ? '#78350f' : '#1e3a5f'}`,
                borderRadius: 10,
                padding: '18px 20px',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
                <span style={{ fontSize: 20, flexShrink: 0, marginTop: 1 }}>
                  {SEVERITY_ICONS[card.severity] ?? '⚠'}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                    <h3 style={{ color: '#e2e8f0', fontSize: 14, fontWeight: 700, margin: 0 }}>{card.title}</h3>
                    <StatusBadge value={card.severity} size="sm" />
                    <span style={{
                      padding: '1px 8px', borderRadius: 4,
                      background: '#0d1f3c', border: '1px solid #1e3a5f',
                      color: '#64748b', fontSize: 10,
                    }}>
                      {PARAM_LABELS[card.parameter as keyof typeof PARAM_LABELS] ?? card.parameter}
                    </span>
                    <span style={{ color: '#334155', fontSize: 11 }}>
                      rows {card.row_start}–{card.row_end} ({card.event_rows} reading{card.event_rows !== 1 ? 's' : ''})
                    </span>
                  </div>
                  <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.6, margin: 0 }}>{card.description}</p>
                </div>
              </div>

              {/* Value range */}
              <div style={{
                marginBottom: 12, padding: '6px 12px',
                background: '#0d1f3c', border: '1px solid #1e3a5f',
                borderRadius: 6, display: 'inline-flex', gap: 8, alignItems: 'center',
              }}>
                <span style={{ color: '#475569', fontSize: 11 }}>Observed range:</span>
                <span style={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: 12 }}>{card.value_range}</span>
              </div>

              {/* Recommended action */}
              <div style={{
                padding: '10px 14px',
                background: 'rgba(59,130,246,0.06)',
                border: '1px solid #1e3a5f',
                borderRadius: 6,
              }}>
                <div style={{ color: '#3b82f6', fontSize: 11, fontWeight: 600, marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Recommended Action
                </div>
                <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.6, margin: 0 }}>{card.recommended_action}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  )
}
