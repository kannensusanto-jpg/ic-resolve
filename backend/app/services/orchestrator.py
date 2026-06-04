from sqlalchemy.orm import Session
from app.services.normalisation import run_normalisation
from app.services.matching import run_matching
from app.services.disputes import run_disputes


def run_full_reconciliation(db: Session, period: str = "2024-03", use_ai: bool = True) -> dict:
    norm = run_normalisation(db, period)
    match = run_matching(db, period)
    disp = run_disputes(db, period, use_ai=use_ai)
    return {
        "period": period,
        "normalisation": norm.model_dump(),
        "matching": match.model_dump(),
        "disputes": disp.model_dump(),
    }
