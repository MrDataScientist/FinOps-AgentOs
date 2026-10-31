# Observability starter

The API exposes Prometheus metrics on `/metrics`. Start `podman compose -f infrastructure/compose.yaml --profile observability up --build` for local Prometheus at loopback port 9090. Import `grafana/dashboard.json` into an independently managed Grafana instance and choose the Prometheus source; Grafana itself is **not** deployed here.

Avoid prompt content, request IDs or personal details in metric labels. `agentos_illustrative_cost_usd_total` is **not a bill or savings**. No production-ready tracing, durable accounting or alerting exists yet.
