from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.insights import get_summary, get_close_summary
from app.schemas import ReconciliationSummary

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/summary", response_model=ReconciliationSummary)
def summary(period: str = "2024-03", db: Session = Depends(get_db)):
    return get_summary(db, period)


@router.get("/close-summary")
def close_summary(period: str = "2024-03", db: Session = Depends(get_db)):
    text = get_close_summary(db, period)
    return {"period": period, "summary": text}
