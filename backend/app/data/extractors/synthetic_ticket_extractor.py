"""Synthetic ticket extractor used without any HaloPSA API call."""

from __future__ import annotations

from collections.abc import Iterable

from backend.app.data.extractors.ticket_extractor import TicketExtractor
from backend.app.schemas.tickets import IncomingSyntheticTicket


class SyntheticTicketExtractor:
    """Extractor returning controlled synthetic tickets for test ingestion."""

    def __init__(self, tickets: Iterable[IncomingSyntheticTicket] | None = None) -> None:
        self._tickets = tuple(tickets or _default_synthetic_tickets())

    def extract(self) -> Iterable[IncomingSyntheticTicket]:
        """Return synthetic tickets only; no network or HaloPSA call is performed."""

        return self._tickets


def _default_synthetic_tickets() -> tuple[IncomingSyntheticTicket, ...]:
    """Build non-identifying synthetic tickets for local pipeline checks."""

    return (
        IncomingSyntheticTicket(
            external_ticket_id="syn-001",
            summary="Password reset workflow unavailable",
            details="Synthetic user cannot complete the password reset flow.",
            status="open",
            priority="medium",
            category="identity_access",
            agent_id="synthetic-agent-001",
        ),
        IncomingSyntheticTicket(
            external_ticket_id="syn-002",
            summary="VPN connection intermittently fails",
            details="Synthetic endpoint reports intermittent VPN tunnel drops.",
            status="open",
            priority="low",
            category="network",
            agent_id="synthetic-agent-002",
        ),
    )
