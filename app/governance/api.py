"""Offline delegated-authority demonstration; isolated from inference endpoints."""

import secrets
import time
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from app.governance.audit import AuditStore
from app.governance.policy import PolicyRejected, authorized_grants, execute_read
from app.governance.tokens import (
    EXCHANGE_AUDIENCE,
    ISSUER,
    TOOL_AUDIENCE,
    TokenRejected,
    issue_token,
    verify_token,
)

router = APIRouter(prefix="/api/v1/governance", tags=["governance-poc"])
ACCESS_TOKEN_TYPE = "urn:ietf:params:oauth:token-type:access_token"
TOKEN_EXCHANGE_GRANT = "urn:ietf:params:oauth:grant-type:token-exchange"


class ToolGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["mcp_tool"]
    tool: str = Field(min_length=1, max_length=80)
    resource: str = Field(min_length=1, max_length=80)


class ExchangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grant_type: Literal["urn:ietf:params:oauth:grant-type:token-exchange"]
    subject_token: str = Field(min_length=1)
    subject_token_type: Literal["urn:ietf:params:oauth:token-type:access_token"]
    actor_token: str = Field(min_length=1)
    actor_token_type: Literal["urn:ietf:params:oauth:token-type:access_token"]
    requested_token_type: Literal["urn:ietf:params:oauth:token-type:access_token"]
    authorization_details: list[ToolGrant] = Field(min_length=1, max_length=10)


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(min_length=1, max_length=80)
    resource: str = Field(min_length=1, max_length=80)


def _audit(request: Request) -> AuditStore:
    return request.app.state.governance_audit


def _operator_access(request: Request, key: str | None) -> None:
    configured = request.app.state.settings.control_plane_api_key
    if not configured or not secrets.compare_digest(key or "", configured):
        raise HTTPException(status_code=401, detail="Operator access required")


@router.post("/token/exchange")
def exchange(data: ExchangeRequest, request: Request) -> dict:
    secret = request.app.state.settings.governance_signing_key
    human = None
    agent = None
    try:
        human = verify_token(
            data.subject_token, secret, audience=EXCHANGE_AUDIENCE, token_class="human"
        )
        agent = verify_token(
            data.actor_token, secret, audience=EXCHANGE_AUDIENCE, token_class="agent"
        )
        grants = authorized_grants(
            [grant.model_dump() for grant in data.authorization_details], human, agent
        )
    except (TokenRejected, PolicyRejected) as exc:
        _audit(request).append(
            event_type="token_exchange", decision="denied",
            reason=type(exc).__name__,
            human_subject=human["sub"] if human else None,
            agent_subject=agent["sub"] if agent else None,
        )
        status = 401 if isinstance(exc, TokenRejected) else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc

    now = int(time.time())
    expires_at = min(now + 300, human["exp"], agent["exp"])
    if expires_at <= now:
        raise HTTPException(status_code=401, detail="Delegation expired")
    jti = str(uuid4())
    claims = {
        "iss": ISSUER,
        "aud": TOOL_AUDIENCE,
        "token_class": "delegated",
        "sub": human["sub"],
        "act": {"sub": agent["sub"]},
        "authorization_details": grants,
        "iat": now,
        "exp": expires_at,
        "jti": jti,
    }
    _audit(request).append(
        event_type="token_exchange", decision="allowed", reason="delegated",
        human_subject=human["sub"], agent_subject=agent["sub"], token_jti=jti,
    )
    return {
        "access_token": issue_token(claims, secret),
        "issued_token_type": ACCESS_TOKEN_TYPE,
        "token_type": "Bearer",
        "expires_in": expires_at - now,
        "authorization_details": grants,
    }


@router.post("/tools/execute")
def execute(data: ToolRequest, request: Request, authorization: str | None = Header(None)) -> dict:
    secret = request.app.state.settings.governance_signing_key
    human = None
    agent = None
    jti = None
    try:
        prefix, separator, bearer = (authorization or "").partition(" ")
        if prefix.lower() != "bearer" or not separator or not bearer:
            raise TokenRejected("Bearer token required")
        claims = verify_token(bearer, secret, audience=TOOL_AUDIENCE, token_class="delegated")
        human = claims["sub"]
        actor = claims.get("act")
        agent = actor.get("sub") if isinstance(actor, dict) else None
        jti = claims["jti"]
        if not human.startswith("human:") or not isinstance(agent, str):
            raise TokenRejected("Invalid delegation lineage")
        result = execute_read(data.tool, data.resource, claims.get("authorization_details", []))
    except (TokenRejected, PolicyRejected, TypeError) as exc:
        _audit(request).append(
            event_type="tool_execution", decision="denied", reason=type(exc).__name__,
            human_subject=human, agent_subject=agent, tool=data.tool,
            resource=data.resource, token_jti=jti,
        )
        status = 401 if isinstance(exc, TokenRejected) else 403
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    _audit(request).append(
        event_type="tool_execution", decision="allowed", reason="mock_read",
        human_subject=human, agent_subject=agent, tool=data.tool,
        resource=data.resource, token_jti=jti,
    )
    return {"tool": data.tool, "resource": data.resource, "result": result}


@router.get("/audit")
def audit_events(
    request: Request,
    x_control_plane_key: str | None = Header(None),
    limit: int = 100,
) -> dict:
    _operator_access(request, x_control_plane_key)
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    return _audit(request).inspect(limit=limit)
