# ADR-001 — Deterministic, fail-closed model routing

- Status: **Accepted for this prototype**, not a corporate security policy.
- Date: 2026-10-31

## Context

Model routes determine privacy exposure and financial consequences. A probabilistic agent cannot assign itself permissions. Local inference has nonzero operating cost.

## Decision

Use explicit task-kind, classification and illustrative-budget gates; default to dry-run. Internal and restricted data route locally only; if no eligible route exists, return a policy denial. Complex public tasks require explicitly enabled cloud routing. Keep real inference separately opt-in and protected by an API key. No implicit cloud escalation. Return model outputs as unvalidated until checked by the calling application.

## Alternatives rejected

- Automatically fail over sensitive tasks to a cloud model.
- Treat local inference as free.
- Advertise dollar savings based on hypothetical rates.
- Allow agents to approve production infrastructure modifications.

## Follow-up

Replace per-request dummy cost estimates with measured, policy-enforced token and infrastructure budgets; add durable metering, independent model quality evaluations, tenant authorization, auditing and human-approved infrastructure recovery workflows.
