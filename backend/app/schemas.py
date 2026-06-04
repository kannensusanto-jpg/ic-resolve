from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date


class EntityOut(BaseModel):
    id: str
    name: str
    aliases: Optional[List[str]] = []
    functional_currency: str
    region: Optional[str] = None
    ic_agreement_flag: bool
    owner_email: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class FXRateOut(BaseModel):
    id: int
    from_currency: str
    to_currency: str
    rate: float
    effective_date: date
    period: str
    model_config = ConfigDict(from_attributes=True)


class JournalEntryOut(BaseModel):
    id: str
    entity_id: str
    counterparty_entity_id: Optional[str] = None
    counterparty_raw: Optional[str] = None
    account_code: str
    account_name: Optional[str] = None
    amount_local: float
    currency: str
    amount_gbp: Optional[float] = None
    period: str
    posting_date: date
    description: Optional[str] = None
    journal_type: str
    is_normalised: bool
    model_config = ConfigDict(from_attributes=True)


class TrialBalanceOut(BaseModel):
    id: int
    entity_id: str
    account_code: str
    account_name: Optional[str] = None
    counterparty_entity_id: Optional[str] = None
    balance_local: float
    currency: str
    balance_gbp: Optional[float] = None
    period: str
    model_config = ConfigDict(from_attributes=True)


class CloseCalendarOut(BaseModel):
    id: int
    entity_id: str
    period: str
    close_date: date
    status: str
    last_updated: datetime
    model_config = ConfigDict(from_attributes=True)


class ToleranceConfigOut(BaseModel):
    id: int
    entity_a_id: str
    entity_b_id: str
    absolute_threshold_gbp: float
    percentage_threshold: float
    period: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ToleranceConfigUpdate(BaseModel):
    entity_a_id: str
    entity_b_id: str
    absolute_threshold_gbp: float = 1000.0
    percentage_threshold: float = 0.001
    period: Optional[str] = None


class DisputeOut(BaseModel):
    id: str
    match_id: str
    entity_a_id: str
    entity_b_id: str
    entity_a: Optional[EntityOut] = None
    entity_b: Optional[EntityOut] = None
    owning_entity: Optional[EntityOut] = None
    period: str
    dispute_type: str
    owning_entity_id: str
    amount_gbp: Optional[float] = None
    sla_deadline: Optional[date] = None
    ai_description: Optional[str] = None
    status: str
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class DisputeUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


class ReconciliationMatchOut(BaseModel):
    id: str
    entity_a_id: str
    entity_b_id: str
    entity_a: Optional[EntityOut] = None
    entity_b: Optional[EntityOut] = None
    period: str
    amount_a_gbp: Optional[float] = None
    amount_b_gbp: Optional[float] = None
    difference_gbp: Optional[float] = None
    tolerance_threshold_gbp: Optional[float] = None
    tolerance_pct: Optional[float] = None
    status: str
    match_type: Optional[str] = None
    has_timing_difference: bool = False
    ai_reasoning: Optional[str] = None
    created_at: datetime
    dispute: Optional[DisputeOut] = None
    model_config = ConfigDict(from_attributes=True)


class AuditEntryOut(BaseModel):
    id: int
    action_type: str
    entity_a_id: Optional[str] = None
    entity_b_id: Optional[str] = None
    period: Optional[str] = None
    action_detail: Optional[str] = None
    ai_model: Optional[str] = None
    ai_reasoning: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReconciliationSummary(BaseModel):
    period: str
    total_pairs: int
    matched_pairs: int
    unmatched_pairs: int
    matched_pct: float
    total_difference_gbp: float
    open_disputes: int
    sla_breached: int
    entities_confirmed: int
    entities_pending: int
    by_match_type: dict


class NormalisationResult(BaseModel):
    aliases_resolved: int
    fx_applied: int
    missing_counterparties: int
    entries_processed: int
    warnings: List[str]


class MatchingResult(BaseModel):
    pairs_processed: int
    matched: int
    unmatched: int
    by_match_type: dict


class DisputeResult(BaseModel):
    disputes_created: int
    disputes_updated: int
    ai_descriptions_generated: int


class QueryRequest(BaseModel):
    query: str
    period: str = "2024-03"


class QueryResponse(BaseModel):
    query: str
    answer: str
    ai_model: str
    period: str
