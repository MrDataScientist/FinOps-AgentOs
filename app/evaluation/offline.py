"""Reproducible end-to-end dry-run *policy* evaluation, NOT an LLM benchmark.

Executes actual FastAPI route plans in process, measures observed request latency,
checks pre-labelled synthetic cases, and emits CI artifacts without prompt text.
No provider model or billing API is contacted.
"""

import argparse
import asyncio
import csv
import hashlib
import json
import os
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns

import httpx

from app.config import Settings
from app.main import create_app

SCENARIO_FILES = (
    "simple-tasks.json",
    "complex-tasks.json",
    "security-tests.json",
    "policy-matrix.json",
)
EVALUATION_MODE = "dry_run_policy_contract_only"
FIELDNAMES = [
    "scenario_id",
    "expected_route",
    "observed_route",
    "status_code",
    "passed",
    "elapsed_ms",
    "illustrative_cost_usd",
    "cost_basis",
]


def load_cases(scenario_dir: Path) -> tuple[list[dict], str]:
    cases: list[dict] = []
    digest = hashlib.sha256()
    for filename in SCENARIO_FILES:
        raw = (scenario_dir / filename).read_bytes()
        digest.update(filename.encode("utf-8"))
        digest.update(raw)
        records = json.loads(raw)
        if not isinstance(records, list):
            raise ValueError(f"{filename} must contain a list")
        cases.extend(records)
    ids = [record["id"] for record in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("Scenario IDs must be unique")
    if not all(record.get("synthetic") is True for record in cases):
        raise ValueError("Only explicitly synthetic cases are allowed")
    return cases, digest.hexdigest()


def normalized_expected(label: str) -> str:
    if label.startswith("denied"):
        return "denied"
    if label in {"local", "none", "azure"}:
        return label
    raise ValueError(f"Unexpected expected-route label: {label}")


async def run_offline_evaluation(scenario_dir: Path) -> dict:
    cases, fixture_sha = load_cases(scenario_dir)
    app = create_app(
        Settings(enable_live_execution=False, enable_local_routing=True, enable_azure_routing=False)
    )
    rows: list[dict] = []
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://evaluation.test",
    ) as client:
        for item in cases:
            body = {
                key: item[key]
                for key in (
                    "task_kind", "classification", "prompt", "max_estimated_cost_usd"
                )
                if key in item
            }
            started = perf_counter_ns()
            response = await client.post("/api/v1/route/plan", json=body)
            elapsed_ms = round((perf_counter_ns() - started) / 1_000_000, 4)
            outcome = response.json()
            observed = "denied" if response.status_code == 403 else outcome.get("route")
            if response.status_code not in (200, 403):
                observed = f"http_{response.status_code}"
            expected = normalized_expected(item["expected_route_default"])
            rows.append(
                {
                    "scenario_id": item["id"],
                    "expected_route": expected,
                    "observed_route": observed,
                    "status_code": response.status_code,
                    "passed": observed == expected,
                    "elapsed_ms": elapsed_ms,
                    "illustrative_cost_usd": (
                        outcome.get("estimated_cost_usd") if response.status_code == 200 else None
                    ),
                    "cost_basis": (
                        outcome.get("cost_basis") if response.status_code == 200 else None
                    ),
                }
            )

    latencies = [r["elapsed_ms"] for r in rows]
    return {
        "metadata": {
            "evaluation_scope": EVALUATION_MODE,
            "utc_timestamp": datetime.now(timezone.utc).isoformat(),
            "code_sha": os.getenv("GITHUB_SHA", "local-uncommitted-or-unspecified"),
            "python_version": platform.python_version(),
            "scenario_sha256": fixture_sha,
            "scenario_files": list(SCENARIO_FILES),
            "live_model_requests": 0,
            "costs_from_real_billing": False,
            "model_quality_measured": False,
            "limitations": (
                "ASGI in-process route-plan latency and policy outcomes only; "
                "no network, real inference, scientific weather validation, "
                "real cloud invoices, or production latency/SLO measurements."
            ),
        },
        "summary": {
            "total_cases": len(rows),
            "passed_cases": sum(row["passed"] for row in rows),
            "failed_cases": sum(not row["passed"] for row in rows),
            "median_observed_policy_http_ms": round(statistics.median(latencies), 4),
            "latency_sample_count": len(latencies),
            "latency_is_production_benchmark": False,
        },
        "cases": rows,
    }


def write_report(report: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "policy-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "policy-cases.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(report["cases"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline synthetic routing contract evaluation")
    parser.add_argument("--scenarios", type=Path, default=Path("scenarios"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/offline-evaluation"))
    args = parser.parse_args()
    report = asyncio.run(run_offline_evaluation(args.scenarios))
    write_report(report, args.output)
    print(json.dumps(report["summary"], indent=2))
    if report["summary"]["failed_cases"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
