"""
Fetch period-end FX rates from api.frankfurter.app (ECB data, no key required).
Rates are stored as X → GBP (how many GBP per 1 unit of X).
"""
import calendar
import httpx
from datetime import date
from sqlalchemy.orm import Session
from app.models import FXRate

CURRENCIES = ["USD", "EUR", "SGD", "AUD", "JPY", "CAD", "CHF", "HKD", "NOK", "SEK", "DKK"]


def _period_end_date(period: str) -> str:
    year, month = map(int, period.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-{last_day:02d}"


def fetch_and_store(db: Session, period: str) -> dict:
    """
    Fetch ECB rates for the last day of the period and persist to fx_rates.
    Falls back to the latest available date if the period end is a weekend/holiday.
    """
    end_date = _period_end_date(period)
    symbols = ",".join(CURRENCIES)

    data = None
    source_url = None
    for url in [
        f"https://api.frankfurter.app/{end_date}?from=GBP&to={symbols}",
        f"https://api.frankfurter.app/latest?from=GBP&to={symbols}",
    ]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                source_url = url
                break
        except Exception:
            continue

    if not data or "rates" not in data:
        return {"ok": False, "error": "Frankfurter API unreachable", "fetched": 0}

    rates_raw = data["rates"]            # {currency: how_many_per_1_GBP}
    actual_date = data.get("date", end_date)
    effective = date.fromisoformat(actual_date)

    # Clear existing for this period
    db.query(FXRate).filter(FXRate.period == period).delete()

    stored = []
    # GBP/GBP = 1
    db.add(FXRate(from_currency="GBP", to_currency="GBP",
                  rate=1.0, effective_date=effective, period=period))
    stored.append({"pair": "GBP/GBP", "rate": 1.0})

    for currency, gbp_units in rates_raw.items():
        # gbp_units = how many {currency} buys 1 GBP  →  1 {currency} = 1/gbp_units GBP
        gbp_per_unit = round(1.0 / gbp_units, 6)
        db.add(FXRate(from_currency=currency, to_currency="GBP",
                      rate=gbp_per_unit, effective_date=effective, period=period))
        stored.append({"pair": f"{currency}/GBP", "rate": gbp_per_unit})

    db.commit()
    return {
        "ok": True,
        "period": period,
        "source_date": actual_date,
        "source_url": source_url,
        "fetched": len(stored),
        "rates": {r["pair"]: r["rate"] for r in stored},
    }
