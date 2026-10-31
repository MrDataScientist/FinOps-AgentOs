from decimal import Decimal

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.client import ProviderResult


PUBLIC = {"task_kind": "explanation", "classification": "public", "prompt": "Weather?"}


def test_health_and_dry_run_plan():
    with TestClient(create_app(Settings())) as client:
        assert client.get("/health").json() == {"status": "ok"}
        plan = client.post("/api/v1/route/plan", json=PUBLIC)
        assert plan.status_code == 200
        assert plan.json()["route"] == "local"
        assert plan.json()["executable"] is False
        assert plan.json()["cost_basis"] == "illustrative_per_request_not_billed"
        assert client.post("/api/v1/infer", json=PUBLIC).status_code == 403
        assert client.get("/api/v1/usage").json()["completed_requests"] == 0


def test_sensitive_routes_local_only():
    config = Settings(enable_local_routing=False, enable_azure_routing=True)
    with TestClient(create_app(config)) as c:
        answer = c.post("/api/v1/route/plan", json={**PUBLIC, "classification": "restricted"})
        assert answer.status_code == 403
        assert "No approved route" in answer.json()["detail"]


def test_complex_public_requires_configured_cloud_route():
    with TestClient(create_app(Settings())) as c:
        result = c.post("/api/v1/route/plan", json={**PUBLIC, "task_kind": "complex_analysis"})
        assert result.status_code == 403
    with TestClient(create_app(Settings(enable_azure_routing=True))) as c:
        plan = c.post("/api/v1/route/plan", json={**PUBLIC, "task_kind": "complex_analysis"})
        assert plan.status_code == 200
        assert plan.json()["route"] == "azure"
        assert plan.json()["executable"] is False


def test_budget_gates_are_enforced():
    with TestClient(create_app(Settings(local_estimated_usd=Decimal("0.50")))) as c:
        assert c.post("/api/v1/route/plan", json=PUBLIC).status_code == 403


def test_deterministic_request_does_not_infer():
    with TestClient(create_app(Settings())) as c:
        d = c.post("/api/v1/route/plan", json={**PUBLIC, "task_kind": "deterministic"})
        assert d.json()["route"] == "none"
        assert d.json()["estimated_cost_usd"] == "0"


def test_live_requires_secret_and_auth(monkeypatch):
    import app.gateway.api as api

    async def stub_ollama(*args, **kwargs):
        return ProviderResult("A dry synthetic answer", 12, 7)

    monkeypatch.setattr(api, "call_ollama", stub_ollama)
    cfg = Settings(enable_live_execution=True, control_plane_api_key="x" * 32)
    with TestClient(create_app(cfg)) as c:
        assert c.post("/api/v1/route/plan", json=PUBLIC).status_code == 401
        headers = {"x-control-plane-key": "x" * 32}
        response = c.post("/api/v1/infer", json=PUBLIC, headers=headers)
        assert response.status_code == 200
        assert response.json()["quality_validated"] is False
        assert response.json()["output_tokens"] == 7
        usage = c.get("/api/v1/usage", headers=headers).json()
        assert usage["completed_requests"] == 1
        assert usage["basis"] == "illustrative_per_request_not_billed"
        assert "agentos_requests_total" in c.get("/metrics", headers=headers).text


def test_live_azure_config_rejects_non_https():
    import pytest

    with pytest.raises(ValueError, match="HTTPS"):
        Settings(enable_live_execution=True, control_plane_api_key="x" * 32,
                 enable_azure_routing=True, azure_endpoint="http://example.com",
                 azure_deployment="demo", azure_api_key="secret")


def test_invalid_extra_fields_rejected():
    with TestClient(create_app(Settings())) as c:
        result = c.post("/api/v1/route/plan", json={**PUBLIC, "access_token": "bad"})
        assert result.status_code == 422
