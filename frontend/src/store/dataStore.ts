// SatInsight AI — Zustand Global Store

import { create } from 'zustand'
import type { TelemetryRecord, DataStatsResponse, DatasetLoadResponse } from '../types/telemetry'
import type { AnomalyRow, InsightCard, RiskCounts } from '../types/anomaly'
import * as api from '../api/client'

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------
export interface AppState {
  // Session
  sessionId: string | null
  datasetName: string | null
  rowCount: number

  // Telemetry records (current page)
  records: TelemetryRecord[]
  currentPage: number
  totalPages: number
  totalRows: number

  // Stats
  stats: DataStatsResponse | null

  // Analysis
  analyzed: boolean
  riskCounts: RiskCounts | null
  paramAnomalyCounts: Record<string, number>

  // Anomalies
  anomalies: AnomalyRow[]
  anomalyTotalCount: number

  // Insights
  insights: InsightCard[]

  // UI
  isLoading: boolean
  isAnalyzing: boolean
  error: string | null
  backendOnline: boolean

  // Actions
  loadSample: () => Promise<void>
  uploadFile: (file: File) => Promise<void>
  fetchPage: (page: number, pageSize?: number) => Promise<void>
  fetchStats: () => Promise<void>
  runAnalysis: () => Promise<void>
  fetchAnomalies: (page?: number, pageSize?: number, risk?: string) => Promise<void>
  fetchInsights: () => Promise<void>
  checkBackend: () => Promise<void>
  clearError: () => void
  reset: () => void
}

// ---------------------------------------------------------------------------
// Helper to set session from a DatasetLoadResponse
// ---------------------------------------------------------------------------
function applySession(
  set: (partial: Partial<AppState>) => void,
  data: DatasetLoadResponse
) {
  set({
    sessionId: data.session_id,
    datasetName: data.dataset_name,
    rowCount: data.row_count,
    analyzed: false,
    riskCounts: null,
    paramAnomalyCounts: {},
    anomalies: [],
    anomalyTotalCount: 0,
    insights: [],
    stats: null,
    records: [],
    currentPage: 1,
    totalPages: 1,
    totalRows: data.row_count,
    error: null,
  })
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------
export const useStore = create<AppState>((set, get) => ({
  // Initial state spread
  sessionId: null,
  datasetName: null,
  rowCount: 0,
  records: [],
  currentPage: 1,
  totalPages: 1,
  totalRows: 0,
  stats: null,
  analyzed: false,
  riskCounts: null,
  paramAnomalyCounts: {},
  anomalies: [],
  anomalyTotalCount: 0,
  insights: [],
  isLoading: false,
  isAnalyzing: false,
  error: null,
  backendOnline: false,

  // ── Actions ──────────────────────────────────────────────────────────────

  checkBackend: async () => {
    try {
      await api.healthCheck()
      set({ backendOnline: true })
    } catch {
      set({ backendOnline: false })
    }
  },

  loadSample: async () => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.loadSample()
      applySession(set, data)
      // Auto-fetch first page + stats
      const sid = data.session_id
      const [pageRes, statsRes] = await Promise.all([
        api.getDataPage(sid, 1, 50),
        api.getStats(sid),
      ])
      set({
        records: pageRes.data.records,
        currentPage: 1,
        totalPages: pageRes.data.total_pages,
        totalRows: pageRes.data.total_rows,
        stats: statsRes.data,
      })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  uploadFile: async (file: File) => {
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.uploadCSV(file)
      applySession(set, data)
      const sid = data.session_id
      const [pageRes, statsRes] = await Promise.all([
        api.getDataPage(sid, 1, 50),
        api.getStats(sid),
      ])
      set({
        records: pageRes.data.records,
        currentPage: 1,
        totalPages: pageRes.data.total_pages,
        totalRows: pageRes.data.total_rows,
        stats: statsRes.data,
      })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchPage: async (page: number, pageSize = 50) => {
    const { sessionId } = get()
    if (!sessionId) return
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.getDataPage(sessionId, page, pageSize)
      set({
        records: data.records,
        currentPage: data.page,
        totalPages: data.total_pages,
        totalRows: data.total_rows,
      })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchStats: async () => {
    const { sessionId } = get()
    if (!sessionId) return
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.getStats(sessionId)
      set({ stats: data })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  runAnalysis: async () => {
    const { sessionId } = get()
    if (!sessionId) return
    set({ isAnalyzing: true, error: null })
    try {
      const { data } = await api.runAnalysis(sessionId)
      set({
        analyzed: true,
        riskCounts: data.risk_counts,
        paramAnomalyCounts: data.param_anomaly_counts,
      })
      // Auto-fetch anomalies + insights
      const [anomRes, insRes] = await Promise.all([
        api.getAnomalies(sessionId, 1, 200),
        api.getInsights(sessionId),
      ])
      set({
        anomalies: anomRes.data.anomalies,
        anomalyTotalCount: anomRes.data.total_anomalies,
        insights: insRes.data.insights,
      })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isAnalyzing: false })
    }
  },

  fetchAnomalies: async (page = 1, pageSize = 200, risk?: string) => {
    const { sessionId } = get()
    if (!sessionId) return
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.getAnomalies(sessionId, page, pageSize, risk)
      set({
        anomalies: data.anomalies,
        anomalyTotalCount: data.total_anomalies,
      })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  fetchInsights: async () => {
    const { sessionId } = get()
    if (!sessionId) return
    set({ isLoading: true, error: null })
    try {
      const { data } = await api.getInsights(sessionId)
      set({ insights: data.insights })
    } catch (e: unknown) {
      set({ error: (e as Error).message })
    } finally {
      set({ isLoading: false })
    }
  },

  clearError: () => set({ error: null }),

  reset: () =>
    set({
      sessionId: null,
      datasetName: null,
      rowCount: 0,
      records: [],
      currentPage: 1,
      totalPages: 1,
      totalRows: 0,
      stats: null,
      analyzed: false,
      riskCounts: null,
      paramAnomalyCounts: {},
      anomalies: [],
      anomalyTotalCount: 0,
      insights: [],
      isLoading: false,
      isAnalyzing: false,
      error: null,
    }),
}))
