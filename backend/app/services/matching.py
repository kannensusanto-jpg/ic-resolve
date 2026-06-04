import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import JournalEntry, ReconciliationMatch, ToleranceConfig, FXRate, AuditEntry
from app.schemas import MatchingResult


def _get_tolerance(db: Session, ea: str, eb: str, period: str) -> tuple[float, float]:
    config = (
        db.query(ToleranceConfig)
        .filter(ToleranceConfig.entity_a_id == ea, ToleranceConfig.entity_b_id == eb)
        .filter((ToleranceConfig.period == period) | (ToleranceConfig.period == None))  # noqa: E711
        .first()
    )
    if not config:
        config = db.query(ToleranceConfig).filter(ToleranceConfig.entity_a_id == "DEFAULT").first()
    return (
        config.absolute_threshold_gbp if config else 1000.0,
        config.percentage_threshold if config else 0.001,
    )


def _net(entries: list) -> float:
    rec = sum(e.amount_gbp or 0 for e in entries if e.journal_type == "IC_RECEIVABLE")
    pay = sum(e.amount_gbp or 0 for e in entries if e.journal_type == "IC_PAYABLE")
    return rec - pay


def _net_local(entries: list) -> dict:
    """Sum local amounts by currency so we can compare pre-FX quantities."""
    totals: dict[str, float] = {}
    for e in entries:
        ccy = e.currency or "UNK"
        sign = 1 if e.journal_type == "IC_RECEIVABLE" else -1
        totals[ccy] = totals.get(ccy, 0) + sign * (e.amount_local or 0)
    return totals


def _official_rate(db: Session, currency: str, period: str) -> float | None:
    row = db.query(FXRate).filter(
        FXRate.from_currency == currency,
        FXRate.period == period,
    ).first()
    return row.rate if row else None


def _fx_analysis(db: Session, entries_a: list, entries_b: list, period: str) -> dict:
    """
    For each non-GBP entry, compare the rate actually used (amount_gbp / amount_local)
    against the official rate in the FX table.

    Returns:
        has_rate_error   – at least one entry used a materially different rate
        net_a_official   – what net_a would be at official rates
        net_b_official   – what net_b would be at official rates
        rate_details     – list of per-entry diagnostics
    """
    RATE_TOLERANCE = 0.005  # 0.5% — differences smaller than this are rounding, not wrong rates

    details = []
    has_rate_error = False
    has_fx_rates = False

    def analyse_entries(entries, side_label):
        nonlocal has_rate_error, has_fx_rates
        for e in entries:
            if not e.currency or e.currency == "GBP":
                continue
            official = _official_rate(db, e.currency, period)
            if official is None:
                continue
            has_fx_rates = True
            if not e.amount_local or e.amount_local == 0:
                continue
            implied = (e.amount_gbp or 0) / e.amount_local
            rate_gap_pct = abs(implied - official) / official if official else 0
            wrong = rate_gap_pct > RATE_TOLERANCE
            if wrong:
                has_rate_error = True
            details.append({
                "side": side_label,
                "entity": e.entity_id,
                "txn_id": e.id,
                "currency": e.currency,
                "amount_local": e.amount_local,
                "amount_reported": e.amount_gbp,
                "implied_rate": round(implied, 6),
                "official_rate": round(official, 6),
                "rate_gap_pct": round(rate_gap_pct * 100, 3),
                "wrong_rate": wrong,
            })
        return entries

    analyse_entries(entries_a, "A")
    analyse_entries(entries_b, "B")

    # Re-compute net balances using official rates
    def net_at_official(entries):
        total = 0.0
        for e in entries:
            official = _official_rate(db, e.currency or "GBP", period) if e.currency != "GBP" else 1.0
            rate = official if official else ((e.amount_gbp or 0) / e.amount_local if e.amount_local else 1.0)
            amount = (e.amount_local or 0) * rate
            total += amount if e.journal_type == "IC_RECEIVABLE" else -amount
        return total

    net_a_official = net_at_official(entries_a) if has_fx_rates else None
    net_b_official = net_at_official(entries_b) if has_fx_rates else None

    return {
        "has_fx_rates": has_fx_rates,
        "has_rate_error": has_rate_error,
        "net_a_official": net_a_official,
        "net_b_official": net_b_official,
        "rate_details": details,
    }


def _classify(
    net_a: float, net_b: float,
    fx: dict,
    abs_thresh: float, pct_thresh: float,
    has_timing: bool, in_period_a: bool, in_period_b: bool,
    period: str,
) -> tuple[str, str, str]:
    """
    Returns (status, match_type, fx_verdict).
    fx_verdict is a plain-English string describing the FX finding (may be empty).
    """
    difference = abs(net_a + net_b)
    max_abs = max(abs(net_a), abs(net_b), 1.0)

    within = difference <= abs_thresh or (difference / max_abs) <= pct_thresh

    if within:
        return "matched", ("exact" if difference < 0.01 else "within_tolerance"), ""

    if has_timing and (not in_period_a or not in_period_b):
        return "unmatched", "timing_difference", ""

    # FX analysis available — decide whether FX explains the gap
    fx_verdict = ""
    if fx["has_fx_rates"] and fx["net_a_official"] is not None and fx["net_b_official"] is not None:
        diff_official = abs(fx["net_a_official"] + fx["net_b_official"])
        official_within = diff_official <= abs_thresh or (diff_official / max_abs) <= pct_thresh

        wrong_entries = [d for d in fx["rate_details"] if d["wrong_rate"]]

        if fx["has_rate_error"] and official_within:
            # Gap disappears at official rates → pure FX issue
            lines = []
            for d in wrong_entries:
                lines.append(
                    f"{d['entity']} used {d['implied_rate']} for {d['currency']} "
                    f"(official: {d['official_rate']}, gap: {d['rate_gap_pct']}%)"
                )
            fx_verdict = (
                f"CONFIRMED FX RATE ERROR: gap of {difference:,.0f} disappears when official "
                f"rates applied (residual: {diff_official:,.0f}). "
                + " | ".join(lines)
            )
            return "unmatched", "fx_difference", fx_verdict

        elif fx["has_rate_error"] and not official_within:
            # FX errors exist but don't explain the full gap → mixed
            lines = [
                f"{d['entity']} {d['currency']} implied {d['implied_rate']} vs official {d['official_rate']} ({d['rate_gap_pct']}%)"
                for d in wrong_entries
            ]
            fx_verdict = (
                f"PARTIAL FX ERROR: rate errors found but gap persists at official rates "
                f"({diff_official:,.0f} residual). " + " | ".join(lines)
            )
            return "unmatched", "amount_difference", fx_verdict

        elif not fx["has_rate_error"] and fx["rate_details"]:
            # Rates all correct — genuine amount difference
            fx_verdict = (
                f"FX RATES VERIFIED CORRECT: all entries used official rates. "
                f"Gap of {difference:,.0f} is a genuine amount difference."
            )
            return "unmatched", "amount_difference", fx_verdict

    # No FX table uploaded — fall back to heuristic
    if difference / max_abs < 0.10:
        return "unmatched", "fx_difference", ""

    return "unmatched", "amount_difference", ""


def _reasoning(
    ea, eb, period, net_a, net_b, diff, match_type,
    abs_t, pct_t, timing, fx_verdict: str, fx: dict,
) -> str:
    base = ""
    if match_type == "exact":
        base = f"Exact match: {ea} {net_a:,.0f} vs {eb} {-net_b:,.0f}. Zero difference."
    elif match_type == "within_tolerance":
        base = (
            f"Within tolerance: difference {diff:,.2f} ≤ threshold {abs_t:,.0f} "
            f"({pct_t * 100:.2f}%). Auto-matched."
        )
    elif match_type == "timing_difference":
        base = (
            f"Timing difference: one entity's entry falls outside period {period}. "
            f"{ea} {net_a:,.0f} | {eb} {-net_b:,.0f}."
        )
    elif match_type == "missing_posting":
        missing = eb if net_a != 0 else ea
        base = f"Missing posting: {missing} has no IC entry for this pair in {period}."
    elif match_type == "fx_difference":
        base = f"FX difference: {ea} {net_a:,.0f} vs {eb} {-net_b:,.0f}. Gap {diff:,.0f}."
    else:
        base = f"Amount difference: {ea} {net_a:,.0f} vs {eb} {-net_b:,.0f}. Gap {diff:,.0f}."

    if fx_verdict:
        base += f" {fx_verdict}"
    elif not fx["has_fx_rates"] and match_type in ("fx_difference", "amount_difference"):
        base += " No FX rate table uploaded — upload FX rates for precise rate-error detection."

    return base


def run_matching(db: Session, period: str = "2024-03") -> MatchingResult:
    entries = db.query(JournalEntry).filter(JournalEntry.is_normalised == True).all()  # noqa: E712

    pairs: set[tuple[str, str]] = set()
    for e in entries:
        if e.entity_id and e.counterparty_entity_id:
            pairs.add(tuple(sorted([e.entity_id, e.counterparty_entity_id])))

    type_counts: dict[str, int] = {}
    matched_count = 0
    unmatched_count = 0

    for ea, eb in pairs:
        match_id = f"{ea}_{eb}_{period}"

        all_a = [e for e in entries if e.entity_id == ea and e.counterparty_entity_id == eb]
        all_b = [e for e in entries if e.entity_id == eb and e.counterparty_entity_id == ea]
        a_period = [e for e in all_a if e.period == period]
        b_period = [e for e in all_b if e.period == period]
        has_timing = any(e.period != period for e in all_a + all_b)

        net_a = _net(a_period) if a_period else _net(all_a)
        net_b = _net(b_period) if b_period else _net(all_b)

        abs_thresh, pct_thresh = _get_tolerance(db, ea, eb, period)

        if not all_a and not all_b:
            status, match_type, fx_verdict = "unmatched", "no_data", ""
            fx = {"has_fx_rates": False, "has_rate_error": False, "rate_details": []}
        elif not all_a:
            status, match_type, fx_verdict = "unmatched", "missing_posting", ""
            net_a = 0.0
            fx = {"has_fx_rates": False, "has_rate_error": False, "rate_details": []}
        elif not all_b and not has_timing:
            status, match_type, fx_verdict = "unmatched", "missing_posting", ""
            net_b = 0.0
            fx = {"has_fx_rates": False, "has_rate_error": False, "rate_details": []}
        else:
            fx = _fx_analysis(db, a_period or all_a, b_period or all_b, period)
            status, match_type, fx_verdict = _classify(
                net_a, net_b, fx, abs_thresh, pct_thresh,
                has_timing, bool(a_period), bool(b_period), period,
            )
            if status == "matched":
                matched_count += 1
            else:
                unmatched_count += 1

        difference_gbp = (
            abs(net_a + net_b)
            if match_type not in ("missing_posting", "no_data")
            else max(abs(net_a), abs(net_b))
        )
        type_counts[match_type] = type_counts.get(match_type, 0) + 1

        reasoning = _reasoning(
            ea, eb, period, net_a, net_b, difference_gbp,
            match_type, abs_thresh, pct_thresh, has_timing, fx_verdict, fx,
        )

        audit_detail = {
            "net_a": round(net_a, 2),
            "net_b": round(net_b, 2),
            "difference": round(difference_gbp, 2),
            "match_type": match_type,
            "tolerance": abs_thresh,
            "fx_rates_available": fx["has_fx_rates"],
            "fx_rate_error_detected": fx.get("has_rate_error", False),
        }
        if fx.get("rate_details"):
            audit_detail["rate_details"] = fx["rate_details"]

        existing = db.get(ReconciliationMatch, match_id)
        if existing:
            existing.amount_a_gbp = net_a
            existing.amount_b_gbp = net_b
            existing.difference_gbp = difference_gbp
            existing.tolerance_threshold_gbp = abs_thresh
            existing.tolerance_pct = pct_thresh
            existing.status = status
            existing.match_type = match_type
            existing.has_timing_difference = has_timing
            existing.ai_reasoning = reasoning
            existing.updated_at = datetime.utcnow()
        else:
            db.add(ReconciliationMatch(
                id=match_id, entity_a_id=ea, entity_b_id=eb, period=period,
                amount_a_gbp=net_a, amount_b_gbp=net_b, difference_gbp=difference_gbp,
                tolerance_threshold_gbp=abs_thresh, tolerance_pct=pct_thresh,
                status=status, match_type=match_type,
                has_timing_difference=has_timing, ai_reasoning=reasoning,
            ))

        db.add(AuditEntry(
            action_type="match_decision",
            entity_a_id=ea, entity_b_id=eb, period=period,
            action_detail=json.dumps(audit_detail),
            ai_reasoning=reasoning,
        ))

    db.commit()
    return MatchingResult(
        pairs_processed=len(pairs),
        matched=matched_count,
        unmatched=unmatched_count,
        by_match_type=type_counts,
    )
