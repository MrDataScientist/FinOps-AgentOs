"""Read-only adapter for the minimal Stormscope v2 weather-risk response.

Only synthetic example data belongs in this public repository. This module does not
call Stormscope and does not treat generated narrative as authoritative.
"""

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import DataClassification, InferenceTask
from integrations.stormscope.adapter import RiskEvidence, explanation_task


class ResolvedLocation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1, max_length=100)


class HazardEvidence(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: Literal["storm", "rain", "wind", "flood"]
    source: Literal["weather", "official"] = "weather"
    evidence: str = Field(min_length=1, max_length=400)


class StormscopeRiskSnapshot(BaseModel):
    """Subset of /api/v2/agent/weather-risk, not a replacement for its full schema."""

    model_config = ConfigDict(extra="ignore")
    risk_score: int = Field(strict=True, ge=0, le=100)
    risk_level: str = Field(min_length=1, max_length=32)
    location: str | None = Field(default=None, max_length=100)
    resolved_location: ResolvedLocation | None = None
    hazards: list[HazardEvidence] = Field(default_factory=list, max_length=40)


def from_weather_risk_response(
    payload: Mapping[str, Any],
    *,
    classification: DataClassification,
) -> InferenceTask:
    """Produce an eligible explanation task without changing the supplied decision.

    Caller must classify the complete data flow, verify user authorization and
    validate any generated explanation. Fail closed if authoritative evidence
    needed by this simple demonstration is absent.
    """
    snapshot = StormscopeRiskSnapshot.model_validate(payload)
    location = (
        snapshot.resolved_location.name
        if snapshot.resolved_location is not None
        else snapshot.location
    )
    weather_evidence = [
        f"{hazard.kind}: {hazard.evidence}"
        for hazard in snapshot.hazards
        if hazard.source == "weather"
    ]
    if not location or not weather_evidence:
        raise ValueError("Location and weather-derived evidence are required")

    return explanation_task(
        RiskEvidence(
            risk_score=snapshot.risk_score,
            risk_level=snapshot.risk_level,
            evidence=weather_evidence[:8],
            location_name=location,
        ),
        classification=classification,
    )
