"""Demonstrate the integration contract using synthetic weather-risk data only.

Usage: python -m integrations.stormscope.demo
No outbound traffic or real model inference occurs.
"""

import argparse
import asyncio
import json
import secrets
from pathlib import Path

import httpx

from app.config import Settings
from app.main import create_app
from app.models import DataClassification
from integrations.stormscope.contract import (
    StormscopeRiskSnapshot,
    from_weather_risk_response,
)

DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "scenarios/stormscope-risk-synthetic.json"


async def run_demo(input_file: Path) -> dict[str, object]:
    raw = json.loads(input_file.read_text(encoding="utf-8"))
    if raw.get("data_origin") != "synthetic":
        raise ValueError("Public demo accepts synthetic fixtures only")
    data = raw["weather_risk_response"]
    snapshot = StormscopeRiskSnapshot.model_validate(data)
    task = from_weather_risk_response(
        data,
        classification=DataClassification.PUBLIC,  # Fixture contains no user data.
    )
    demo_key = secrets.token_urlsafe(32)
    auth_headers = {"X-Control-Plane-Key": demo_key}
    app = create_app(Settings(control_plane_api_key=demo_key))
    request = task.model_dump(mode="json")
    cases = (
        ("missing_credential", "/api/v1/route/plan", {}, request, 401),
        ("plan_allowed", "/api/v1/route/plan", auth_headers, request, 200),
        (
            "budget_denied",
            "/api/v1/route/plan",
            auth_headers,
            {**request, "max_estimated_cost_usd": "0"},
            403,
        ),
        ("live_execution_denied", "/api/v1/infer", auth_headers, request, 403),
    )
    gateway_decisions = []
    decision = {}
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://agentos.test",
    ) as client:
        for case, endpoint, headers, body, expected_status in cases:
            result = await client.post(endpoint, headers=headers, json=body)
            if result.status_code != expected_status:
                raise RuntimeError(
                    f"{case}: expected HTTP {expected_status}, got {result.status_code}"
                )
            response = result.json()
            if case == "plan_allowed":
                decision = response
            gateway_decisions.append(
                {
                    "case": case,
                    "endpoint": endpoint,
                    "credential_presented": bool(headers),
                    "http_status": result.status_code,
                    "reason": response["reason"] if result.is_success else response["detail"],
                }
            )
    return {
        "data_origin": "synthetic",
        "mode": "dry_run_policy_only",
        "stormscope_risk_score": snapshot.risk_score,
        "stormscope_risk_level": snapshot.risk_level,
        "agentos_route": decision["route"],
        "agentos_executable": decision["executable"],
        "illustrative_cost_usd": decision["estimated_cost_usd"],
        "cost_basis": decision["cost_basis"],
        "risk_score_unchanged": snapshot.risk_score == data["risk_score"],
        "gateway_decisions": gateway_decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Stormscope routing demonstration")
    parser.add_argument("--input", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run_demo(args.input)), indent=2))


if __name__ == "__main__":
    main()
