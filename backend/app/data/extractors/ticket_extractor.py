"""Ticket extraction boundary independent from any source provider."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from backend.app.schemas.tickets import IncomingTicket


class TicketExtractor(Protocol):
    """Boundary abstraction for ticket extraction sources."""

    def extract(self) -> Iterable[IncomingTicket]:
        """Return ticket-like records without persisting raw source payloads."""
