from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.evaluation.contracts import cost_per_accepted_task
from app.models import DataClassification, InferenceTask, TaskKind
from app.policies.engine import PolicyDenied, choose_route
from app.workflows.approvals import HumanApprovalRequired, require_approval
from integrations.stormscope.adapter import RiskEvidence, explanation_task


def task(kind=TaskKind.EXPLANATION, classification=DataClassification.INTERNAL):
    return InferenceTask(task_kind=kind, classification=classification, prompt="Synthetic task")


def test_restricted_never_cloud_even_when_enabled():
    with pytest.raises(PolicyDenied):
        choose_route(task(classification=DataClassification.RESTRICTED),
                     Settings(enable_local_routing=False, enable_azure_routing=True))


def test_default_local_estimate_not_claimed_as_real_bill():
    decision = choose_route(task(), Settings())
    assert decision.route == "local"
    assert decision.estimated_cost_usd > 0
    assert "not_billed" in decision.cost_basis


def test_invalid_budget_and_negative_estimates():
    with pytest.raises(ValidationError):
        InferenceTask(task_kind="explanation", classification="public", prompt="hi",
                      max_estimated_cost_usd=Decimal("-0.01"))
    with pytest.raises(ValueError):
        Settings(local_estimated_usd=Decimal("-1"))


def test_cost_per_accepted_task():
    assert cost_per_accepted_task(1.5, 3) == pytest.approx(0.5)
    assert cost_per_accepted_task(1.5, 0) is None
    with pytest.raises(ValueError):
        cost_per_accepted_task(-1, 2)


def test_stormscope_adapter_preserves_risk_fields():
    payload = RiskEvidence(risk_score=64, risk_level="HIGH", location_name="Munich",
                           evidence=["Strong wind recorded", "Rain reported"])
    t = explanation_task(payload)
    assert t.task_kind == TaskKind.EXPLANATION
    assert "Risk score: 64" in t.prompt
    assert "Risk level: HIGH" in t.prompt
    with pytest.raises(ValidationError):
        RiskEvidence(risk_score=101, risk_level="HIGH", location_name="A", evidence=["X"])


def test_approval_gate():
    with pytest.raises(HumanApprovalRequired):
        require_approval(approved_by_human=False)
    require_approval(approved_by_human=True)


def test_sensitive_complex_requires_qualified_model_even_when_local_available():
    with pytest.raises(PolicyDenied, match="quality-qualified"):
        choose_route(
            task(kind=TaskKind.COMPLEX_ANALYSIS, classification=DataClassification.RESTRICTED),
            Settings(enable_local_routing=True),
        )
