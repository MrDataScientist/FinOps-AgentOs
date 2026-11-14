"""No external tools, real identities, or cloud calls in these tests."""

import sqlite3
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.governance.tokens import EXCHANGE_AUDIENCE, ISSUER, issue_token
from app.main import create_app

SECRET = "s" * 48
OPERATOR_KEY = "o" * 32
GRANT = {"type": "mcp_tool", "tool": "jira.issue.read", "resource": "DEMO-1"}


def settings(tmp_path):
    return Settings(
        governance_enabled=True,
        governance_signing_key=SECRET,
        governance_audit_db=str(tmp_path / "audit.sqlite3"),
        control_plane_api_key=OPERATOR_KEY,
    )


def credential(kind, subject, permissions, *, expiry=600, audience=EXCHANGE_AUDIENCE):
    now = int(time.time())
    return issue_token(
        {
            "iss": ISSUER, "aud": audience, "token_class": kind,
            "sub": subject, "permissions": permissions, "iat": now,
            "exp": now + expiry, "jti": str(uuid4()),
        },
        SECRET,
    )


def request_body(grant=GRANT, actor="agent:triage"):
    return {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": credential("human", "human:alex", ["jira.issue.read"]),
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "actor_token": credential("agent", actor, ["jira.issue.read"]),
        "actor_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "authorization_details": [grant],
    }


def exchange(client, body=None):
    return client.post("/api/v1/governance/token/exchange", json=body or request_body())


def test_disabled_by_default():
    with TestClient(create_app(Settings())) as client:
        assert client.post("/api/v1/governance/token/exchange", json=request_body()).status_code == 404


def test_enabled_requires_distinct_strong_secrets(tmp_path):
    with pytest.raises(ValueError, match="governance"):
        Settings(governance_enabled=True, governance_audit_db=str(tmp_path / "audit.db"))
    with pytest.raises(ValueError, match="distinct"):
        Settings(governance_enabled=True, governance_signing_key=SECRET,
                 control_plane_api_key=SECRET)


def test_delegated_read_and_audit_evidence(tmp_path):
    config = settings(tmp_path)
    with TestClient(create_app(config)) as client:
        response = exchange(client)
        assert response.status_code == 200, response.text
        assert response.json()["expires_in"] <= 300
        assert response.json()["authorization_details"] == [GRANT]
        token = response.json()["access_token"]
        read = client.post(
            "/api/v1/governance/tools/execute",
            json={"tool": "jira.issue.read", "resource": "DEMO-1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert read.status_code == 200, read.text
        assert read.json()["result"]["key"] == "DEMO-1"
        assert client.get("/api/v1/governance/audit").status_code == 401
        audited = client.get(
            "/api/v1/governance/audit", headers={"x-control-plane-key": OPERATOR_KEY}
        ).json()
        assert audited["chain_valid"] is True
        assert [e["decision"] for e in audited["events"]] == ["allowed", "allowed"]
        assert audited["events"][1]["human_subject"] == "human:alex"
        assert audited["events"][1]["agent_subject"] == "agent:triage"
        assert audited["events"][1]["token_jti"] == audited["events"][0]["token_jti"]
        assert token not in str(audited)
    with TestClient(create_app(config)) as reopened:
        assert reopened.get(
            "/api/v1/governance/audit", headers={"x-control-plane-key": OPERATOR_KEY}
        ).json()["total_events"] == 2


def test_denies_unauthorized_tool_and_resource(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as client:
        token = exchange(client).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.post(
            "/api/v1/governance/tools/execute",
            json={"tool": "jira.issue.read", "resource": "DEMO-2"}, headers=headers
        ).status_code == 403
        assert client.post(
            "/api/v1/governance/tools/execute",
            json={"tool": "jira.issue.update", "resource": "DEMO-1"}, headers=headers
        ).status_code == 403
        audit = client.get(
            "/api/v1/governance/audit", headers={"x-control-plane-key": OPERATOR_KEY}
        ).json()
        assert [e["decision"] for e in audit["events"]] == ["allowed", "denied", "denied"]


def test_denies_scope_escalation_unregistered_agent_and_expiry(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as client:
        assert exchange(client, request_body({
            "type": "mcp_tool", "tool": "jira.issue.update", "resource": "DEMO-1"
        })).status_code == 403
        assert exchange(client, request_body(actor="agent:unknown")).status_code == 403
        expired = request_body()
        expired["subject_token"] = credential("human", "human:alex", ["jira.issue.read"],
                                               expiry=-5)
        assert exchange(client, expired).status_code == 401


def test_rejects_forged_tokens_wrong_audience_and_missing_bearer(tmp_path):
    with TestClient(create_app(settings(tmp_path))) as client:
        body = request_body()
        body["subject_token"] += "tamper"
        assert exchange(client, body).status_code == 401
        body = request_body()
        body["actor_token"] = credential(
            "agent", "agent:triage", ["jira.issue.read"], audience="other-service"
        )
        assert exchange(client, body).status_code == 401
        assert client.post(
            "/api/v1/governance/tools/execute",
            json={"tool": "jira.issue.read", "resource": "DEMO-1"},
        ).status_code == 401


def test_audit_detects_modified_entry(tmp_path):
    config = settings(tmp_path)
    with TestClient(create_app(config)) as client:
        assert exchange(client).status_code == 200
    with sqlite3.connect(config.governance_audit_db) as db:
        db.execute("UPDATE audit_events SET decision='denied' WHERE seq=1")
    with TestClient(create_app(config)) as client:
        report = client.get(
            "/api/v1/governance/audit", headers={"x-control-plane-key": OPERATOR_KEY}
        ).json()
        assert report["chain_valid"] is False
