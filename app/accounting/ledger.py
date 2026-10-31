"""Ephemeral demo ledger, never a substitute for cloud billing reconciliation."""

import asyncio
from decimal import Decimal

from pydantic import BaseModel


class UsageSummary(BaseModel):
    completed_requests: int
    total_estimated_usd: Decimal
    basis: str = "illustrative_per_request_not_billed"


class UsageLedger:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._count = 0
        self._cost = Decimal("0")

    async def record(self, estimated_cost: Decimal) -> None:
        async with self._lock:
            self._count += 1
            self._cost += estimated_cost

    async def summary(self) -> UsageSummary:
        async with self._lock:
            return UsageSummary(
                completed_requests=self._count,
                total_estimated_usd=self._cost,
            )
