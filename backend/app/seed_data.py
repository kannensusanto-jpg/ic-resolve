from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models import (
    Entity, FXRate, JournalEntry, TrialBalance,
    CloseCalendar, ToleranceConfig, ReconciliationMatch, Dispute, AuditEntry
)


def seed_database(db: Session) -> dict:
    for model in [AuditEntry, Dispute, ReconciliationMatch, ToleranceConfig,
                  CloseCalendar, TrialBalance, JournalEntry, FXRate, Entity]:
        db.query(model).delete()
    db.commit()

    # ── Entities ─────────────────────────────────────────────────────────────
    entities = [
        Entity(id="E001", name="Nexora Holdings Ltd",
               aliases=["Nexora UK", "Nexora UK Ltd", "NXR Holdings", "Nexora Holdings"],
               functional_currency="GBP", region="United Kingdom",
               ic_agreement_flag=True, owner_email="controller.uk@nexora.com"),
        Entity(id="E002", name="Nexora US Inc",
               aliases=["Nexora USA", "NXR US", "Nexora America", "Nexora Inc"],
               functional_currency="USD", region="United States",
               ic_agreement_flag=True, owner_email="controller.us@nexora.com"),
        Entity(id="E003", name="Nexora Germany GmbH",
               aliases=["Nexora DE", "NexGermany", "Nexora GmbH", "Nexora Deutschland"],
               functional_currency="EUR", region="Germany",
               ic_agreement_flag=True, owner_email="controller.de@nexora.com"),
        Entity(id="E004", name="Nexora Singapore Pte Ltd",
               aliases=["Nexora SG", "NexSingapore", "Nexora Asia"],
               functional_currency="SGD", region="Singapore",
               ic_agreement_flag=True, owner_email="controller.sg@nexora.com"),
        Entity(id="E005", name="Nexora Australia Pty Ltd",
               aliases=["Nexora AU", "NexAustralia", "Nexora ANZ"],
               functional_currency="AUD", region="Australia",
               ic_agreement_flag=True, owner_email="controller.au@nexora.com"),
        Entity(id="E006", name="Nexora France SAS",
               aliases=["Nexora FR", "NexFrance", "Nexora France"],
               functional_currency="EUR", region="France",
               ic_agreement_flag=True, owner_email="controller.fr@nexora.com"),
    ]
    db.add_all(entities)

    # ── FX Rates (March 2024, all to GBP) ────────────────────────────────────
    # USD/GBP=0.785  EUR/GBP=0.858  SGD/GBP=0.582  AUD/GBP=0.513
    fx_rates = [
        FXRate(from_currency="GBP", to_currency="GBP", rate=1.0000,
               effective_date=date(2024, 3, 31), period="2024-03"),
        FXRate(from_currency="USD", to_currency="GBP", rate=0.7850,
               effective_date=date(2024, 3, 31), period="2024-03"),
        FXRate(from_currency="EUR", to_currency="GBP", rate=0.8580,
               effective_date=date(2024, 3, 31), period="2024-03"),
        FXRate(from_currency="SGD", to_currency="GBP", rate=0.5820,
               effective_date=date(2024, 3, 31), period="2024-03"),
        FXRate(from_currency="AUD", to_currency="GBP", rate=0.5130,
               effective_date=date(2024, 3, 31), period="2024-03"),
    ]
    db.add_all(fx_rates)

    # ── Journal Entries (pre-normalisation: counterparty_entity_id=None) ─────
    #
    # Pair 1  E001 ↔ E002  Management Fee        → MATCHED   (diff ~£0)
    # Pair 2  E001 ↔ E003  IT Services           → FX BREACH (diff £3,110 > £1k)
    # Pair 3  E001 ↔ E004  IC Loan               → MISSING POSTING (E004 silent)
    # Pair 4  E002 ↔ E003  Shared Services       → AMOUNT DIFFERENCE (diff £37k)
    # Pair 5  E001 ↔ E006  Royalties             → MATCHED   (diff £20)
    # Pair 6  E002 ↔ E004  Commission            → MATCHED   (diff ~£0)
    # Pair 7  E003 ↔ E005  Distribution Fee      → TIMING DIFFERENCE (E005 in Apr)
    # Pair 8  E001 ↔ E005  Brand Licence         → MATCHED   (diff £0.36)
    journal_entries = [
        # ── Pair 1 ──────────────────────────────────────────────────────────
        JournalEntry(id="JE-E001-E002-001", entity_id="E001",
                     counterparty_raw="Nexora America", account_code="1500",
                     account_name="IC Receivable – Management Fees",
                     amount_local=500_000.0, currency="GBP",
                     period="2024-03", posting_date=date(2024, 3, 15),
                     description="Management fee receivable from Nexora America — Q1 2024",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E002-E001-001", entity_id="E002",
                     counterparty_raw="NXR Holdings", account_code="2500",
                     account_name="IC Payable – Management Fees",
                     amount_local=636_943.0, currency="USD",
                     # 636,943 × 0.785 = £499,999.96  → difference < £1
                     period="2024-03", posting_date=date(2024, 3, 15),
                     description="Management fee payable to NXR Holdings — Q1 2024",
                     journal_type="IC_PAYABLE"),

        # ── Pair 2 ──────────────────────────────────────────────────────────
        JournalEntry(id="JE-E001-E003-001", entity_id="E001",
                     counterparty_raw="Nexora GmbH", account_code="1501",
                     account_name="IC Receivable – IT Services",
                     amount_local=250_000.0, currency="GBP",
                     period="2024-03", posting_date=date(2024, 3, 22),
                     description="IT infrastructure services Q1 2024 — receivable from Nexora GmbH",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E003-E001-001", entity_id="E003",
                     counterparty_raw="Nexora UK", account_code="2501",
                     account_name="IC Payable – IT Services",
                     amount_local=295_000.0, currency="EUR",
                     # 295,000 × 0.858 = £253,110  → diff vs E001 = £3,110 (breach)
                     period="2024-03", posting_date=date(2024, 3, 20),
                     description="IT services payable to Nexora UK — Q1 2024 (E003 used stale rate)",
                     journal_type="IC_PAYABLE"),

        # ── Pair 3 (E004 has NO matching entry) ─────────────────────────────
        JournalEntry(id="JE-E001-E004-001", entity_id="E001",
                     counterparty_raw="Nexora Asia", account_code="1600",
                     account_name="IC Loan Receivable",
                     amount_local=1_200_000.0, currency="GBP",
                     period="2024-03", posting_date=date(2024, 3, 1),
                     description="Intercompany loan to Nexora Asia — outstanding balance Mar 2024",
                     journal_type="IC_RECEIVABLE"),

        # ── Pair 4 ──────────────────────────────────────────────────────────
        JournalEntry(id="JE-E002-E003-001", entity_id="E002",
                     counterparty_raw="NexGermany", account_code="1502",
                     account_name="IC Receivable – Shared Services",
                     amount_local=180_000.0, currency="USD",
                     # 180,000 × 0.785 = £141,300
                     period="2024-03", posting_date=date(2024, 3, 28),
                     description="Shared services fee receivable from NexGermany — Q1 2024",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E003-E002-001", entity_id="E003",
                     counterparty_raw="Nexora Inc", account_code="2502",
                     account_name="IC Payable – Shared Services",
                     amount_local=121_000.0, currency="EUR",
                     # 121,000 × 0.858 = £103,818  → diff = £37,482 (amount diff)
                     period="2024-03", posting_date=date(2024, 3, 25),
                     description="Shared services payable to Nexora Inc — Q1 2024 (based on E003 usage report)",
                     journal_type="IC_PAYABLE"),

        # ── Pair 5 ──────────────────────────────────────────────────────────
        JournalEntry(id="JE-E001-E006-001", entity_id="E001",
                     counterparty_raw="NexFrance", account_code="1503",
                     account_name="IC Receivable – Royalties",
                     amount_local=75_000.0, currency="GBP",
                     period="2024-03", posting_date=date(2024, 3, 31),
                     description="Brand royalty receivable from NexFrance — Q1 2024",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E006-E001-001", entity_id="E006",
                     counterparty_raw="Nexora Holdings", account_code="2503",
                     account_name="IC Payable – Royalties",
                     amount_local=87_413.0, currency="EUR",
                     # 87,413 × 0.858 = £74,980  → diff = £20 (within £1k)
                     period="2024-03", posting_date=date(2024, 3, 31),
                     description="Brand royalty payable to Nexora Holdings — Q1 2024",
                     journal_type="IC_PAYABLE"),

        # ── Pair 6 ──────────────────────────────────────────────────────────
        JournalEntry(id="JE-E002-E004-001", entity_id="E002",
                     counterparty_raw="NexSingapore", account_code="1504",
                     account_name="IC Receivable – Commission",
                     amount_local=95_000.0, currency="USD",
                     # 95,000 × 0.785 = £74,575
                     period="2024-03", posting_date=date(2024, 3, 29),
                     description="Sales commission receivable from NexSingapore — Q1 2024",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E004-E002-001", entity_id="E004",
                     counterparty_raw="Nexora USA", account_code="2504",
                     account_name="IC Payable – Commission",
                     amount_local=128_136.0, currency="SGD",
                     # 128,136 × 0.582 = £74,575.15  → diff < £1
                     period="2024-03", posting_date=date(2024, 3, 29),
                     description="Sales commission payable to Nexora USA — Q1 2024",
                     journal_type="IC_PAYABLE"),

        # ── Pair 7 (E005 posts in April → TIMING) ───────────────────────────
        JournalEntry(id="JE-E003-E005-001", entity_id="E003",
                     counterparty_raw="NexAustralia", account_code="1505",
                     account_name="IC Receivable – Distribution Fees",
                     amount_local=150_000.0, currency="EUR",
                     # 150,000 × 0.858 = £128,700
                     period="2024-03", posting_date=date(2024, 3, 28),
                     description="Distribution fee receivable from NexAustralia — March 2024",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E005-E003-001", entity_id="E005",
                     counterparty_raw="Nexora DE", account_code="2505",
                     account_name="IC Payable – Distribution Fees",
                     amount_local=250_878.0, currency="AUD",
                     # 250,878 × 0.513 = £128,700  — same amount but wrong period
                     period="2024-04", posting_date=date(2024, 4, 3),
                     description="Distribution fee payable to Nexora DE — March 2024 (accrual reposted Apr)",
                     journal_type="IC_PAYABLE"),

        # ── Pair 8 ──────────────────────────────────────────────────────────
        JournalEntry(id="JE-E001-E005-001", entity_id="E001",
                     counterparty_raw="Nexora ANZ", account_code="1506",
                     account_name="IC Receivable – Brand Licence",
                     amount_local=45_000.0, currency="GBP",
                     period="2024-03", posting_date=date(2024, 3, 31),
                     description="Annual brand licence receivable from Nexora ANZ — Q1 2024",
                     journal_type="IC_RECEIVABLE"),
        JournalEntry(id="JE-E005-E001-001", entity_id="E005",
                     counterparty_raw="Nexora UK", account_code="2506",
                     account_name="IC Payable – Brand Licence",
                     amount_local=87_720.0, currency="AUD",
                     # 87,720 × 0.513 = £45,000.36  → diff < £1
                     period="2024-03", posting_date=date(2024, 3, 31),
                     description="Brand licence payable to Nexora UK — Q1 2024",
                     journal_type="IC_PAYABLE"),
    ]
    db.add_all(journal_entries)

    # ── Trial Balances ────────────────────────────────────────────────────────
    trial_balances = [
        # E001
        TrialBalance(entity_id="E001", account_code="1500", account_name="IC Rec – Mgmt Fees",
                     counterparty_entity_id="E002", balance_local=500_000, currency="GBP", balance_gbp=500_000, period="2024-03"),
        TrialBalance(entity_id="E001", account_code="1501", account_name="IC Rec – IT Services",
                     counterparty_entity_id="E003", balance_local=250_000, currency="GBP", balance_gbp=250_000, period="2024-03"),
        TrialBalance(entity_id="E001", account_code="1600", account_name="IC Loan Receivable",
                     counterparty_entity_id="E004", balance_local=1_200_000, currency="GBP", balance_gbp=1_200_000, period="2024-03"),
        TrialBalance(entity_id="E001", account_code="1503", account_name="IC Rec – Royalties",
                     counterparty_entity_id="E006", balance_local=75_000, currency="GBP", balance_gbp=75_000, period="2024-03"),
        TrialBalance(entity_id="E001", account_code="1506", account_name="IC Rec – Brand Licence",
                     counterparty_entity_id="E005", balance_local=45_000, currency="GBP", balance_gbp=45_000, period="2024-03"),
        # E002
        TrialBalance(entity_id="E002", account_code="2500", account_name="IC Pay – Mgmt Fees",
                     counterparty_entity_id="E001", balance_local=636_943, currency="USD", period="2024-03"),
        TrialBalance(entity_id="E002", account_code="1502", account_name="IC Rec – Shared Svcs",
                     counterparty_entity_id="E003", balance_local=180_000, currency="USD", period="2024-03"),
        TrialBalance(entity_id="E002", account_code="1504", account_name="IC Rec – Commission",
                     counterparty_entity_id="E004", balance_local=95_000, currency="USD", period="2024-03"),
        # E003
        TrialBalance(entity_id="E003", account_code="2501", account_name="IC Pay – IT Services",
                     counterparty_entity_id="E001", balance_local=295_000, currency="EUR", period="2024-03"),
        TrialBalance(entity_id="E003", account_code="2502", account_name="IC Pay – Shared Svcs",
                     counterparty_entity_id="E002", balance_local=121_000, currency="EUR", period="2024-03"),
        TrialBalance(entity_id="E003", account_code="1505", account_name="IC Rec – Distribution",
                     counterparty_entity_id="E005", balance_local=150_000, currency="EUR", period="2024-03"),
        # E004  (no IC loan payable to E001 — missing)
        TrialBalance(entity_id="E004", account_code="2504", account_name="IC Pay – Commission",
                     counterparty_entity_id="E002", balance_local=128_136, currency="SGD", period="2024-03"),
        # E005
        TrialBalance(entity_id="E005", account_code="2506", account_name="IC Pay – Brand Licence",
                     counterparty_entity_id="E001", balance_local=87_720, currency="AUD", period="2024-03"),
        TrialBalance(entity_id="E005", account_code="2505", account_name="IC Pay – Distribution",
                     counterparty_entity_id="E003", balance_local=250_878, currency="AUD", period="2024-04"),
        # E006
        TrialBalance(entity_id="E006", account_code="2503", account_name="IC Pay – Royalties",
                     counterparty_entity_id="E001", balance_local=87_413, currency="EUR", period="2024-03"),
    ]
    db.add_all(trial_balances)

    # ── Close Calendar ────────────────────────────────────────────────────────
    close_calendar = [
        CloseCalendar(entity_id="E001", period="2024-03", close_date=date(2024, 4, 5), status="submitted"),
        CloseCalendar(entity_id="E002", period="2024-03", close_date=date(2024, 4, 7), status="open"),
        CloseCalendar(entity_id="E003", period="2024-03", close_date=date(2024, 4, 5), status="confirmed"),
        CloseCalendar(entity_id="E004", period="2024-03", close_date=date(2024, 4, 8), status="open"),
        CloseCalendar(entity_id="E005", period="2024-03", close_date=date(2024, 4, 6), status="open"),
        CloseCalendar(entity_id="E006", period="2024-03", close_date=date(2024, 4, 5), status="confirmed"),
    ]
    db.add_all(close_calendar)

    # ── Tolerance Configs ─────────────────────────────────────────────────────
    tolerance_configs = [
        ToleranceConfig(entity_a_id="DEFAULT", entity_b_id="DEFAULT",
                        absolute_threshold_gbp=1000.0, percentage_threshold=0.001),
        ToleranceConfig(entity_a_id="E001", entity_b_id="E004",
                        absolute_threshold_gbp=500.0, percentage_threshold=0.0005, period="2024-03"),
    ]
    db.add_all(tolerance_configs)
    db.commit()

    return {
        "entities": len(entities),
        "fx_rates": len(fx_rates),
        "journal_entries": len(journal_entries),
        "trial_balances": len(trial_balances),
        "close_calendar": len(close_calendar),
        "tolerance_configs": len(tolerance_configs),
    }
