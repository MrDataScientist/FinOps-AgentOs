# FinOps-AgentOS

**Local-first, policy-gated AI inference control-plane reference.** A small open-source Python service for *planning* model selection and, only when explicitly enabled, invoking Ollama or Azure OpenAI. Stormscope is the first conceptual integration. This is an **experimental MVP**, not a production-ready self-healing platform or a proven cost optimizer.

## Quick start (Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Dry-run is the default: no model API calls and no Azure resources are needed.

```bash
curl http://127.0.0.1:8080/health
curl -X POST http://127.0.0.1:8080/api/v1/route/plan \
  -H 'Content-Type: application/json' \
  -d '{"task_kind":"explanation","classification":"public","prompt":"Explain a synthetic weather scenario."}'
```

Open `http://127.0.0.1:8080/docs` for Swagger/OpenAPI docs.

## Local containers

```bash
podman compose -f infrastructure/compose.yaml up --build
# Alternatively: docker compose -f infrastructure/compose.yaml up --build
```

API: `127.0.0.1:8080`. Optional local Prometheus is enabled with `--profile observability`. No cloud account required.

## Optional local inference

1. Install/run Ollama and pull an appropriate model (e.g. `ollama pull qwen2.5-coder:3b`).
2. Set environment `ENABLE_LIVE_EXECUTION=true`, `OLLAMA_URL`, `OLLAMA_MODEL`, and a random `CONTROL_PLANE_API_KEY` of at least 24 characters.
3. Call `POST /api/v1/infer` with header `x-control-plane-key`. By default the server never contacts Ollama. The provided Compose sample intentionally forces live execution **off**.
4. Cloud execution requires separate explicit `ENABLE_AZURE_ROUTING=true`, HTTPS endpoint, Azure deployment and credential; do not use corporate inputs without approval.

**Important:** `LOCAL_ESTIMATED_USD_PER_REQUEST` and `AZURE_ESTIMATED_USD_PER_REQUEST` are illustrative hypotheses—not real invoices, token-level pricing, savings, or a hard spend ceiling. Local models require compute, power and operating cost. The in-memory usage ledger resets on restart and never evaluates response correctness.

## Repository

- `app/gateway`: FastAPI endpoints, Prometheus metrics
- `app/policies`, `app/routing`: explicit classification and budget gates
- `app/providers`: opt-in Ollama and Azure single-shot adapters
- `app/accounting`: ephemeral illustrative accounting
- `app/evaluation`: evaluation contracts only
- `app/workflows`: approval stub, **not LangGraph automation yet**
- `integrations/stormscope`: sample explanation-only adapter; existing risk scores remain authoritative
- `scenarios`: synthetic examples
- `observability`: Prometheus and example Grafana panel definitions
- `infrastructure`: Compose container and future Terraform feasibility
- `docs`: architecture, evaluations and routing decision

```bash
python -m pytest -q
```

## Next phases (not implemented)

1. Evaluate actual model quality and operating costs on versioned scenarios.
2. Add **quality-qualified** routing and enforce real quotas, not illustrative request costs.
3. Reconcile infrastructure costs and cloud invoices; report cost per accepted task.
4. Build circuit breakers, recovery and full observability.
5. Add governance for agent-proposed infrastructure changes; require explicit approval before consequential writes.

[Architecture](docs/architecture.md) · [Evaluation plan](docs/evaluation-plan.md) · [Routing ADR](docs/decisions/ADR-001-routing-and-cost.md).

MIT-licensed code; model/service licenses are separate.
