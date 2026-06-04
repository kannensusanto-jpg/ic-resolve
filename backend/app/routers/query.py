import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ReconciliationMatch, Dispute, Entity, AuditEntry
from app.schemas import QueryRequest, QueryResponse
from app.services import ai_client
from app.services.policy import get_active_policy_text

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def natural_language_query(req: QueryRequest, db: Session = Depends(get_db)):
    entities = {e.id: e.name for e in db.query(Entity).all()}
    matches = db.query(ReconciliationMatch).filter(ReconciliationMatch.period == req.period).all()
    disputes = db.query(Dispute).filter(Dispute.period == req.period).all()

    lines = [f"=== IC RECONCILIATION — PERIOD {req.period} ===\n"]

    lines.append("RECONCILIATION PAIRS:")
    for m in matches:
        ea = entities.get(m.entity_a_id, m.entity_a_id)
        eb = entities.get(m.entity_b_id, m.entity_b_id)
        lines.append(
            f"  • {ea} ↔ {eb}: {m.status.upper()} | {m.match_type} | "
            f"Diff £{(m.difference_gbp or 0):,.0f} | "
            f"{ea} £{(m.amount_a_gbp or 0):,.0f} | {eb} £{abs(m.amount_b_gbp or 0):,.0f}"
        )

    lines.append("\nDISPUTES:")
    for d in disputes:
        ea = entities.get(d.entity_a_id, d.entity_a_id)
        eb = entities.get(d.entity_b_id, d.entity_b_id)
        owner = entities.get(d.owning_entity_id, d.owning_entity_id)
        lines.append(
            f"  • {ea} ↔ {eb}: {d.dispute_type} | £{(d.amount_gbp or 0):,.0f} | "
            f"Owner: {owner} | SLA: {d.sla_deadline} | Status: {d.status}"
        )

    context = "\n".join(lines)

    try:
        policy_text = get_active_policy_text(db)
        answer, model = ai_client.answer_query(req.query, context, req.period, policy_text=policy_text)
    except Exception as e:
        answer = f"Query failed: {e}. Please verify ANTHROPIC_API_KEY is set."
        model = "none"

    db.add(AuditEntry(
        action_type="query",
        period=req.period,
        action_detail=json.dumps({"query": req.query}),
        ai_model=model,
        ai_reasoning=answer[:500],
    ))
    db.commit()

    return QueryResponse(query=req.query, answer=answer, ai_model=model, period=req.period)
