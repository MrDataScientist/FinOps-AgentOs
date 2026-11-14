"""Run an entirely synthetic governed tool-read demonstration: python -m app.governance.demo."""

import tempfile
import time
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import Settings
from app.governance.tokens import EXCHANGE_AUDIENCE, ISSUER, issue_token
from app.main import create_app


def source(kind: str, subject: str, key: str) -> str:
    now = int(time.time())
    return issue_token(
        {
            "iss": ISSUER, "aud": EXCHANGE_AUDIENCE, "token_class": kind,
            "sub": subject, "permissions": ["jira.issue.read"],
            "iat": now, "exp": now + 600, "jti": str(uuid4()),
        }, key,
    )


def main() -> None:
    signing_key = "synthetic-demo-signing-key-" + "s" * 32
    operator_key = "synthetic-demo-operator-key-" + "o" * 32
    with tempfile.TemporaryDirectory() as directory:
        settings = Settings(
            governance_enabled=True,
            governance_signing_key=signing_key,
            control_plane_api_key=operator_key,
            governance_audit_db=str(Path(directory) / "events.sqlite3"),
        )
        with TestClient(create_app(settings)) as client:
            exchanged = client.post(
                "/api/v1/governance/token/exchange",
                json={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "subject_token": source("human", "human:alex", signing_key),
                    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "actor_token": source("agent", "agent:triage", signing_key),
                    "actor_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "authorization_details": [
                        {"type": "mcp_tool", "tool": "jira.issue.read", "resource": "DEMO-1"}
                    ],
                },
            )
            exchanged.raise_for_status()
            bearer = exchanged.json()["access_token"]
            headers = {"Authorization": f"Bearer {bearer}"}
            allowed = client.post(
                "/api/v1/governance/tools/execute",
                json={"tool": "jira.issue.read", "resource": "DEMO-1"}, headers=headers,
            )
            denied = client.post(
                "/api/v1/governance/tools/execute",
                json={"tool": "jira.issue.update", "resource": "DEMO-1"}, headers=headers,
            )
            audit = client.get(
                "/api/v1/governance/audit", headers={"x-control-plane-key": operator_key}
            )
            print("Authorized read:", allowed.status_code, allowed.json().get("result"))
            print("Unauthorized write:", denied.status_code)
            print("Audit valid:", audit.json()["chain_valid"],
                  "events:", audit.json()["total_events"])


if __name__ == "__main__":
    main()
