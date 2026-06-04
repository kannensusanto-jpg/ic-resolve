from datetime import date
from sqlalchemy.orm import Session
from app.models import ReconciliationMatch, Dispute, CloseCalendar, Entity
from app.schemas import ReconciliationSummary
from app.services import ai_client
from app.services.policy import get_active_policy_text


def get_summary(db: Session, period: str = "2024-03") -> ReconciliationSummary:
    matches = db.query(ReconciliationMatch).filter(ReconciliationMatch.period == period).all()
    open_disputes = db.query(Dispute).filter(
        Dispute.period == period, Dispute.status == "open"
    ).all()

    total = len(matches)
    matched = sum(1 for m in matches if m.status == "matched")
    matched_pct = round(matched / total * 100, 1) if total else 0.0
    total_diff = sum(m.difference_gbp or 0 for m in matches if m.status == "unmatched")

    by_type: dict[str, int] = {}
    for m in matches:
        key = m.match_type or "unknown"
        by_type[key] = by_type.get(key, 0) + 1

    today = date.today()
    sla_breached = sum(1 for d in open_disputes if d.sla_deadline and d.sla_deadline < today)

    cal = db.query(CloseCalendar).filter(CloseCalendar.period == period).all()
    confirmed = sum(1 for c in cal if c.status in ("confirmed", "closed"))
    pending = sum(1 for c in cal if c.status in ("open", "submitted"))

    return ReconciliationSummary(
        period=period,
        total_pairs=total,
        matched_pairs=matched,
        unmatched_pairs=total - matched,
        matched_pct=matched_pct,
        total_difference_gbp=total_diff,
        open_disputes=len(open_disputes),
        sla_breached=sla_breached,
        entities_confirmed=confirmed,
        entities_pending=pending,
        by_match_type=by_type,
    )


def get_close_summary(db: Session, period: str = "2024-03") -> str:
    summary = get_summary(db, period)
    entities = {e.id: e.name for e in db.query(Entity).all()}

    open_disputes = db.query(Dispute).filter(
        Dispute.period == period, Dispute.status == "open"
    ).all()

    stats = {
        "period": period,
        "total_ic_pairs": summary.total_pairs,
        "matched_pairs": summary.matched_pairs,
        "matched_pct": f"{summary.matched_pct}%",
        "total_unmatched_exposure_gbp": f"£{summary.total_difference_gbp:,.0f}",
        "open_disputes": summary.open_disputes,
        "sla_breached": summary.sla_breached,
        "entities_confirmed": summary.entities_confirmed,
        "entities_pending": summary.entities_pending,
    }

    dispute_list = [
        {
            "pair": f"{entities.get(d.entity_a_id, d.entity_a_id)} ↔ {entities.get(d.entity_b_id, d.entity_b_id)}",
            "type": d.dispute_type,
            "amount": f"£{d.amount_gbp:,.0f}" if d.amount_gbp else "N/A",
            "sla": str(d.sla_deadline),
            "owner": entities.get(d.owning_entity_id, d.owning_entity_id),
        }
        for d in open_disputes
    ]

    try:
        policy_text = get_active_policy_text(db)
        return ai_client.generate_close_summary(stats, dispute_list, period, policy_text=policy_text)
    except Exception:
        return (
            f"Period {period} IC reconciliation: {summary.matched_pairs}/{summary.total_pairs} pairs matched "
            f"({summary.matched_pct}%). {summary.open_disputes} open disputes with total exposure "
            f"£{summary.total_difference_gbp:,.0f}. {summary.sla_breached} SLA breach(es)."
        )
