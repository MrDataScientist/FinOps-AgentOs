---
name: finops-policy-validation
description: Validate FinOps-AgentOS routing, privacy, inference gates and cost evidence when changing policies, providers, accounting or Stormscope integration.
---

# Validate FinOps-AgentOS

1. Read [repository instructions](../../../AGENTS.md) and inspect the changed paths and acceptance criteria.
2. Inspect the relevant sources listed below before choosing assertions. Preserve fail-closed classification and budget routing, authenticated opt-in live execution, and application-owned Stormscope risk scores. Test denied routes, unavailable providers, missing usage metadata and unauthorized inference. Keep synthetic routing evidence distinct from model-answer quality, real provider latency and reconciled billing. The ledger is an illustrative in-memory estimate, not a durable billing system or proven savings.
3. Run the smallest relevant checks first, then the commands below when their scope applies. Inspect scripts, fixtures and configuration before executing them; these are a check menu, not permission for external calls.
4. Record each acceptance criterion as Pass, Fail or Skipped with observed evidence and the tested revision. Record blocked tools or missing data explicitly. Recheck an unexpected failure once, then distinguish a regression from pre-existing behavior using the code and baseline.
5. Report remaining gaps and recovery steps. Never promote mock/offline evidence into live-system correctness or production readiness.

## Sources

- [app/policies/engine.py](../../../app/policies/engine.py)
- [app/providers/client.py](../../../app/providers/client.py)
- [app/accounting/ledger.py](../../../app/accounting/ledger.py)
- [tests/test_gateway.py](../../../tests/test_gateway.py)
- [tests/test_stormscope_contract.py](../../../tests/test_stormscope_contract.py)
- [docs/evaluation-results.md](../../../docs/evaluation-results.md)

## Check menu (from repository configuration)

```bash
python -m pytest -q
ruff check .
python -m app.evaluation.offline --output artifacts/offline-evaluation
python -m integrations.stormscope.demo
```
