"""FinOps-AgentOS: controlled inference reference API, intentionally not an agent OS."""

from fastapi import FastAPI

from app.accounting.ledger import UsageLedger
from app.config import Settings
from app.gateway.api import router


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        title="FinOps-AgentOS",
        version="0.1.0",
        description="Local-first, policy-gated model decisions and illustrative accounting",
    )
    app.state.settings = settings or Settings.from_env()
    app.state.ledger = UsageLedger()
    app.include_router(router)
    return app


app = create_app()
