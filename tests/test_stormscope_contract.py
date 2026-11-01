"""Contract and privacy boundary checks for the Stormscope reference client."""

import asyncio
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.models import DataClassification
from app.policies.engine import PolicyDenied, choose_route
from integrations.stormscope.contract import from_weather_risk_response
from integrations.stormscope.demo import run_demo

FIXTURE = Path(__file__).resolve().parents[1] / "scenarios/stormscope-risk-synthetic.json"


def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["weather_risk_response"]


def test_preserves_authoritative_risk_decision():
    data = payload()
    before = json.dumps(data, sort_keys=True)
    task = from_weather_risk_response(data, classification=DataClassification.PUBLIC)
    assert "Risk score: 64" in task.prompt
    assert "Risk level: HIGH" in task.prompt
    assert "Synthetic wind gusts" in task.prompt
    assert task.classification is DataClassification.PUBLIC
    assert json.dumps(data, sort_keys=True) == before


def test_internal_data_never_uses_cloud():
    task = from_weather_risk_response(payload(), classification=DataClassification.INTERNAL)
    with pytest.raises(PolicyDenied):
        choose_route(task, Settings(enable_local_routing=False, enable_azure_routing=True))


@pytest.mark.parametrize("field,value", [("risk_score", None), ("risk_score", 999)])
def test_rejects_invalid_or_unavailable_risk(field, value):
    data = payload()
    data[field] = value
    with pytest.raises(ValidationError):
        from_weather_risk_response(data, classification=DataClassification.PUBLIC)


def test_requires_source_weather_evidence():
    data = payload()
    data["hazards"] = [{"kind": "wind", "source": "official", "evidence": "Unverified alert"}]
    with pytest.raises(ValueError, match="evidence"):
        from_weather_risk_response(data, classification=DataClassification.PUBLIC)


def test_demo_routes_synthetic_request_only():
    output = asyncio.run(run_demo(FIXTURE))
    assert output["mode"] == "dry_run_policy_only"
    assert output["agentos_route"] == "local"
    assert output["agentos_executable"] is False
    assert output["risk_score_unchanged"] is True


def test_existing_adapter_defaults_internal():
    from integrations.stormscope.adapter import RiskEvidence, explanation_task

    item = RiskEvidence(
        risk_score=64, risk_level="HIGH", location_name="Munich", evidence=["Wind"],
    )
    assert explanation_task(item).classification is DataClassification.INTERNAL
