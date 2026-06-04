export interface Entity {
  id: string
  name: string
  aliases: string[]
  functional_currency: string
  region: string | null
  ic_agreement_flag: boolean
  owner_email: string | null
}

export interface FXRate {
  id: number
  from_currency: string
  to_currency: string
  rate: number
  effective_date: string
  period: string
}

export interface JournalEntry {
  id: string
  entity_id: string
  counterparty_entity_id: string | null
  counterparty_raw: string | null
  account_code: string
  account_name: string | null
  amount_local: number
  currency: string
  amount_gbp: number | null
  period: string
  posting_date: string
  description: string | null
  journal_type: 'IC_RECEIVABLE' | 'IC_PAYABLE'
  is_normalised: boolean
}

export interface TrialBalance {
  id: number
  entity_id: string
  account_code: string
  account_name: string | null
  counterparty_entity_id: string | null
  balance_local: number
  currency: string
  balance_gbp: number | null
  period: string
}

export interface CloseCalendar {
  id: number
  entity_id: string
  period: string
  close_date: string
  status: 'open' | 'submitted' | 'confirmed' | 'closed'
  last_updated: string
}

export interface ToleranceConfig {
  id: number
  entity_a_id: string
  entity_b_id: string
  absolute_threshold_gbp: number
  percentage_threshold: number
  period: string | null
}

export type DisputeType = 'timing' | 'fx' | 'missing_posting' | 'amount_difference'
export type DisputeStatus = 'open' | 'in_review' | 'resolved' | 'escalated'
export type MatchStatus = 'matched' | 'unmatched'
export type MatchType =
  | 'exact'
  | 'within_tolerance'
  | 'timing_difference'
  | 'missing_posting'
  | 'fx_difference'
  | 'amount_difference'
  | 'no_data'

export interface Dispute {
  id: string
  match_id: string
  entity_a_id: string
  entity_b_id: string
  entity_a: Entity | null
  entity_b: Entity | null
  owning_entity: Entity | null
  period: string
  dispute_type: DisputeType
  owning_entity_id: string
  amount_gbp: number | null
  sla_deadline: string | null
  ai_description: string | null
  status: DisputeStatus
  resolution_notes: string | null
  created_at: string
  updated_at: string
}

export interface ReconciliationMatch {
  id: string
  entity_a_id: string
  entity_b_id: string
  entity_a: Entity | null
  entity_b: Entity | null
  period: string
  amount_a_gbp: number | null
  amount_b_gbp: number | null
  difference_gbp: number | null
  tolerance_threshold_gbp: number | null
  tolerance_pct: number | null
  status: MatchStatus
  match_type: MatchType | null
  has_timing_difference: boolean
  ai_reasoning: string | null
  created_at: string
  dispute: Dispute | null
}

export interface ReconciliationSummary {
  period: string
  total_pairs: number
  matched_pairs: number
  unmatched_pairs: number
  matched_pct: number
  total_difference_gbp: number
  open_disputes: number
  sla_breached: number
  entities_confirmed: number
  entities_pending: number
  by_match_type: Record<string, number>
}

export interface AuditEntry {
  id: number
  action_type: string
  entity_a_id: string | null
  entity_b_id: string | null
  period: string | null
  action_detail: string | null
  ai_model: string | null
  ai_reasoning: string | null
  created_at: string
}

export interface NormalisationResult {
  aliases_resolved: number
  fx_applied: number
  missing_counterparties: number
  entries_processed: number
  warnings: string[]
}

export interface MatchingResult {
  pairs_processed: number
  matched: number
  unmatched: number
  by_match_type: Record<string, number>
}

export interface DisputeResult {
  disputes_created: number
  disputes_updated: number
  ai_descriptions_generated: number
}

export interface QueryResponse {
  query: string
  answer: string
  ai_model: string
  period: string
}
