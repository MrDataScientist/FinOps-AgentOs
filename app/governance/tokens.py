"""Minimal HS256 JWT envelope for a self-contained local PoC.

Not an OIDC verifier, federation implementation, or production token service.
A real deployment must use independent trust domains, JWKS/issuer discovery,
key rotation, audience policy, revocation, and replay controls.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

ISSUER = "agentos-local-demo"
EXCHANGE_AUDIENCE = "agentos-token-exchange"
TOOL_AUDIENCE = "agentos-mcp-gateway"


class TokenRejected(ValueError):
    """Invalid or expired signed credential."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    try:
        return base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise TokenRejected("Malformed token encoding") from exc


def issue_token(claims: dict[str, Any], secret: str) -> str:
    """Create signed tokens for tests and the offline demo, never via a public endpoint."""
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    body = _b64(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode())
    signing_input = f"{header}.{body}"
    signature = _b64(hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def verify_token(
    token: str, secret: str, *, audience: str, token_class: str
) -> dict[str, Any]:
    try:
        header, body, signature = token.split(".")
        metadata = json.loads(_unb64(header))
        claims = json.loads(_unb64(body))
    except (ValueError, TypeError) as exc:
        raise TokenRejected("Malformed token") from exc
    if metadata != {"alg": "HS256", "typ": "JWT"} or not isinstance(claims, dict):
        raise TokenRejected("Unsupported token format")
    expected = _b64(
        hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(signature, expected):
        raise TokenRejected("Invalid token signature")
    now = int(time.time())
    if (
        claims.get("iss") != ISSUER
        or claims.get("aud") != audience
        or claims.get("token_class") != token_class
        or type(claims.get("iat")) is not int
        or type(claims.get("exp")) is not int
        or claims["exp"] <= now
        or claims["iat"] > now + 30
        or claims["iat"] > claims["exp"]
        or not isinstance(claims.get("jti"), str)
        or not claims["jti"]
    ):
        raise TokenRejected("Invalid token claims or lifetime")
    if not isinstance(claims.get("sub"), str) or not claims["sub"]:
        raise TokenRejected("Missing token subject")
    return claims
