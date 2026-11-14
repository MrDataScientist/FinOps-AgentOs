"""Locally persisted HMAC-chained audit log. Tamper-evident, not tamper-proof."""

import hashlib
import hmac
import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

FIELDS = (
    "event_id", "occurred_at", "event_type", "decision", "human_subject",
    "agent_subject", "tool", "resource", "token_jti", "reason",
)


def _serialize(item: dict) -> bytes:
    return json.dumps(item, separators=(",", ":"), sort_keys=True).encode()


class AuditStore:
    def __init__(self, path: str, signing_key: str) -> None:
        self.path = path
        self.key = hmac.new(signing_key.encode(), b"agentos-audit-v1", hashlib.sha256).digest()
        self.lock = threading.Lock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS audit_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    occurred_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    human_subject TEXT,
                    agent_subject TEXT,
                    tool TEXT,
                    resource TEXT,
                    token_jti TEXT,
                    reason TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )"""
            )

    def _digest(self, prev_hash: str, item: dict) -> str:
        return hmac.new(self.key, prev_hash.encode() + _serialize(item), hashlib.sha256).hexdigest()

    def append(
        self, *, event_type: str, decision: str, reason: str,
        human_subject: str | None = None, agent_subject: str | None = None,
        tool: str | None = None, resource: str | None = None,
        token_jti: str | None = None,
    ) -> None:
        # Only deliberately selected metadata; never requests, tool args, JWTs, or API keys.
        record = {
            "event_id": str(uuid4()),
            "occurred_at": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "decision": decision,
            "human_subject": human_subject,
            "agent_subject": agent_subject,
            "tool": tool,
            "resource": resource,
            "token_jti": token_jti,
            "reason": reason,
        }
        with self.lock, sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            latest = db.execute("SELECT event_hash FROM audit_events ORDER BY seq DESC LIMIT 1")
            row = latest.fetchone()
            prev_hash = row[0] if row else "GENESIS"
            digest = self._digest(prev_hash, record)
            columns = ", ".join(FIELDS) + ", prev_hash, event_hash"
            placeholders = ", ".join("?" for _ in range(len(FIELDS) + 2))
            db.execute(
                f"INSERT INTO audit_events ({columns}) VALUES ({placeholders})",
                tuple(record[field] for field in FIELDS) + (prev_hash, digest),
            )

    def inspect(self, limit: int = 100) -> dict:
        with self.lock, sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            all_rows = db.execute("SELECT * FROM audit_events ORDER BY seq ASC").fetchall()
        previous = "GENESIS"
        valid = True
        for row in all_rows:
            event = {field: row[field] for field in FIELDS}
            if (
                row["prev_hash"] != previous
                or not hmac.compare_digest(row["event_hash"], self._digest(previous, event))
            ):
                valid = False
            previous = row["event_hash"]
        selected = all_rows[-limit:]
        return {
            "chain_valid": valid,
            "total_events": len(all_rows),
            "events": [
                {**{field: row[field] for field in FIELDS},
                 "prev_hash": row["prev_hash"], "event_hash": row["event_hash"]}
                for row in selected
            ],
        }
