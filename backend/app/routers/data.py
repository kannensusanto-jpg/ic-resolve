from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.seed_data import seed_database
from app.services.excel_import import (
    import_trial_balance, import_ic_transactions, import_fx_rates,
    derive_journal_entries_from_tb,
)
from app.models import (
    Entity, FXRate, JournalEntry, TrialBalance, CloseCalendar, ToleranceConfig,
    ReconciliationMatch, Dispute, AuditEntry,
)
from app.schemas import (
    EntityOut, FXRateOut, JournalEntryOut, TrialBalanceOut,
    CloseCalendarOut, ToleranceConfigOut, ToleranceConfigUpdate,
)

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/status")
def data_status(db: Session = Depends(get_db)):
    """Returns whether usable data exists, and which periods are available."""
    from sqlalchemy import func
    entry_count = db.query(JournalEntry).count()
    periods = [r[0] for r in db.query(JournalEntry.period).distinct().all() if r[0]]
    return {
        "has_data": entry_count > 0,
        "entry_count": entry_count,
        "periods": sorted(periods),
        "latest_period": sorted(periods)[-1] if periods else None,
    }


@router.delete("/clear")
def clear_data(db: Session = Depends(get_db)):
    """Delete all uploaded data, matches, disputes, and audit entries."""
    for model in [AuditEntry, Dispute, ReconciliationMatch, JournalEntry, TrialBalance, FXRate, CloseCalendar, ToleranceConfig, Entity]:
        db.query(model).delete()
    db.commit()
    return {"status": "cleared"}


@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    counts = seed_database(db)
    return {"status": "seeded", "counts": counts}


@router.post("/upload/trial-balance")
async def upload_trial_balance(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "File must be an Excel file (.xlsx or .xls)")
    content = await file.read()
    result = import_trial_balance(db, content)
    return {"status": "imported", **result}


@router.post("/upload/ic-transactions")
async def upload_ic_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "File must be an Excel file (.xlsx or .xls)")
    content = await file.read()
    result = import_ic_transactions(db, content)
    return {"status": "imported", **result}


@router.post("/upload/fx-rates")
async def upload_fx_rates(
    file: UploadFile = File(...),
    period: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "File must be an Excel file (.xlsx or .xls)")
    content = await file.read()
    result = import_fx_rates(db, content, default_period=period)
    return {"status": "imported", **result}


@router.post("/upload/both")
async def upload_both(
    trial_balance: UploadFile = File(...),
    ic_transactions: Optional[UploadFile] = File(None),
    fx_rates: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    tb_content = await trial_balance.read()
    tb_result = import_trial_balance(db, tb_content)
    period = tb_result["period"]

    tx_result = None
    if ic_transactions and ic_transactions.filename:
        tx_content = await ic_transactions.read()
        tx_result = import_ic_transactions(db, tx_content)
    else:
        # No transaction file — derive synthetic entries from the TB
        tx_result = derive_journal_entries_from_tb(db, period)
        tx_result["source"] = "trial_balance"

    fx_result = None
    if fx_rates and fx_rates.filename:
        fx_content = await fx_rates.read()
        fx_result = import_fx_rates(db, fx_content, default_period=period)

    return {
        "status": "imported",
        "trial_balance": tb_result,
        "ic_transactions": tx_result,
        "fx_rates": fx_result,
        "period": period,
    }


@router.get("/entities", response_model=List[EntityOut])
def get_entities(db: Session = Depends(get_db)):
    return db.query(Entity).all()


@router.get("/fx-rates", response_model=List[FXRateOut])
def get_fx_rates(period: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FXRate)
    if period:
        q = q.filter(FXRate.period == period)
    return q.all()


@router.get("/journal-entries", response_model=List[JournalEntryOut])
def get_journal_entries(
    period: Optional[str] = None,
    entity_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(JournalEntry)
    if period:
        q = q.filter(JournalEntry.period == period)
    if entity_id:
        q = q.filter(JournalEntry.entity_id == entity_id)
    return q.all()


@router.get("/trial-balances", response_model=List[TrialBalanceOut])
def get_trial_balances(
    period: Optional[str] = None,
    entity_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(TrialBalance)
    if period:
        q = q.filter(TrialBalance.period == period)
    if entity_id:
        q = q.filter(TrialBalance.entity_id == entity_id)
    return q.all()


@router.get("/close-calendar", response_model=List[CloseCalendarOut])
def get_close_calendar(period: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(CloseCalendar)
    if period:
        q = q.filter(CloseCalendar.period == period)
    return q.all()


@router.get("/tolerance-configs", response_model=List[ToleranceConfigOut])
def get_tolerance_configs(db: Session = Depends(get_db)):
    return db.query(ToleranceConfig).all()


@router.post("/tolerance-configs", response_model=ToleranceConfigOut)
def upsert_tolerance_config(config: ToleranceConfigUpdate, db: Session = Depends(get_db)):
    existing = db.query(ToleranceConfig).filter(
        ToleranceConfig.entity_a_id == config.entity_a_id,
        ToleranceConfig.entity_b_id == config.entity_b_id,
    ).first()
    if existing:
        existing.absolute_threshold_gbp = config.absolute_threshold_gbp
        existing.percentage_threshold = config.percentage_threshold
        existing.period = config.period
    else:
        existing = ToleranceConfig(**config.model_dump())
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing
