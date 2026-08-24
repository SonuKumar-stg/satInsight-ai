// SatInsight AI — Anomaly Detection Page

import Layout from '../components/layout/Layout'
import AnomalyChart from '../components/charts/AnomalyChart'
import AnomalyTable from '../components/tables/AnomalyTable'
import MetricCard from '../components/ui/MetricCard'
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell,
} from 'recharts'
import { useStore } from '../store/dataStore'
import { PARAM_LABELS } from '../types/telemetry'

const TICK_STYLE = { fill: '#475569', fontSize: 10 }

export default function AnomalyDetection() {
  const {
    sessionId, analyzed, anomalies, riskCounts,
    paramAnomalyCounts, totalRows, isAnalyzing, runAnalysis,
  } = useStore()

  const barData = Object.entries(paramAnomalyCounts)
    .map(([param, count]) => ({
      param,
      label: PARAM_LABELS[param as keyof typeof PARAM_LABELS] ?? param,
      count,
    }))
    .sort((a, b) => b.count - a.count)

  return (
    <Layout title="Anomaly Detection" subtitle="Isolation Forest + Rolling Z-Score">
      {!sessionId ? (
        <p style={{ color: '#64748b', fontSize: 13 }}>Load a dataset from the Overview page first.</p>
      ) : !analyzed ? (
        <div style={{
          padding: 32, background: '#0a1628', border: '1px solid #1e3a5f',
          borderRadius: 10, maxWidth: 480, textAlign: 'center',
        }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>⚡</div>
          <h3 style={{ color: '#e2e8f0', fontSize: 15, margin: '0 0 8px' }}>Analysis not run yet</h3>
          <p style={{ color: '#64748b', fontSize: 13, margin: '0 0 20px' }}>
            Run the AI/ML pipeline to detect anomalies using Isolation Forest and rolling Z-scores.
          </p>
          <button
            onClick={runAnalysis}
            disabled={isAnalyzing}
            style={{
              padding: '9px 24px', borderRadius: 8, fontSize: 13,
              background: '#1d4ed8', border: 'none', color: '#fff', cursor: isAnalyzing ? 'wait' : 'pointer',
            }}
          >
            {isAnalyzing ? 'Running analysis…' : 'Run Anomaly Detection'}
          </button>
        </div>
      ) : (
        <>
          {/* KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 24 }}>
            <MetricCard label="Total Rows"      value={totalRows}  icon="⊞" />
            <MetricCard label="Normal"          value={riskCounts?.Normal ?? 0}    icon="●" accent="#166534" />
            <MetricCard label="Warning"         value={riskCounts?.Warning ?? 0}   icon="⚠" accent="#78350f" />
            <MetricCard label="Critical"        value={riskCounts?.Critical ?? 0}  icon="🔴" accent="#7f1d1d" />
            <MetricCard
              label="Anomaly Rate"
              value={riskCounts ? `${((riskCounts.total_anomalies / riskCounts.total_rows) * 100).toFixed(1)}%` : '—'}
              icon="∿" accent="#1e3a5f"
            />
          </div>

          {/* Scatter chart */}
          <div style={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10, padding: 20, marginBottom: 20 }}>
            <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>
              Isolation Forest Score vs Row Index
            </h3>
            <AnomalyChart anomalies={anomalies} allCount={totalRows} height={260} />
          </div>

          {/* Bar chart: per-param counts */}
          {barData.length > 0 && (
            <div style={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10, padding: 20, marginBottom: 20 }}>
              <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>Anomalies by Parameter</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={barData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid stroke="#0d1f3c" strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={TICK_STYLE} tickLine={false} />
                  <YAxis tick={TICK_STYLE} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 11 }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {barData.map((_, i) => (
                      <Cell key={i} fill={`hsl(${210 + i * 25}, 70%, 50%)`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Anomaly table */}
          <div style={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 10, padding: 20 }}>
            <h3 style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 16px' }}>
              Anomaly Records — {anomalies.length} rows
            </h3>
            <AnomalyTable anomalies={anomalies} maxRows={200} />
          </div>
        </>
      )}
    </Layout>
  )
}
