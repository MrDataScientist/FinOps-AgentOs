# ADR-003 — Preserve human-to-agent authority lineage

- **Status:** Accepted for the local security governance PoC (not production)
- **Decision date:** 2026-11-14

## Context

A shared service credential cannot answer who delegated authority to an autonomous actor. An agent must not be able to claim a user identity merely by supplying an unverified string.

## Decision

Introduce an explicitly enabled, separate governance API using a narrow subset of OAuth 2.0 Token Exchange (RFC 8693). Verify **both** signed human subject tokens and signed machine actor tokens for a local trust issuer and dedicated exchange audience. Issue a short-lived, audience-restricted delegated bearer credential with human subject, agent actor, a unique token ID and down-scoped authorization details. Do not exchange expired, invalidly signed, wrong-audience, or unknown-agent credentials. Source permissions intersect with the local agent registry and tool policy.

Credentials are signed with a configured shared HMAC secret strictly for a synthetic, single-issuer laboratory; **there is no token issuance HTTP endpoint**. Token generation is done offline by the demo/tests. The control plane is disabled by default and requires separate strong operator and signing secrets.

## Alternatives rejected

- Trusting an agent-supplied human ID or arbitrary HTTP headers.
- Reusing the inference API key as proof of human delegation.
- Broad service tokens with all Jira permissions.
- Exposing a public test-token minting endpoint.

## Consequences and follow-up

- This PoC does **not** implement OIDC, real IdP login, interoperable full RFC 8693 token exchange, asymmetric signature verification, key rotation, subject revocation, replay prevention, token binding or multi-tenant identity isolation.
- Next: replace demo credentials with validated enterprise IdP access tokens/JWKS, separate human and workload issuers (e.g. SPIFFE/workload identity), implement proper consent/delegation lifecycles and expiry/revocation policy.
- Human subject and machine actor must remain separately visible in every audit event.

See [governance demo](../governance-mvp.md) and [ADR-004](ADR-004-agent-policy-and-audit.md).
