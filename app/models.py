"""Strict public contracts; prompts are never included in decision responses."""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TaskKind(StrEnum):
    DETERMINISTIC = "deterministic"
    EXPLANATION = "explanation"
    COMPLEX_ANALYSIS = "complex_analysis"


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"


class InferenceTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_kind: TaskKind
    classification: DataClassification
    prompt: str = Field(min_length=1, max_length=12000)
    max_output_tokens: int = Field(default=256, ge=32, le=1024)
    max_estimated_cost_usd: Decimal = Field(default=Decimal("0.10"), ge=0, le=100)


class RouteDecision(BaseModel):
    route: str
    model: str | None
    reason: str
    estimated_cost_usd: Decimal
    cost_basis: str = "illustrative_per_request_not_billed"
    executable: bool = False


class InferenceResponse(BaseModel):
    route: str
    model: str
    output: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: Decimal
    cost_basis: str = "illustrative_per_request_not_billed"
    quality_validated: bool = False
