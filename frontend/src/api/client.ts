// SatInsight AI — Axios API Client
// All backend endpoints typed and centralised here.

import axios from 'axios'
import type {
  DatasetLoadResponse,
  DataPageResponse,
  DataStatsResponse,
  DataPreviewResponse,
} from '../types/telemetry'
import type {
  AnalyzeResponse,
  AnomalyListResponse,
  InsightsResponse,
  AnomalySummary,
} from '../types/anomaly'

const api = axios.create({
  baseURL: '/api',          // Vite proxy forwards /api → http://localhost:8000
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Interceptor: surface server error messages clearly ─────────────────────
api.interceptors.response.use(
  (r) => r,
  (err) => {
    const msg =
      err?.response?.data?.detail ??
      err?.message ??
      'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------
export const healthCheck = () =>
  api.get<{ status: string; service: string; version: string }>('/health')

// ---------------------------------------------------------------------------
// Data / Sessions
// ---------------------------------------------------------------------------
export const loadSample = () =>
  api.get<DatasetLoadResponse>('/sample')

export const uploadCSV = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<DatasetLoadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getDataPage = (
  sessionId: string,
  page = 1,
  pageSize = 50
) =>
  api.get<DataPageResponse>(`/data/${sessionId}`, {
    params: { page, page_size: pageSize },
  })

export const getPreview = (sessionId: string, n = 10) =>
  api.get<DataPreviewResponse>(`/data/${sessionId}/preview`, { params: { n } })

export const getStats = (sessionId: string) =>
  api.get<DataStatsResponse>(`/data/${sessionId}/stats`)

// ---------------------------------------------------------------------------
// Anomaly Detection
// ---------------------------------------------------------------------------
export const runAnalysis = (sessionId: string) =>
  api.post<AnalyzeResponse>(`/analyze/${sessionId}`)

export const getAnomalies = (
  sessionId: string,
  page = 1,
  pageSize = 50,
  risk?: string
) =>
  api.get<AnomalyListResponse>(`/anomalies/${sessionId}`, {
    params: { page, page_size: pageSize, ...(risk ? { risk } : {}) },
  })

export const getAnomalySummary = (sessionId: string) =>
  api.get<AnomalySummary>(`/anomalies/${sessionId}/summary`)

// ---------------------------------------------------------------------------
// AI Insights
// ---------------------------------------------------------------------------
export const getInsights = (sessionId: string) =>
  api.get<InsightsResponse>(`/insights/${sessionId}`)

export const getInsightStatus = (sessionId: string) =>
  api.get<{ session_id: string; analysis_run: boolean; insight_count: number }>(
    `/insights/${sessionId}/status`
  )
