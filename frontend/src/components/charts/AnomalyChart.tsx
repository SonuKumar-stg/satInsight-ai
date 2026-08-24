// SatInsight AI — Anomaly Scatter Chart (IF score vs row index)

import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts'
import type { AnomalyRow } from '../../types/anomaly'

interface AnomalyChartProps {
  anomalies: AnomalyRow[]
  allCount: number
  height?: number
}

const RISK_COLORS: Record<string, string> = {
  Critical: '#ef4444',
  Warning:  '#f59e0b',
  Normal:   '#22c55e',
}

const TICK_STYLE = { fill: '#475569', fontSize: 10 }

export default function AnomalyChart({ anomalies, allCount, height = 280 }: AnomalyChartProps) {
  if (!anomalies.length) {
    return (
      <div style={{
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#334155',
        fontSize: 13,
        border: '1px dashed #1e3a5f',
        borderRadius: 8,
      }}>
        Run analysis to see anomaly scatter chart
      </div>
    )
  }

  const criticalData  = anomalies.filter((a) => a.risk_level === 'Critical')
  const warningData   = anomalies.filter((a) => a.risk_level === 'Warning')

  const toPoint = (a: AnomalyRow) => ({
    x: a.row_index,
    y: parseFloat(a.if_score.toFixed(4)),
    z: parseFloat(a.max_zscore.toFixed(2)),
    risk: a.risk_level,
    params: a.anomaly_params.join(', '),
  })

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="#0d1f3c" strokeDasharray="3 3" />
        <XAxis
          dataKey="x"
          type="number"
          name="Row"
          domain={[0, allCount]}
          tick={TICK_STYLE}
          tickLine={false}
          label={{ value: 'Row Index', position: 'insideBottom', offset: -2, fill: '#475569', fontSize: 10 }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name="IF Score"
          tick={TICK_STYLE}
          tickLine={false}
          label={{ value: 'IF Score', angle: -90, position: 'insideLeft', fill: '#475569', fontSize: 10 }}
        />
        <Tooltip
          cursor={{ strokeDasharray: '3 3', stroke: '#1e3a5f' }}
          contentStyle={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 11 }}
          formatter={(v, name) => [v != null ? `${v}` : '', String(name)]}
          labelFormatter={() => ''}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Scatter name="Critical" data={criticalData.map(toPoint)} fill={RISK_COLORS.Critical}>
          {criticalData.map((_, i) => <Cell key={i} fill={RISK_COLORS.Critical} />)}
        </Scatter>
        <Scatter name="Warning" data={warningData.map(toPoint)} fill={RISK_COLORS.Warning}>
          {warningData.map((_, i) => <Cell key={i} fill={RISK_COLORS.Warning} />)}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  )
}
