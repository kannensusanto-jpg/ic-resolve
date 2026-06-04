from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.database import init_db
from app.routers import data, reconciliation, disputes, insights, query, audit, policy

app = FastAPI(
    title="IC Resolve",
    description="AI-Powered Intercompany Reconciliation Orchestrator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [data.router, reconciliation.router, disputes.router,
               insights.router, query.router, audit.router, policy.router]:
    app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "IC Resolve", "version": "1.0.0"}


# Serve built frontend — must come last so API routes take priority
_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
