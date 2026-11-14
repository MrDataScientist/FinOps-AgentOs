# FinOps-AgentOS roadmap

**Status:** planning artifact; implementation status below is explicit. Goal: secure, reliable, cost-aware AI workflows without autonomous production changes.

| Track | Current MVP | Next | Later |
| --- | --- | --- | --- |
| Routing and evidence | Local deterministic route planning; offline tests; illustrative accounting | Approved opt-in inference; independent quality/latency/cost measurements | Real budgets, bill reconciliation, reliability/availability policies |
| Agent security | Local synthetic delegated token exchange; exact mock Jira read grant; SQLite HMAC audit (**PoC only**) | External IdP/workload identities, key rotation, policy decision point, human approvals, MCP wiring | A2A cross-agent delegation, independent audit sink, incident response and production control gates |
| Gateway operations | Standalone FastAPI control plane | Production identity boundary and telemetry | Evaluate Azure API Management policies, server vs tool authorization boundaries |
| Integrations | Synthetic Stormscope risk explanation adapter | Jira-compatible MCP mock, LangGraph dual-agent orchestration | Slack/Confluence use cases, approved enterprise adapters |
| Recovery / infrastructure | No autonomous changes | Human-reviewed change proposals, infra test environment | Terraform/OpenTofu changes gated by policy, rollout safety, rollback and verified audit |

## Security roadmap milestones

- **Phase 1:** demonstrate the three authority questions with read-only synthetic tooling. **Implemented in governance PoC only**; LangGraph dual-agent orchestration and actual MCP protocol transport remain future work.
- **Phase 2:** make identity, centralized policy and human approval independent of an agent's generated output.
- **Phase 3:** add A2A trust propagation, immutable external security traces and FinOps budget controls for tool actions.
- **Phase 4:** evaluate managed MCP gateway with Azure API Management and establish whether enforcement is server-scoped or tool-scoped for the chosen product/version.

**Non-goals for now:** real Jira write access, live customer data, deploy/merge automation, claims of CRA compliance, production token exchange or tamper-proof audit.

Details: [Governance MVP](governance-mvp.md), [ADR-003](decisions/ADR-003-agent-delegation-and-token-exchange.md), [ADR-004](decisions/ADR-004-agent-policy-and-audit.md).
