// SatInsight AI — TypeScript Types: Telemetry

export interface TelemetryRecord {
  timestamp: string
  temperature: number | null
  radiation: number | null
  pressure: number | null
  battery_level: number | null
  signal_strength: number | null
  velocity: number | null
  altitude: number | null
  [key: string]: string | number | null
}

export interface DatasetMeta {
  session_id: string
  dataset_name: string
  row_count: number
  columns: string[]
  created_at: number
  has_anomalies: boolean
}

export interface DatasetLoadResponse {
  session_id: string
  dataset_name: string
  row_count: number
  columns: string[]
  warnings: string[]
  message: string
}

export interface DataPageResponse {
  session_id: string
  page: number
  page_size: number
  total_rows: number
  total_pages: number
  records: TelemetryRecord[]
}

export interface ParameterStats {
  count: number
  mean: number | null
  std: number | null
  min: number | null
  max: number | null
  q1: number | null
  median: number | null
  q3: number | null
  iqr: number | null
  missing_count: number
}

export interface DataStatsResponse {
  session_id: string
  dataset_name: string
  row_count: number
  parameters: Record<string, ParameterStats>
}

export interface DataPreviewResponse {
  session_id: string
  dataset_name: string
  row_count: number
  columns: string[]
  preview_rows: TelemetryRecord[]
  warnings: string[]
}

export const NUMERIC_PARAMS = [
  'temperature',
  'radiation',
  'pressure',
  'battery_level',
  'signal_strength',
  'velocity',
  'altitude',
] as const

export type NumericParam = (typeof NUMERIC_PARAMS)[number]

export const PARAM_UNITS: Record<NumericParam, string> = {
  temperature: '°C',
  radiation: 'mSv/h',
  pressure: 'hPa',
  battery_level: '%',
  signal_strength: 'dBm',
  velocity: 'km/s',
  altitude: 'km',
}

export const PARAM_LABELS: Record<NumericParam, string> = {
  temperature: 'Temperature',
  radiation: 'Radiation',
  pressure: 'Pressure',
  battery_level: 'Battery',
  signal_strength: 'Signal',
  velocity: 'Velocity',
  altitude: 'Altitude',
}

export const PARAM_COLORS: Record<NumericParam, string> = {
  temperature: '#f97316',
  radiation: '#a855f7',
  pressure: '#06b6d4',
  battery_level: '#22c55e',
  signal_strength: '#3b82f6',
  velocity: '#f59e0b',
  altitude: '#ec4899',
}
