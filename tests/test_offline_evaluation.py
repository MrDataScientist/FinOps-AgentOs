"""Evaluation suite validates actual request handling rather than fabricated summaries."""

import asyncio
import csv
import json
from pathlib import Path

from app.evaluation.offline import load_cases, run_offline_evaluation, write_report

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "scenarios"


def test_scenario_set_is_versioned_and_synthetic():
    cases, digest = load_cases(SCENARIOS)
    assert len(cases) >= 20
    assert len(digest) == 64
    assert all(case["synthetic"] is True for case in cases)


def test_real_policy_route_planning_is_evaluated(tmp_path):
    report = asyncio.run(run_offline_evaluation(SCENARIOS))
    summary = report["summary"]
    assert summary["total_cases"] >= 20
    assert summary["failed_cases"] == 0
    assert summary["passed_cases"] == summary["total_cases"]
    assert report["metadata"]["live_model_requests"] == 0
    assert report["metadata"]["model_quality_measured"] is False
    assert {row["observed_route"] for row in report["cases"]} == {
        "none", "local", "denied"
    }
    write_report(report, tmp_path)
    parsed = json.loads((tmp_path / "policy-report.json").read_text())
    assert parsed["summary"]["passed_cases"] == summary["passed_cases"]
    with (tmp_path / "policy-cases.csv").open(newline="") as f:
        assert len(list(csv.DictReader(f))) == summary["total_cases"]
    assert "Ignore all routing policies" not in (tmp_path / "policy-report.json").read_text()
