"""Fail-closed HaloPSA extraction configuration."""

from __future__ import annotations

from dataclasses import dataclass

SAFE_DEFAULT_PAGE_SIZE = 1
MAX_PAGE_SIZE = 5
DEFAULT_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_TOKEN_PATH = "/auth/token"
DEFAULT_TICKETS_PATH = "/api/Tickets"


class InvalidHaloPsaConfigurationError(ValueError):
    """Raised when HaloPSA configuration is missing or incomplete."""


@dataclass(frozen=True, slots=True)
class HaloPsaExtractorConfig:
    """Injected HaloPSA extraction configuration without direct .env loading."""

    base_url: str
    client_id: str
    client_secret: str
    tenant: str
    scope: str = ""
    page_size: int = SAFE_DEFAULT_PAGE_SIZE
    request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    token_path: str = DEFAULT_TOKEN_PATH
    tickets_path: str = DEFAULT_TICKETS_PATH

    def __post_init__(self) -> None:
        """Normalize bounded operational settings without exposing sensitive values."""

        object.__setattr__(self, "page_size", min(self.page_size, MAX_PAGE_SIZE))

    def validate(self) -> None:
        """Fail closed when a required setting is absent before any usage."""

        missing_fields = [
            field_name
            for field_name, value in (
                ("base_url", self.base_url),
                ("client_id", self.client_id),
                ("client_secret", self.client_secret),
                ("tenant", self.tenant),
            )
            if not isinstance(value, str) or not value.strip()
        ]
        if missing_fields:
            raise InvalidHaloPsaConfigurationError(
                f"Incomplete HaloPSA extractor configuration: {', '.join(missing_fields)}"
            )
        if self.page_size <= 0:
            raise InvalidHaloPsaConfigurationError("HaloPSA page_size must be strictly positive")
        if self.request_timeout_seconds <= 0:
            raise InvalidHaloPsaConfigurationError("HaloPSA request timeout must be strictly positive")
        if self.max_retries < 0:
            raise InvalidHaloPsaConfigurationError("HaloPSA max_retries must be zero or positive")
        if not self.token_path.strip():
            raise InvalidHaloPsaConfigurationError("HaloPSA token_path must be configured")
        if not self.tickets_path.strip():
            raise InvalidHaloPsaConfigurationError("HaloPSA tickets_path must be configured")

    def redacted_summary(self) -> str:
        """Return a non-sensitive summary suitable for technical diagnostics."""

        self.validate()
        return f"HaloPsaExtractorConfig(page_size={self.page_size}, max_retries={self.max_retries})"
