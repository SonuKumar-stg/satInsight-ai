// SatInsight AI — TypeScript Types: Anomaly & Insights

export type RiskLevel = 'Normal' | 'Warning' | 'Critical'
export type Severity = 'info' | 'warning' | 'critical'

export interface RiskCounts {
  Normal: number
  Warning: number
  Critical: number
  total_anomalies: number
  total_rows: number
}

export interface AnalyzeResponse {
  session_id: string
  dataset_name: string
  row_count: number
  risk_counts: RiskCounts
  param_anomaly_counts: Record<string, number>
  message: string
}

export interface AnomalyRow {
  row_index: number
  timestamp: string | null
  temperature: number | null
  radiation: number | null
  pressure: number | null
  battery_level: number | null
  signal_strength: number | null
  velocity: number | null
  altitude: number | null
  if_score: number
  max_zscore: number
  risk_level: RiskLevel
  anomaly_params: string[]
  [key: string]: string | number | string[] | null
}

export interface AnomalyListResponse {
  session_id: string
  page: number
  page_size: number
  total_anomalies: number
  total_pages: number
  filter_risk: string | null
  anomalies: AnomalyRow[]
}

export interface InsightCard {
  id: string
  title: string
  description: string
  severity: Severity
  parameter: string
  value_range: string
  recommended_action: string
  row_start: number
  row_end: number
  event_rows: number
}

export interface InsightsResponse {
  session_id: string
  dataset_name: string
  total_insights: number
  insights: InsightCard[]
  analysis_run: boolean
}

export interface AnomalySummary {
  session_id: string
  risk_counts: RiskCounts
  param_anomaly_counts: Record<string, number>
}
