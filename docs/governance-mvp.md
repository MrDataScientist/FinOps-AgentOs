# AgentOS Security Governance PoC — local authorization and audit MVP

## Three questions

1. **Who authorized this agent?** Signed human and actor demo credentials are verified, and token exchange produces a short-lived delegated JWT preserving both identities.
2. **What may it do?** The token carries exact tool/resource authorization details; the gateway independently enforces an allowlist before invoking mock tools.
3. **Can we prove what it did?** Every exchange and tool decision is logged with human/agent/tool/resource/token IDs. A local HMAC chain detects certain later record modifications.

**Scope:** Synthetic Jira-shaped objects only; no real Jira, MCP network transport, LangGraph orchestration, human login, or production identity integration. The MVP is opt-in and never runs cloud calls.

## Security flow

~~~mermaid
flowchart TD
 H[Verified demo human credential] --> EX[Token exchange / lineage]
 A[Verified demo agent credential] --> EX
 EX --> P[Deterministic grants intersection]
 P -->|deny| AU[(SQLite HMAC audit)]
 P -->|allow| T[5-minute scoped delegated bearer]
 T --> G[Runtime tool authorization]
 G -->|allow: Jira issue read| M[In-memory mock issue]
 G -->|deny all writes / mismatched resources| AU
 G --> AU
 OP[Operator key] --> AU
~~~

## Local run

Use Python 3.11+ and install development dependencies:

~~~bash
pip install -e '.[dev]'
python -m pytest -q
ruff check .
python -m app.governance.demo
~~~

The demo uses in-process FastAPI TestClient, creates temporary secrets and an isolated temporary SQLite audit file, exchanges two **synthetic signed** credentials, executes a permitted read, rejects an unauthorized write, and verifies the audit chain. It prints no tokens.

To expose the PoC HTTP API on **loopback only**, set ENABLE_GOVERNANCE_POC=true, CONTROL_PLANE_API_KEY and GOVERNANCE_SIGNING_KEY to **distinct** local random secrets (each at least 32 characters) and set GOVERNANCE_AUDIT_DB to a writable SQLite path. Start the FastAPI app locally and use separately minted test subject and actor credentials. The HTTP service never mints initial human/actor credentials. Disable the PoC outside a controlled lab.

## API

| Endpoint | Behavior |
| --- | --- |
| POST /api/v1/governance/token/exchange | RFC 8693-style input: signed subject_token + actor_token; grant_type, token types and exact authorization_details; issue a scoped token |
| POST /api/v1/governance/tools/execute | Bearer delegated token and exact tool/resource; enforce the policy and return synthetic Jira issue |
| GET /api/v1/governance/audit | Operator-key-protected, recent audit events and full-chain validation |

Example authorization detail:

~~~json
{"type":"mcp_tool","tool":"jira.issue.read","resource":"DEMO-1"}
~~~

The subject/actor token shapes have a local demo issuer, exchange audience, identity type, subject ID, issuer-provided permissions, issuance/expiry times and unique token IDs. The issued tool token carries sub (human) and act.sub (machine), tool audience and the narrowed grants.

## Acceptance checks

- Valid human + registered agent + exact read grant: HTTP 200 and correlated audit records.
- Unsupported tool (including write), different resource or unregistered agent: denied.
- Expired, forged or wrong-audience credentials: denied.
- Missing runtime bearer: denied and logged.
- Audit viewer without operator key: HTTP 401.
- Tamper an existing event: chain verification indicates failure.
- Disable feature flag: all governance API routes absent (404).
- No live models, external Jira/MCP calls, actual approvals, or infrastructure writes.

## Risks and production gates

This uses one shared symmetric signing trust root, offline synthetic identities and no revocation. A real integration must validate an enterprise identity provider and workload identity provider, separate keys, consent/delegation proof, key rotation, replay defense, and appropriate token semantics. It also needs MCP transport adapters, centralized PDP/PEP, per-tenant authorization, human approval for writes, independent immutable audit storage, trace correlation, threat modeling and operational monitoring. An HMAC-linked SQLite ledger is **not** independent proof of nonrepudiation.

## Roadmap mapping

- **Phase 1 — this PR:** two demo identities, signed exchange, allowlisted Jira-compatible mock tool, deny-by-default runtime enforcement, local chained audit.
- **Phase 2:** centralized policy decision service, fine-grained agent identity, human approval workflow and real MCP server integration.
- **Phase 3:** A2A exchange, independent audit traces, FinOps-AgentOS budget enforcement.
- **Phase 4:** evaluate Azure API Management as an MCP gateway; confirm capabilities and scope in the current service documentation before designing finer-grained tool authorization.

Architecture decisions: [ADR-003](decisions/ADR-003-agent-delegation-and-token-exchange.md), [ADR-004](decisions/ADR-004-agent-policy-and-audit.md).
