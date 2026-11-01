"""Demonstrate the integration contract using synthetic weather-risk data only.

Usage: python -m integrations.stormscope.demo
No outbound traffic or real model inference occurs.
"""

import argparse
import asyncio
import json
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
    app = create_app(Settings())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://agentos.test",
    ) as client:
        result = await client.post("/api/v1/route/plan", json=task.model_dump(mode="json"))
    result.raise_for_status()
    decision = result.json()
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
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic Stormscope routing demonstration")
    parser.add_argument("--input", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run_demo(args.input)), indent=2))


if __name__ == "__main__":
    main()
