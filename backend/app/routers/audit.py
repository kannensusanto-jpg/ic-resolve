from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import AuditEntry
from app.schemas import AuditEntryOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=List[AuditEntryOut])
def get_audit_trail(
    period: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    q = db.query(AuditEntry)
    if period:
        q = q.filter(AuditEntry.period == period)
    if action_type:
        q = q.filter(AuditEntry.action_type == action_type)
    return q.order_by(AuditEntry.created_at.desc()).limit(limit).all()
