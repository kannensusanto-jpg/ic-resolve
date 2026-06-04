import json
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Entity, FXRate, JournalEntry, TrialBalance, AuditEntry
from app.schemas import NormalisationResult


def _build_alias_map(db: Session) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    for entity in db.query(Entity).all():
        alias_map[entity.name.lower()] = entity.id
        for alias in (entity.aliases or []):
            alias_map[alias.lower()] = entity.id
    return alias_map


def _get_fx_rate(db: Session, from_currency: str, period: str) -> Optional[float]:
    row = db.query(FXRate).filter(
        FXRate.from_currency == from_currency,
        FXRate.period == period,
    ).first()
    return row.rate if row else None


def run_normalisation(db: Session, period: str = "2024-03") -> NormalisationResult:
    alias_map = _build_alias_map(db)
    aliases_resolved = 0
    fx_applied = 0
    warnings: list[str] = []

    entries = db.query(JournalEntry).filter(JournalEntry.is_normalised == False).all()  # noqa: E712

    for entry in entries:
        changed = False

        # 1. Resolve counterparty alias → canonical entity ID
        if entry.counterparty_entity_id is None and entry.counterparty_raw:
            resolved = alias_map.get(entry.counterparty_raw.lower())
            if resolved:
                entry.counterparty_entity_id = resolved
                aliases_resolved += 1
                changed = True
            else:
                warnings.append(
                    f"Cannot resolve alias '{entry.counterparty_raw}' on entry {entry.id}"
                )

        # 2. Convert local amount → GBP
        if entry.amount_gbp is None:
            if entry.currency == "GBP":
                entry.amount_gbp = entry.amount_local
                fx_applied += 1
                changed = True
            else:
                rate = _get_fx_rate(db, entry.currency, period)
                if rate:
                    entry.amount_gbp = round(entry.amount_local * rate, 2)
                    fx_applied += 1
                    changed = True
                else:
                    warnings.append(
                        f"No FX rate {entry.currency}/GBP for period {period} — entry {entry.id}"
                    )

        if changed:
            entry.is_normalised = True

    db.commit()

    # Normalise trial balance GBP amounts
    for tb in db.query(TrialBalance).filter(TrialBalance.balance_gbp == None).all():  # noqa: E711
        rate = 1.0 if tb.currency == "GBP" else _get_fx_rate(db, tb.currency, tb.period)
        if rate:
            tb.balance_gbp = round(tb.balance_local * rate, 2)
    db.commit()

    # Detect entity pairs where one side has no entries
    missing_count = 0
    all_entries = db.query(JournalEntry).filter(JournalEntry.period == period).all()
    pairs: set[tuple[str, str]] = set()
    for e in all_entries:
        if e.entity_id and e.counterparty_entity_id:
            pairs.add(tuple(sorted([e.entity_id, e.counterparty_entity_id])))

    for ea, eb in pairs:
        has_a = any(e.entity_id == ea and e.counterparty_entity_id == eb for e in all_entries)
        has_b = any(e.entity_id == eb and e.counterparty_entity_id == ea for e in all_entries)
        if not has_a or not has_b:
            missing_count += 1
            missing_side = ea if not has_a else eb
            warnings.append(
                f"Missing IC entry: {missing_side} has no balance for pair ({ea}↔{eb}) in {period}"
            )

    db.add(AuditEntry(
        action_type="normalisation",
        period=period,
        action_detail=json.dumps({
            "aliases_resolved": aliases_resolved,
            "fx_applied": fx_applied,
            "entries_processed": len(entries),
            "warnings": warnings,
        }),
        ai_reasoning=(
            "Automated normalisation: alias resolution via counterparty master; "
            "FX conversion using period-end closing rates."
        ),
    ))
    db.commit()

    return NormalisationResult(
        aliases_resolved=aliases_resolved,
        fx_applied=fx_applied,
        missing_counterparties=missing_count,
        entries_processed=len(entries),
        warnings=warnings,
    )
