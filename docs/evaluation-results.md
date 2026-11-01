# Evaluation evidence — measured policy behavior, not measured model performance

## Reproducible result

Every PR workflow invokes:

```bash
python -m app.evaluation.offline --output artifacts/offline-evaluation
```

The runner uses 25 explicitly **synthetic** expected-route cases from four checked-in fixture files. It calls the real FastAPI `POST /api/v1/route/plan` handler using `httpx.ASGITransport` (in-process; no external network). For each case it records a **measured** HTTP request duration, the actual route/denial, expected route, pass/fail and any **illustrative** estimate. The script exits nonzero if a routing expectation fails.

### Evidence provenance

- GitHub Actions `Python tests` workflow uploads a `policy-evaluation-<run id>` artifact containing `policy-report.json`, `policy-cases.csv` and the console output.
- JSON includes UTC evaluation time, Git commit SHA, Python version, SHA-256 over exact scenario bytes, case count and the failed-case count.
- Download the artifact from the relevant PR workflow run, not from this README, to inspect **actual results**.
- Generated reports are never checked in as immutable "official" benchmarks. Rerun the command on your own machine for comparison, and keep environment notes.

## What these results establish

| Claim | State |
| --- | --- |
| Deterministic privacy/budget/task route decisions match predefined cases | **Tested by offline policy suite** |
| Denied and deterministic-only paths do not trigger a model call in the suite | **By design: plan-only requests** |
| In-process FastAPI plan latency | **Observed per run; not representative of production/network latency** |
| LLM correctness, citation validity, multilingual quality | **Not measured** |
| Actual cloud/local cost, invoice reconciliation, net savings | **Not measured** |
| Stormscope production end-to-end integration | **Not implemented** |
| Availability, resilience, security penetration tests, SLA | **Not demonstrated** |

This distinction matters: 25/25 passing policy checks (if observed in CI) is **not** evidence of a 100% correct LLM, real cost savings or production reliability.

## Next: real model + unit-economics evidence

Freeze a separate 20–30 item independently-labelled *explanation* golden set with immutable risk fields, hazard citations, multilingual queries, prompt injection, failure cases and expected limitations. Run the same cases against an approved Azure model and a known local model. Record model/revision, tokenizer, prompt revision, latency p50/p95, tokens, retries, accepted grounded responses, and cost inputs. Compare cost **per accepted task**, including local compute and billing, with a clearly stated quality threshold and uncertainty.

Do not send real employer data or personal locations to unapproved model endpoints. Avoid exposing raw prompt data in artifacts. Do not use synthetic fixtures to claim scientific forecast accuracy.
