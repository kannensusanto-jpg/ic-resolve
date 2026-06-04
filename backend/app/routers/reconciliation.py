from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import ReconciliationMatch, Entity, Dispute
from app.schemas import (
    ReconciliationMatchOut, ReconciliationSummary,
    MatchingResult, NormalisationResult, DisputeOut,
)
from app.services.normalisation import run_normalisation
from app.services.matching import run_matching
from app.services.orchestrator import run_full_reconciliation
from app.services.insights import get_summary

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


def _enrich_matches(matches, db: Session):
    entities = {e.id: e for e in db.query(Entity).all()}
    disputes_map = {d.match_id: d for d in db.query(Dispute).all()}
    result = []
    for m in matches:
        out = ReconciliationMatchOut.model_validate(m)
        out.entity_a = entities.get(m.entity_a_id)
        out.entity_b = entities.get(m.entity_b_id)
        if m.id in disputes_map:
            d = disputes_map[m.id]
            dout = DisputeOut.model_validate(d)
            dout.entity_a = entities.get(d.entity_a_id)
            dout.entity_b = entities.get(d.entity_b_id)
            dout.owning_entity = entities.get(d.owning_entity_id)
            out.dispute = dout
        result.append(out)
    return result


@router.post("/normalise", response_model=NormalisationResult)
def normalise(period: str = "2024-03", db: Session = Depends(get_db)):
    return run_normalisation(db, period)


@router.post("/match", response_model=MatchingResult)
def match(period: str = "2024-03", db: Session = Depends(get_db)):
    return run_matching(db, period)


@router.post("/run-all")
def run_all(period: str = "2024-03", use_ai: bool = True, db: Session = Depends(get_db)):
    return run_full_reconciliation(db, period, use_ai=use_ai)


@router.get("/summary", response_model=ReconciliationSummary)
def summary(period: str = "2024-03", db: Session = Depends(get_db)):
    return get_summary(db, period)


@router.get("/pairs", response_model=List[ReconciliationMatchOut])
def get_pairs(
    period: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(ReconciliationMatch)
    if period:
        q = q.filter(ReconciliationMatch.period == period)
    if status:
        q = q.filter(ReconciliationMatch.status == status)
    return _enrich_matches(q.all(), db)


@router.get("/pairs/{match_id}", response_model=ReconciliationMatchOut)
def get_pair(match_id: str, db: Session = Depends(get_db)):
    m = db.get(ReconciliationMatch, match_id)
    if not m:
        raise HTTPException(404, "Match not found")
    return _enrich_matches([m], db)[0]
