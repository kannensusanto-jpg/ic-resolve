import json
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.models import ReconciliationMatch, Dispute, Entity, CloseCalendar, JournalEntry, AuditEntry
from app.schemas import DisputeResult
from app.services import ai_client
from app.services.policy import get_active_policy_text

DISPUTE_TYPE_MAP = {
    "timing_difference": "timing",
    "fx_difference": "fx",
    "missing_posting": "missing_posting",
    "amount_difference": "amount_difference",
    "no_data": "missing_posting",
}

SLA_BUFFER_DAYS = {
    "timing": 3,
    "fx": 2,
    "missing_posting": 1,
    "amount_difference": 5,
}


def _sla_deadline(db: Session, owning_entity_id: str, period: str, dispute_type: str) -> date:
    cal = db.query(CloseCalendar).filter(
        CloseCalendar.entity_id == owning_entity_id,
        CloseCalendar.period == period,
    ).first()
    base = cal.close_date if cal else date(2024, 4, 10)
    return base - timedelta(days=SLA_BUFFER_DAYS.get(dispute_type, 3))


def run_disputes(db: Session, period: str = "2024-03", use_ai: bool = True) -> DisputeResult:
    policy_text = get_active_policy_text(db) if use_ai else None
    unmatched = db.query(ReconciliationMatch).filter(
        ReconciliationMatch.period == period,
        ReconciliationMatch.status == "unmatched",
    ).all()

    created = updated = ai_generated = 0

    for match in unmatched:
        dispute_id = f"DISP-{match.entity_a_id}-{match.entity_b_id}-{period}"
        dispute_type = DISPUTE_TYPE_MAP.get(match.match_type, "amount_difference")

        # Seller/creditor entity owns the dispute — entity_a by convention (alphabetically first)
        owning_entity_id = match.entity_a_id
        if match.match_type == "missing_posting":
            # The entity with no entry is responsible for posting
            owning_entity_id = match.entity_b_id if match.amount_a_gbp else match.entity_a_id

        sla_deadline = _sla_deadline(db, owning_entity_id, period, dispute_type)

        entity_a = db.get(Entity, match.entity_a_id)
        entity_b = db.get(Entity, match.entity_b_id)
        name_a = entity_a.name if entity_a else match.entity_a_id
        name_b = entity_b.name if entity_b else match.entity_b_id

        entries_a = db.query(JournalEntry).filter(
            JournalEntry.entity_id == match.entity_a_id,
            JournalEntry.counterparty_entity_id == match.entity_b_id,
        ).all()
        entries_b = db.query(JournalEntry).filter(
            JournalEntry.entity_id == match.entity_b_id,
            JournalEntry.counterparty_entity_id == match.entity_a_id,
        ).all()

        journal_ctx = f"{name_a}: " + (
            "; ".join(
                f"{e.description} [{e.currency} {e.amount_local:,.0f}, {e.posting_date}]"
                for e in entries_a
            ) or "NO ENTRIES"
        )
        journal_ctx += f" | {name_b}: " + (
            "; ".join(
                f"{e.description} [{e.currency} {e.amount_local:,.0f}, {e.posting_date}]"
                for e in entries_b
            ) or "NO ENTRIES"
        )

        ai_description = None
        if use_ai:
            try:
                desc, _ = ai_client.draft_dispute_description(
                    entity_a=name_a,
                    entity_b=name_b,
                    dispute_type=dispute_type,
                    amount_gbp=match.difference_gbp or 0,
                    amount_a_gbp=match.amount_a_gbp or 0,
                    amount_b_gbp=-(match.amount_b_gbp or 0),
                    period=period,
                    journal_details=journal_ctx,
                    policy_text=policy_text,
                )
                ai_description = desc
                ai_generated += 1
            except Exception:
                pass

        if ai_description is None:
            ai_description = (
                f"{dispute_type.replace('_', ' ').title()} dispute: "
                f"difference of £{(match.difference_gbp or 0):,.0f} between {name_a} and {name_b} "
                f"for period {period}. Please review journal entries."
            )

        existing = db.get(Dispute, dispute_id)
        if existing:
            if existing.status not in ("resolved", "escalated"):
                existing.dispute_type = dispute_type
                existing.owning_entity_id = owning_entity_id
                existing.amount_gbp = match.difference_gbp
                existing.sla_deadline = sla_deadline
                existing.ai_description = ai_description
                existing.updated_at = datetime.utcnow()
                updated += 1
        else:
            db.add(Dispute(
                id=dispute_id,
                match_id=match.id,
                entity_a_id=match.entity_a_id,
                entity_b_id=match.entity_b_id,
                period=period,
                dispute_type=dispute_type,
                owning_entity_id=owning_entity_id,
                amount_gbp=match.difference_gbp,
                sla_deadline=sla_deadline,
                ai_description=ai_description,
                status="open",
            ))
            created += 1

        db.add(AuditEntry(
            action_type="dispute_created",
            entity_a_id=match.entity_a_id,
            entity_b_id=match.entity_b_id,
            period=period,
            action_detail=json.dumps({
                "dispute_id": dispute_id,
                "dispute_type": dispute_type,
                "owning_entity": owning_entity_id,
                "amount_gbp": match.difference_gbp,
                "sla_deadline": str(sla_deadline),
                "ai_used": use_ai and ai_generated > 0,
            }),
            ai_model="claude-sonnet-4-6" if use_ai else None,
            ai_reasoning=ai_description,
        ))

    db.commit()
    return DisputeResult(
        disputes_created=created,
        disputes_updated=updated,
        ai_descriptions_generated=ai_generated,
    )
