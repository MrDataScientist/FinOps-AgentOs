"""Fail-closed policy routing: no LLM decides its own privileges."""

from app.config import Settings
from app.models import DataClassification, InferenceTask, RouteDecision, TaskKind


class PolicyDenied(Exception):
    """There is no permitted and affordable route for this task."""


def choose_route(task: InferenceTask, settings: Settings) -> RouteDecision:
    if task.task_kind is TaskKind.DETERMINISTIC:
        return RouteDecision(
            route="none", model=None, reason="Use the application-owned deterministic engine",
            estimated_cost_usd=0,
        )

    if task.classification is not DataClassification.PUBLIC:
        candidates = ["local"]
    elif task.task_kind is TaskKind.COMPLEX_ANALYSIS:
        candidates = ["azure"]
    else:
        candidates = ["local", "azure"]

    for route in candidates:
        if route == "local" and settings.enable_local_routing:
            cost = settings.local_estimated_usd
            model = settings.ollama_model
        elif route == "azure" and settings.enable_azure_routing:
            cost = settings.azure_estimated_usd
            model = settings.azure_deployment or "azure-deployment-unconfigured"
        else:
            continue
        if cost <= task.max_estimated_cost_usd:
            return RouteDecision(
                route=route,
                model=model,
                reason=f"Allowed by static {task.classification.value}/{task.task_kind.value} policy",
                estimated_cost_usd=cost,
                executable=settings.enable_live_execution,
            )
    raise PolicyDenied("No approved route meets the classification, capability and budget rules")
