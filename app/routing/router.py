"""Stable routing interface; replace heuristic selection only after evaluations exist."""

from app.config import Settings
from app.models import InferenceTask, RouteDecision
from app.policies.engine import choose_route


class PolicyRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def decide(self, task: InferenceTask) -> RouteDecision:
        return choose_route(task, self.settings)
