"""Evaluation results are evidence artifacts, not produced from model confidence alone."""

from pydantic import BaseModel, Field


class HumanEvaluation(BaseModel):
    scenario_id: str
    evaluator: str
    accepted: bool
    groundedness_1_to_5: int = Field(ge=1, le=5)
    evidence_reference: str


def cost_per_accepted_task(total_cost_usd: float, accepted_count: int) -> float | None:
    if accepted_count <= 0:
        return None
    if total_cost_usd < 0:
        raise ValueError("Total cost cannot be negative")
    return total_cost_usd / accepted_count
