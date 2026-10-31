"""HTTP boundary. No external inference occurs unless explicitly enabled."""

import secrets
from time import perf_counter

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.accounting.ledger import UsageLedger
from app.config import Settings
from app.models import InferenceResponse, InferenceTask, RouteDecision
from app.policies.engine import PolicyDenied
from app.providers.client import ProviderError, call_azure, call_ollama
from app.routing.router import PolicyRouter

router = APIRouter()
REQUESTS = Counter("agentos_requests_total", "Request outcomes", ["route", "status"])
LATENCY = Histogram("agentos_inference_seconds", "Execution latency", ["route"])
TOKENS = Counter("agentos_tokens_total", "Reported provider tokens", ["route", "direction"])
COST = Counter("agentos_illustrative_cost_usd_total", "Illustrative cost; NOT billed", ["route"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def auth(
    settings: Settings = Depends(get_settings),
    x_control_plane_key: str | None = Header(default=None),
) -> None:
    # Configured API key protects endpoints; without one dry-run is loopback-only.
    if settings.control_plane_api_key and not secrets.compare_digest(
        x_control_plane_key or "", settings.control_plane_api_key
    ):
        raise HTTPException(status_code=401, detail="Invalid control-plane key")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/v1/route/plan", response_model=RouteDecision, dependencies=[Depends(auth)])
def plan(task: InferenceTask, settings: Settings = Depends(get_settings)) -> RouteDecision:
    try:
        return PolicyRouter(settings).decide(task)
    except PolicyDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/api/v1/infer", response_model=InferenceResponse, dependencies=[Depends(auth)])
async def infer(
    task: InferenceTask,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> InferenceResponse:
    if not settings.enable_live_execution:
        raise HTTPException(status_code=403, detail="Live execution disabled")
    try:
        decision = PolicyRouter(settings).decide(task)
    except PolicyDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if decision.route == "none":
        raise HTTPException(status_code=422, detail="Use the deterministic application service")

    start = perf_counter()
    try:
        if decision.route == "local":
            result = await call_ollama(task, settings)
        elif decision.route == "azure":
            result = await call_azure(task, settings)
        else:
            raise HTTPException(status_code=403, detail="Unsupported route")
    except ProviderError as exc:
        REQUESTS.labels(route=decision.route, status="provider_error").inc()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        LATENCY.labels(route=decision.route).observe(perf_counter() - start)

    for direction, count in (("input", result.input_tokens), ("output", result.output_tokens)):
        if isinstance(count, int) and count >= 0:
            TOKENS.labels(route=decision.route, direction=direction).inc(count)
    COST.labels(route=decision.route).inc(float(decision.estimated_cost_usd))
    REQUESTS.labels(route=decision.route, status="completed").inc()
    ledger: UsageLedger = request.app.state.ledger
    await ledger.record(decision.estimated_cost_usd)
    return InferenceResponse(
        route=decision.route,
        model=decision.model or "unknown",
        output=result.text,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        estimated_cost_usd=decision.estimated_cost_usd,
    )


@router.get("/api/v1/usage", dependencies=[Depends(auth)])
async def usage(request: Request):
    ledger: UsageLedger = request.app.state.ledger
    return await ledger.summary()


@router.get("/metrics", dependencies=[Depends(auth)])
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
