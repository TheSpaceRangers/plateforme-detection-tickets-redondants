"""Ticket repository abstractions and storage implementations."""

from __future__ import annotations

from pathlib import Path
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

    def __init__(self, connection_factory: Callable[[], Any], *, initialize_schema: bool = False) -> None:
        self._connection_factory = connection_factory
        self._initialize_schema = initialize_schema
        self._schema_initialized = False

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
                agent_id_pseudonym,
                ticket_created_at,
                ticket_updated_at,
                ticket_closed_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (external_ticket_id) DO UPDATE SET
                priority = EXCLUDED.priority,
                category = EXCLUDED.category,
                agent_id_pseudonym = EXCLUDED.agent_id_pseudonym,
                ticket_created_at = COALESCE(EXCLUDED.ticket_created_at, clean_tickets.ticket_created_at),
                ticket_updated_at = COALESCE(EXCLUDED.ticket_updated_at, clean_tickets.ticket_updated_at),
                ticket_closed_at = COALESCE(EXCLUDED.ticket_closed_at, clean_tickets.ticket_closed_at)
            RETURNING (xmax = 0) AS inserted
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
                ticket.ticket_created_at,
                ticket.ticket_updated_at,
                ticket.ticket_closed_at,
            )
            for ticket in tickets
        ]

        connection = self._connection_factory()
        with connection:
            with connection.cursor() as cursor:
                self._ensure_schema(cursor)
                stored_count = 0
                for value in values:
                    cursor.execute(insert_statement, value)
                    row = cursor.fetchone()
                    stored_count += 1 if row and row[0] else 0
        return stored_count

    def _ensure_schema(self, cursor: Any) -> None:
        """Create the allowlisted clean ticket table when explicitly requested."""

        if not self._initialize_schema or self._schema_initialized:
            return
        cursor.execute(_schema_sql())
        for migration_sql in _migration_sql_statements():
            cursor.execute(migration_sql)
        self._schema_initialized = True


def _schema_sql() -> str:
    """Load the clean-ticket-only PostgreSQL schema bundled with backend."""

    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def _migration_sql_statements() -> tuple[str, ...]:
    """Load idempotent clean ticket schema migrations in filename order."""

    migrations_path = Path(__file__).resolve().parents[1] / "migrations"
    if not migrations_path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8") for path in sorted(migrations_path.glob("*.sql")))


def _assert_clean_ticket_sequence(tickets: Sequence[StoredCleanTicket]) -> None:
    """Reject raw mappings or objects outside the sanitized storage schema."""

    for ticket in tickets:
        if not isinstance(ticket, StoredCleanTicket):
            raise TypeError("Ticket repositories accept StoredCleanTicket instances only")
