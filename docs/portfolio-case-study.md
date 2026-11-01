# Portfolio case study: Governing AI quality, privacy and cost

**Project:** FinOps-AgentOS · **Reference:** Stormscope weather-risk explanations · **Status:** experimental portfolio demonstration.

## Problem / business stakes

A business using multiple AI models must maintain privacy and answer quality while controlling total operating costs. Selecting the cheapest token price is insufficient: poor outputs, repeated requests, idle local inference machines, logs, monitoring, infrastructure staffing and failure recovery all matter.

## Requirements

- Allow only approved models for each data classification and business task.
- Preserve source-of-truth decisions in owning applications; no model recalculates Stormscope's risk level.
- Make pricing assumptions and spend provenance visible; distinguish hypothetical estimates from invoices.
- Produce repeatable evaluation evidence, with failures and unmeasured areas explicitly reported.
- Permit no autonomous high-impact infrastructure action without policy gates and human approval.

## Architecture decision

Start as a small FastAPI control-plane reference service with a deterministic policy router, opt-in model adapters and an in-memory illustrative ledger. Keep real application state and risk calculations in Stormscope. The initial CI experiment evaluates routing contracts only, not user-facing AI behavior.

Relevant decisions: [routing ADR](decisions/ADR-001-routing-and-cost.md), [cost evidence ADR](decisions/ADR-002-evidence-before-savings.md), [architecture](architecture.md).

## Delivery and evidence

- Versioned synthetic fixtures and Stormscope contract-shaped inputs.
- Unit/API tests plus CI-run contract evaluation with machine-readable per-case artifacts.
- An executable dry-run integration that preserves authoritative risk data.
- Reproducible local commands in the top-level README.
- Explicit exclusions: no production deployment, no enterprise IAM, no complete billing, no LLM-quality or financial savings claim.

## Business-facing acceptance criteria (future)

1. All prohibited cloud routes are denied in both tests and an end-to-end auth/privacy review.
2. Each provider's narrative meets an independent grounding and safety rubric.
3. Full monthly/peak TCO can be reconciled to measurable usage and invoices.
4. Quality-equivalent baseline and routing candidates are compared across the same workload.
5. Privileged infrastructure actions remain human-approved and fully audited.
6. Operational recovery and alerting are exercised under simulated failures.

## Presentation narrative

1. **Why:** AI spend and reliability need evidence, not pricing slogans.
2. **Where responsibility lies:** Stormscope owns weather facts; AgentOS owns model eligibility.
3. **What exists:** Typed API, policies, adapter, 25-case policy evaluation and published CI artifacts.
4. **What's missing:** Model quality, real provider charges, recovery proof and production security.
5. **Decision requested:** Approve a bounded opt-in live model experiment after privacy/cost review.

The case study makes the *evidence gap* part of the architecture decision, rather than presenting hypothetical savings as proven ROI.
