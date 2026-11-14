"""FinOps-AgentOS: controlled inference reference API, intentionally not an agent OS."""

from fastapi import FastAPI

from app.accounting.ledger import UsageLedger
from app.config import Settings
from app.gateway.api import router
from app.governance.api import router as governance_router
from app.governance.audit import AuditStore


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        title="FinOps-AgentOS",
        version="0.1.0",
        description="Local-first, policy-gated model decisions and illustrative accounting",
    )
    app.state.settings = settings or Settings.from_env()
    app.state.ledger = UsageLedger()
    app.include_router(router)
    if app.state.settings.governance_enabled:
        app.state.governance_audit = AuditStore(
            app.state.settings.governance_audit_db,
            app.state.settings.governance_signing_key,
        )
        app.include_router(governance_router)
    return app


app = create_app()
