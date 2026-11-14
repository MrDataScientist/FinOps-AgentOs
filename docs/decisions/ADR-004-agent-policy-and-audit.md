# ADR-004 — Fail-closed per-tool authorization and auditable execution

- **Status:** Accepted for local security governance PoC (not production)
- **Decision date:** 2026-11-14

## Context

Tokens identifying a delegator and agent do not imply unrestricted access. Runtime calls must be bounded by tool/resource policy, and investigators need evidence of both allowed and denied actions.

## Decision

Express granular delegated permission as an authorization_details array with type **mcp_tool**, exact tool and exact resource, inspired by OAuth 2.0 Rich Authorization Requests (RFC 9396). It is a documented **custom authorization-detail type**, not a claim of full RFC 9396 interoperability.

At exchange time, intersect issuer-asserted human grants, issuer-asserted agent grants, local registered agent capabilities and a static gateway allowlist. Only synthetic **jira.issue.read** on DEMO-1 or DEMO-2 is supported. No Jira network connection, real write, arbitrary tool dispatch, wildcard resource or autonomous action. Deny everything else; do not execute based on a model-generated authorization conclusion.

At runtime, verify the delegated bearer token signature, expiry, audience, token class and exact authorization details again, then record the decision **before** returning a successful response. Unavailable audit storage prevents successful exchanges or tool execution (fail closed).

Persist selected event metadata in SQLite with an HMAC-linked chain: event ID, UTC timestamp, human, agent, tool, resource, token ID, decision and reason category. Never log raw credentials, prompts or request payloads. Restrict audit read access with an operator key. Audit storage is local and not immutable.

## Alternatives rejected

- Tool authorization by agent prompt or inference result.
- Allowing write operations in the first MVP.
- Relying on gateway request logs as sufficient audit evidence.
- Storing raw tokens or full tool parameters in the audit ledger.

## Consequences and follow-up

- HMAC-linked records detect local modifications **when the signing key remains protected**, but SQLite can be deleted, rolled back or replaced and is not a WORM/SIEM store or nonrepudiation guarantee. There is no tenant separation or retention/redaction lifecycle.
- Next: central PDP/PEP, resource-level ownership checks, human-in-the-loop approval for mutations, independent append-only audit sink, key management, trace propagation and signed attestations. Integrate with MCP tool dispatch and FinOps budget approval.
- Production incident response, risk modeling and EU CRA applicability need separate validation.

See [ADR-003](ADR-003-agent-delegation-and-token-exchange.md) and [governance demo](../governance-mvp.md).
