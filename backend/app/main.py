from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import data, reconciliation, disputes, insights, query, audit, policy

app = FastAPI(
    title="IC Resolve",
    description="AI-Powered Intercompany Reconciliation Orchestrator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
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
