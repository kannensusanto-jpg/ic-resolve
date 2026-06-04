from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Dispute, Entity
from app.schemas import DisputeOut, DisputeUpdate, DisputeResult
from app.services.disputes import run_disputes

router = APIRouter(prefix="/disputes", tags=["disputes"])


def _enrich(d: Dispute, entities: dict) -> DisputeOut:
    out = DisputeOut.model_validate(d)
    out.entity_a = entities.get(d.entity_a_id)
    out.entity_b = entities.get(d.entity_b_id)
    out.owning_entity = entities.get(d.owning_entity_id)
    return out


@router.post("/generate", response_model=DisputeResult)
def generate(period: str = "2024-03", use_ai: bool = True, db: Session = Depends(get_db)):
    return run_disputes(db, period, use_ai=use_ai)


@router.get("", response_model=List[DisputeOut])
def get_disputes(
    period: Optional[str] = None,
    status: Optional[str] = None,
    dispute_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Dispute)
    if period:
        q = q.filter(Dispute.period == period)
    if status:
        q = q.filter(Dispute.status == status)
    if dispute_type:
        q = q.filter(Dispute.dispute_type == dispute_type)
    entities = {e.id: e for e in db.query(Entity).all()}
    return [_enrich(d, entities) for d in q.order_by(Dispute.created_at.desc()).all()]


@router.get("/{dispute_id}", response_model=DisputeOut)
def get_dispute(dispute_id: str, db: Session = Depends(get_db)):
    d = db.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(404, "Dispute not found")
    entities = {e.id: e for e in db.query(Entity).all()}
    return _enrich(d, entities)


@router.patch("/{dispute_id}", response_model=DisputeOut)
def update_dispute(dispute_id: str, update: DisputeUpdate, db: Session = Depends(get_db)):
    d = db.get(Dispute, dispute_id)
    if not d:
        raise HTTPException(404, "Dispute not found")
    if update.status is not None:
        d.status = update.status
    if update.resolution_notes is not None:
        d.resolution_notes = update.resolution_notes
    d.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(d)
    entities = {e.id: e for e in db.query(Entity).all()}
    return _enrich(d, entities)
