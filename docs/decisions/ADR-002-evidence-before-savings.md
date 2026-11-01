# ADR-002 — Evidence before claims of savings or quality

- **Status:** Accepted for the portfolio MVP
- **Decision date:** 2026-11-01

## Context

A router can reduce nominal per-call token fees while increasing total cost through retries, compute, poor accuracy or operational workload. Local inference has nonzero TCO. A synthetic prompt fixture is not a scientific weather observation or an independent AI quality label.

## Decision

CI will first capture real **policy contract** outcomes through the FastAPI route-planning endpoint. Outputs contain case provenance, measured in-process latency and explicitly hypothetical prices only. Cloud vs local inference *quality*, *cost per accepted business outcome* and *savings* remain unmeasured until a controlled opt-in benchmark with independent labels and reconciled charges is completed. No dashboard may label illustrative numbers "dollars saved."

## Rejected alternatives

- Claim projected percent savings as actual.
- Treat a successful routing decision as an accepted AI answer.
- Present local-model compute as free.
- Treat synthetic input consistency as verified meteorological correctness.

## Follow-up gates

- Golden dataset and independent quality review; keep risk scoring immutable.
- Azure and local model evaluation within approved data classifications.
- Retry, latency, fallback and token telemetry with non-sensitive traces.
- Full cloud/provider bills plus private inference equipment and labor cost.
- Executive summary with both negative results and residual risks.
