"""Explicit environment configuration; no provider is contacted on startup."""

import os
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlparse


def enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    enable_live_execution: bool = False
    enable_local_routing: bool = True
    enable_azure_routing: bool = False
    control_plane_api_key: str = ""
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:3b"
    azure_endpoint: str = ""
    azure_deployment: str = ""
    azure_api_key: str = ""
    azure_api_version: str = "2024-10-21"
    # Rates are illustrative per-request estimates, NOT provider prices or actual bills.
    local_estimated_usd: Decimal = Decimal("0.005")
    azure_estimated_usd: Decimal = Decimal("0.03")

    def __post_init__(self) -> None:
        if self.local_estimated_usd < 0 or self.azure_estimated_usd < 0:
            raise ValueError("Cost estimates must be nonnegative")
        if self.enable_live_execution and len(self.control_plane_api_key) < 24:
            raise ValueError("Live execution requires CONTROL_PLANE_API_KEY of at least 24 chars")
        if self.enable_live_execution and self.enable_azure_routing:
            parts = urlparse(self.azure_endpoint)
            if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
                raise ValueError("Live Azure requests require a valid HTTPS endpoint")
            if not self.azure_deployment or not self.azure_api_key:
                raise ValueError("Azure execution requires deployment and API key")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            enable_live_execution=enabled("ENABLE_LIVE_EXECUTION"),
            enable_local_routing=enabled("ENABLE_LOCAL_ROUTING", True),
            enable_azure_routing=enabled("ENABLE_AZURE_ROUTING"),
            control_plane_api_key=os.getenv("CONTROL_PLANE_API_KEY", ""),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            local_estimated_usd=Decimal(os.getenv("LOCAL_ESTIMATED_USD_PER_REQUEST", "0.005")),
            azure_estimated_usd=Decimal(os.getenv("AZURE_ESTIMATED_USD_PER_REQUEST", "0.03")),
        )
