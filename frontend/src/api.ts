import axios from 'axios'
import type {
  Entity, FXRate, JournalEntry, TrialBalance, CloseCalendar, ToleranceConfig,
  ReconciliationMatch, ReconciliationSummary, Dispute, AuditEntry,
  NormalisationResult, MatchingResult, DisputeResult, QueryResponse,
} from './types'

const http = axios.create({ baseURL: '/api' })

export const api = {
  health: () => http.get('/health'),

  // Data
  getDataStatus: () => http.get<{ has_data: boolean; entry_count: number; periods: string[]; latest_period: string | null }>('/data/status'),
  seed: () => http.post('/data/seed'),
  getEntities: () => http.get<Entity[]>('/data/entities'),
  getFXRates: (period?: string) => http.get<FXRate[]>('/data/fx-rates', { params: { period } }),
  getJournalEntries: (period?: string, entity_id?: string) =>
    http.get<JournalEntry[]>('/data/journal-entries', { params: { period, entity_id } }),
  getTrialBalances: (period?: string, entity_id?: string) =>
    http.get<TrialBalance[]>('/data/trial-balances', { params: { period, entity_id } }),
  getCloseCalendar: (period?: string) =>
    http.get<CloseCalendar[]>('/data/close-calendar', { params: { period } }),
  getToleranceConfigs: () => http.get<ToleranceConfig[]>('/data/tolerance-configs'),
  upsertTolerance: (config: Partial<ToleranceConfig>) =>
    http.post<ToleranceConfig>('/data/tolerance-configs', config),

  // Reconciliation
  normalise: (period = '2024-03') =>
    http.post<NormalisationResult>('/reconciliation/normalise', null, { params: { period } }),
  match: (period = '2024-03') =>
    http.post<MatchingResult>('/reconciliation/match', null, { params: { period } }),
  runAll: (period = '2024-03', use_ai = true) =>
    http.post('/reconciliation/run-all', null, { params: { period, use_ai } }),
  getSummary: (period = '2024-03') =>
    http.get<ReconciliationSummary>('/reconciliation/summary', { params: { period } }),
  getPairs: (period?: string, status?: string) =>
    http.get<ReconciliationMatch[]>('/reconciliation/pairs', { params: { period, status } }),
  getPair: (id: string) => http.get<ReconciliationMatch>(`/reconciliation/pairs/${id}`),

  // Disputes
  generateDisputes: (period = '2024-03', use_ai = true) =>
    http.post<DisputeResult>('/disputes/generate', null, { params: { period, use_ai } }),
  getDisputes: (period?: string, status?: string, dispute_type?: string) =>
    http.get<Dispute[]>('/disputes', { params: { period, status, dispute_type } }),
  updateDispute: (id: string, update: { status?: string; resolution_notes?: string }) =>
    http.patch<Dispute>(`/disputes/${id}`, update),

  // Insights
  getInsightsSummary: (period = '2024-03') =>
    http.get<ReconciliationSummary>('/insights/summary', { params: { period } }),
  getCloseSummary: (period = '2024-03') =>
    http.get<{ period: string; summary: string }>('/insights/close-summary', { params: { period } }),

  // Query
  query: (query: string, period = '2024-03') =>
    http.post<QueryResponse>('/query', { query, period }),

  // Audit
  getAuditTrail: (period?: string, action_type?: string) =>
    http.get<AuditEntry[]>('/audit', { params: { period, action_type } }),
}
