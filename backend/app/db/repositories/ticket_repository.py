"""Ticket repository abstractions and storage implementations."""

from __future__ import annotations

from typing import Any, Callable, Protocol, Sequence

from backend.app.schemas.tickets import StoredCleanTicket


class TicketRepository(Protocol):
    """Mockable persistence boundary for sanitized ticket records only."""

    def save_many(self, tickets: Sequence[StoredCleanTicket]) -> int:
        """Persist sanitized tickets and return the number of stored records."""


class InMemoryTicketRepository:
    """Test repository retaining only sanitized ticket dataclasses in memory."""

    def __init__(self) -> None:
        self._tickets: list[StoredCleanTicket] = []

    @property
    def tickets(self) -> tuple[StoredCleanTicket, ...]:
        """Return sanitized tickets stored during tests."""

        return tuple(self._tickets)

    def save_many(self, tickets: Sequence[StoredCleanTicket]) -> int:
        """Persist sanitized tickets in memory for tests."""

        _assert_clean_ticket_sequence(tickets)
        self._tickets.extend(tickets)
        return len(tickets)

    def clear(self) -> None:
        """Remove sanitized in-memory tickets between isolated tests."""

        self._tickets.clear()


class PostgresTicketRepository:
    """PostgreSQL repository persisting allowlisted sanitized ticket columns only."""

    def __init__(self, connection_factory: Callable[[], Any]) -> None:
        self._connection_factory = connection_factory

    def save_many(self, tickets: Sequence[StoredCleanTicket]) -> int:
        """Persist sanitized tickets without accepting raw JSON payloads."""

        _assert_clean_ticket_sequence(tickets)
        if not tickets:
            return 0

        insert_statement = """
            INSERT INTO clean_tickets (
                external_ticket_id,
                summary,
                details,
                status,
                priority,
                category,
                agent_id_pseudonym
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = [
            (
                ticket.external_ticket_id,
                ticket.summary,
                ticket.details,
                ticket.status,
                ticket.priority,
                ticket.category,
                ticket.agent_id_pseudonym,
            )
            for ticket in tickets
        ]

        connection = self._connection_factory()
        with connection:
            with connection.cursor() as cursor:
                cursor.executemany(insert_statement, values)
        return len(tickets)


def _assert_clean_ticket_sequence(tickets: Sequence[StoredCleanTicket]) -> None:
    """Reject raw mappings or objects outside the sanitized storage schema."""

    for ticket in tickets:
        if not isinstance(ticket, StoredCleanTicket):
            raise TypeError("Ticket repositories accept StoredCleanTicket instances only")
