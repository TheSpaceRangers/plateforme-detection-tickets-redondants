"""Mockable HaloPSA client boundary with no network transport by default."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Protocol

from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig


class NetworkTransportNotConfiguredError(RuntimeError):
    """Raised when HaloPSA extraction is attempted without injected transport."""


class HaloPsaTransport(Protocol):
    """Injected transport abstraction for future HaloPSA API calls."""

    def fetch_tickets(self, config: HaloPsaExtractorConfig) -> Iterable[Mapping[str, object]]:
        """Fetch source ticket mappings through an implementation supplied by tests or integration code."""


class NoopHaloPsaTransport:
    """Default transport that blocks network execution explicitly."""

    def fetch_tickets(self, config: HaloPsaExtractorConfig) -> Iterable[Mapping[str, object]]:
        """Reject extraction attempts instead of performing any network call."""

        raise NetworkTransportNotConfiguredError("HaloPSA network transport must be injected explicitly")


class HaloPsaTicketClient:
    """Small client wrapper that validates configuration before delegating to an injected transport."""

    def __init__(self, config: HaloPsaExtractorConfig, transport: HaloPsaTransport | None = None) -> None:
        config.validate()
        self._config = config
        self._transport = transport or NoopHaloPsaTransport()

    def fetch_ticket_payloads(self) -> Iterable[Mapping[str, object]]:
        """Return transient payload mappings from the injected transport only."""

        self._config.validate()
        return self._transport.fetch_tickets(self._config)
