// SatInsight AI — Multi-series Telemetry Time-series Chart

import { useState } from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'
import type { TelemetryRecord } from '../../types/telemetry'
import { NUMERIC_PARAMS, PARAM_COLORS, PARAM_LABELS, PARAM_UNITS } from '../../types/telemetry'

interface TelemetryChartProps {
  data: TelemetryRecord[]
  defaultParams?: string[]
  height?: number
}

const TICK_STYLE = { fill: '#475569', fontSize: 10 }

export default function TelemetryChart({
  data,
  defaultParams = ['temperature', 'battery_level', 'altitude'],
  height = 300,
}: TelemetryChartProps) {
  const [active, setActive] = useState<Set<string>>(new Set(defaultParams))

  if (!data.length) {
    return (
      <div style={emptyStyle(height)}>
        No telemetry data loaded
      </div>
    )
  }

  // Thin data to ≤300 points for chart performance
  const step = Math.max(1, Math.floor(data.length / 300))
  const chartData = data.filter((_, i) => i % step === 0).map((r) => ({
    ...r,
    _label: r.timestamp?.slice(11, 16) ?? '',   // HH:MM
  }))

  const toggle = (param: string) =>
    setActive((prev) => {
      const next = new Set(prev)
      next.has(param) ? next.delete(param) : next.add(param)
      return next
    })

  return (
    <div>
      {/* Parameter toggles */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
        {NUMERIC_PARAMS.map((p) => (
          <button
            key={p}
            onClick={() => toggle(p)}
            style={{
              padding: '3px 10px',
              borderRadius: 20,
              fontSize: 11,
              border: `1px solid ${active.has(p) ? PARAM_COLORS[p] : '#1e3a5f'}`,
              background: active.has(p) ? `${PARAM_COLORS[p]}22` : 'transparent',
              color: active.has(p) ? PARAM_COLORS[p] : '#475569',
              cursor: 'pointer',
            }}
          >
            {PARAM_LABELS[p]}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid stroke="#0d1f3c" strokeDasharray="3 3" />
          <XAxis
            dataKey="_label"
            tick={TICK_STYLE}
            interval={Math.floor(chartData.length / 8)}
            tickLine={false}
          />
          <YAxis tick={TICK_STYLE} tickLine={false} width={48} />
          <Tooltip
            contentStyle={{ background: '#0a1628', border: '1px solid #1e3a5f', borderRadius: 6, fontSize: 11 }}
            labelStyle={{ color: '#94a3b8' }}
            itemStyle={{ color: '#e2e8f0' }}
            formatter={(v, name) => [
              `${v != null && typeof v === 'number' ? v.toFixed(2) : String(v ?? '')} ${PARAM_UNITS[name as keyof typeof PARAM_UNITS] ?? ''}`,
              PARAM_LABELS[name as keyof typeof PARAM_LABELS] ?? name,
            ]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: '#64748b' }}
            formatter={(value) => PARAM_LABELS[value as keyof typeof PARAM_LABELS] ?? value}
          />
          {NUMERIC_PARAMS.filter((p) => active.has(p)).map((p) => (
            <Line
              key={p}
              type="monotone"
              dataKey={p}
              stroke={PARAM_COLORS[p]}
              dot={false}
              strokeWidth={1.5}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function emptyStyle(height: number): React.CSSProperties {
  return {
    height,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#334155',
    fontSize: 13,
    border: '1px dashed #1e3a5f',
    borderRadius: 8,
  }
}
