# IC Resolve — AI-Powered Intercompany Reconciliation Orchestrator

## Quick Start

### 1. Install Python (required for backend)
Download Python 3.11+ from https://www.python.org/downloads/windows/
- Check **"Add Python to PATH"** during install
- Verify: `python --version`

### 2. Backend setup
```powershell
cd ic-resolve\backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
copy .env.example .env
# Edit .env and set: ANTHROPIC_API_KEY=sk-ant-...

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup
```powershell
cd ic-resolve\frontend
npm install   # already done
npm run dev
```

Open http://localhost:5173

---

## First Run
1. Click **Seed Data** — loads 6 Nexora entities, 16 journal entries, FX rates, close calendar
2. Click **Run with AI** — normalises aliases, applies FX, runs matching, generates AI dispute descriptions
3. Explore the 4 modules:

| Module | What it shows |
|--------|--------------|
| Dashboard | KPI cards, match status pie, unmatched exposure bar chart |
| Recon Workbench | All 8 IC pairs, AI reasoning, tolerance config |
| Dispute Workbench | 4 disputes, AI-drafted descriptions, SLA tracking |
| AI Query | Natural language queries about reconciliation state |
| Audit Trail | Every AI decision logged with reasoning |

---

## Mock Data — Nexora Group IC Pairs

| Pair | Transaction | Expected Result |
|------|-------------|----------------|
| E001 ↔ E002 | Management Fee | ✅ Matched (diff < £1) |
| E001 ↔ E003 | IT Services | ❌ FX Difference (£3,110) |
| E001 ↔ E004 | IC Loan | ❌ Missing Posting (E004 silent) |
| E002 ↔ E003 | Shared Services | ❌ Amount Difference (£37,482) |
| E001 ↔ E006 | Royalties | ✅ Matched (diff £20) |
| E002 ↔ E004 | Commission | ✅ Matched (diff < £1) |
| E003 ↔ E005 | Distribution Fee | ❌ Timing Difference (E005 posts in Apr) |
| E001 ↔ E005 | Brand Licence | ✅ Matched (diff £0.36) |

---

## API Reference
Interactive docs at http://localhost:8000/docs (Swagger UI)

Key endpoints:
- `POST /api/data/seed` — load mock data
- `POST /api/reconciliation/run-all?use_ai=true` — full pipeline
- `POST /api/reconciliation/normalise` — step 1: alias resolution + FX
- `POST /api/reconciliation/match` — step 2: matching with tolerance
- `POST /api/disputes/generate?use_ai=true` — step 3: dispute drafting
- `GET /api/reconciliation/summary` — dashboard stats
- `GET /api/reconciliation/pairs` — all IC pairs with match status
- `GET /api/disputes` — dispute workbench data
- `GET /api/audit` — full audit trail
- `POST /api/query` — natural language query `{ "query": "...", "period": "2024-03" }`

---

## Tolerance Configuration
Default: ±£1,000 OR ±0.1% (whichever allows the match).
Override per entity pair via the Recon Workbench settings panel, or:
```
POST /api/data/tolerance-configs
{ "entity_a_id": "E001", "entity_b_id": "E003", "absolute_threshold_gbp": 5000, "percentage_threshold": 0.02 }
```

## Architecture
```
ic-resolve/
├── backend/          FastAPI + SQLAlchemy + SQLite
│   └── app/
│       ├── models.py         SQLAlchemy ORM
│       ├── schemas.py        Pydantic v2 schemas
│       ├── seed_data.py      Mock Nexora Group data
│       └── services/
│           ├── normalisation.py   Alias resolution + FX
│           ├── matching.py        Tolerance-based matching
│           ├── disputes.py        Dispute classification + AI drafting
│           ├── insights.py        Summary + close pack
│           ├── orchestrator.py    Full pipeline runner
│           └── ai_client.py       Claude API (prompt caching)
└── frontend/         React 18 + TypeScript + Vite + Tailwind + Recharts
    └── src/
        ├── components/Dashboard.tsx
        ├── components/ReconciliationWorkbench.tsx
        ├── components/DisputeWorkbench.tsx
        ├── components/QueryInterface.tsx
        └── components/AuditTrail.tsx
```
