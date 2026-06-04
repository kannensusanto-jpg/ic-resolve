from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, Integer, Text, DateTime, Date, JSON, ForeignKey
from app.database import Base


class Entity(Base):
    __tablename__ = "entities"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    aliases = Column(JSON, default=list)
    functional_currency = Column(String, nullable=False, default="GBP")
    region = Column(String)
    ic_agreement_flag = Column(Boolean, default=True)
    owner_email = Column(String)


class FXRate(Base):
    __tablename__ = "fx_rates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_currency = Column(String, nullable=False)
    to_currency = Column(String, nullable=False, default="GBP")
    rate = Column(Float, nullable=False)
    effective_date = Column(Date, nullable=False)
    period = Column(String, nullable=False)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    counterparty_entity_id = Column(String, nullable=True)
    counterparty_raw = Column(String)
    account_code = Column(String, nullable=False)
    account_name = Column(String)
    amount_local = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    amount_gbp = Column(Float, nullable=True)
    period = Column(String, nullable=False)
    posting_date = Column(Date, nullable=False)
    description = Column(String)
    journal_type = Column(String, nullable=False)  # IC_RECEIVABLE or IC_PAYABLE
    is_normalised = Column(Boolean, default=False)


class TrialBalance(Base):
    __tablename__ = "trial_balances"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    account_code = Column(String, nullable=False)
    account_name = Column(String)
    counterparty_entity_id = Column(String, nullable=True)
    balance_local = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    balance_gbp = Column(Float, nullable=True)
    period = Column(String, nullable=False)


class CloseCalendar(Base):
    __tablename__ = "close_calendar"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    period = Column(String, nullable=False)
    close_date = Column(Date, nullable=False)
    status = Column(String, default="open")
    last_updated = Column(DateTime, default=datetime.utcnow)


class ToleranceConfig(Base):
    __tablename__ = "tolerance_configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_a_id = Column(String, nullable=False)
    entity_b_id = Column(String, nullable=False)
    absolute_threshold_gbp = Column(Float, default=1000.0)
    percentage_threshold = Column(Float, default=0.001)
    period = Column(String, nullable=True)


class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"
    id = Column(String, primary_key=True)
    entity_a_id = Column(String, nullable=False)
    entity_b_id = Column(String, nullable=False)
    period = Column(String, nullable=False)
    amount_a_gbp = Column(Float)
    amount_b_gbp = Column(Float)
    difference_gbp = Column(Float)
    tolerance_threshold_gbp = Column(Float)
    tolerance_pct = Column(Float)
    status = Column(String, nullable=False)
    match_type = Column(String)
    has_timing_difference = Column(Boolean, default=False)
    ai_reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dispute(Base):
    __tablename__ = "disputes"
    id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("reconciliation_matches.id"), nullable=False)
    entity_a_id = Column(String, nullable=False)
    entity_b_id = Column(String, nullable=False)
    period = Column(String, nullable=False)
    dispute_type = Column(String, nullable=False)
    owning_entity_id = Column(String, nullable=False)
    amount_gbp = Column(Float)
    sla_deadline = Column(Date)
    ai_description = Column(Text)
    status = Column(String, default="open")
    resolution_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False)          # user-supplied name, e.g. "IC Policy v2.1"
    filename = Column(String, nullable=False)
    content_type = Column(String)                   # pdf, docx, txt
    raw_text = Column(Text, nullable=False)
    char_count = Column(Integer)
    is_active = Column(Boolean, default=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class AuditEntry(Base):
    __tablename__ = "audit_trail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String, nullable=False)
    entity_a_id = Column(String)
    entity_b_id = Column(String)
    period = Column(String)
    action_detail = Column(Text)
    ai_model = Column(String)
    ai_reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
