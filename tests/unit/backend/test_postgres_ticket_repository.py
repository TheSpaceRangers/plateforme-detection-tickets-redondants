"""Unit tests for explicit PostgreSQL ticket repository safety boundaries."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import fields
from datetime import datetime, timezone
from typing import Any

import pytest

from backend.app.db.postgres_config import PostgresConfigurationError, PostgresConnectionConfig
from backend.app.db.repositories.ticket_repository import PostgresTicketRepository
from backend.app.schemas.tickets import StoredCleanTicket


ALLOWED_CLEAN_COLUMNS = (
    "external_ticket_id",
    "summary",
    "details",
    "status",
    "priority",
    "category",
    "agent_id_pseudonym",
    "ticket_created_at",
    "ticket_updated_at",
    "ticket_closed_at",
)
FORBIDDEN_RAW_COLUMNS = ("agent_id", "raw_json", "raw_payload", "payload", "halopsa_payload")


def _complete_postgres_env(**overrides: str | None) -> dict[str, str]:
    values = {
        "POSTGRES_ENABLE_WRITE": "true",
        "POSTGRES_HOST": "synthetic-host-secret-value",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "synthetic-db-secret-value",
        "POSTGRES_USER": "synthetic-user-secret-value",
        "POSTGRES_PASSWORD": "synthetic-password-secret-value",
    }
    for key, value in overrides.items():
        if value is None:
            values.pop(key, None)
        else:
            values[key] = value
    return values


def test_postgres_connection_config_requires_explicit_write_enable_before_storage() -> None:
    # Arrange
    env = _complete_postgres_env(POSTGRES_ENABLE_WRITE="false")

    # Act
    with pytest.raises(PostgresConfigurationError) as error:
        PostgresConnectionConfig.from_env(env)

    # Assert
    assert "explicitly enabled" in str(error.value)
    assert not any(secret_value in str(error.value) for secret_value in env.values())


def test_postgres_connection_config_accepts_complete_component_config_when_enabled() -> None:
    # Arrange
    env = _complete_postgres_env()

    # Act
    config = PostgresConnectionConfig.from_env(env)

    # Assert
    assert config.connection_kwargs() == {
        "host": "synthetic-host-secret-value",
        "port": 5432,
        "dbname": "synthetic-db-secret-value",
        "user": "synthetic-user-secret-value",
        "password": "synthetic-password-secret-value",
    }


@pytest.mark.parametrize("missing_key", ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"])
def test_postgres_connection_config_fails_closed_for_incomplete_config_without_secret_values(missing_key: str) -> None:
    # Arrange
    env = _complete_postgres_env(**{missing_key: None})
    forbidden_secret_values = set(env.values()) - {"true", "5432"}

    # Act
    with pytest.raises(PostgresConfigurationError) as error:
        PostgresConnectionConfig.from_env(env)

    # Assert
    error_message = str(error.value)
    assert missing_key in error_message
    assert not any(secret_value in error_message for secret_value in forbidden_secret_values)


def test_postgres_connection_config_rejects_invalid_port_without_raw_value_leak() -> None:
    # Arrange
    env = _complete_postgres_env(POSTGRES_PORT="not-a-secret-port-value")

    # Act
    with pytest.raises(PostgresConfigurationError) as error:
        PostgresConnectionConfig.from_env(env)

    # Assert
    assert "POSTGRES_PORT must be an integer" == str(error.value)
    assert "not-a-secret-port-value" not in str(error.value)


def test_postgres_repository_inserts_only_allowlisted_clean_ticket_columns() -> None:
    # Arrange
    created_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    updated_at = datetime(2026, 1, 3, 3, 4, 5, tzinfo=timezone.utc)
    closed_at = datetime(2026, 1, 4, 3, 4, 5, tzinfo=timezone.utc)
    ticket = StoredCleanTicket(
        external_ticket_id="syn-001",
        summary="Synthetic summary",
        details="Synthetic details",
        status="open",
        priority="medium",
        category="identity_access",
        agent_id_pseudonym="hmac_sha256:syntheticdigest",
        ticket_created_at=created_at,
        ticket_updated_at=updated_at,
        ticket_closed_at=closed_at,
    )
    cursor = _RecordingCursor()
    repository = PostgresTicketRepository(connection_factory=lambda: _RecordingConnection(cursor))

    # Act
    stored_count = repository.save_many((ticket,))

    # Assert
    assert stored_count == 1
    assert _inserted_columns(cursor.statement) == ALLOWED_CLEAN_COLUMNS
    assert not any(raw_column in _inserted_columns(cursor.statement) for raw_column in FORBIDDEN_RAW_COLUMNS)
    assert cursor.values == [
        (
            "syn-001",
            "Synthetic summary",
            "Synthetic details",
            "open",
            "medium",
            "identity_access",
            "hmac_sha256:syntheticdigest",
            created_at,
            updated_at,
            closed_at,
        )
    ]
    assert tuple(field.name for field in fields(ticket)) == ALLOWED_CLEAN_COLUMNS


def test_postgres_repository_ignores_duplicate_external_ticket_id_without_unique_violation() -> None:
    # Arrange
    duplicate_ticket = StoredCleanTicket(
        external_ticket_id="syn-duplicate-001",
        summary="Synthetic duplicate summary",
        details="Synthetic duplicate details",
        status="open",
        priority="medium",
        category="identity_access",
        agent_id_pseudonym=None,
    )
    cursor = _RecordingCursor(rowcounts=(1, 0))
    repository = PostgresTicketRepository(connection_factory=lambda: _RecordingConnection(cursor))

    # Act
    stored_count = repository.save_many((duplicate_ticket, duplicate_ticket))

    # Assert
    assert stored_count == 1
    assert len(cursor.values) == 2
    assert "ON CONFLICT (external_ticket_id) DO UPDATE SET" in cursor.statement
    assert "ticket_created_at = COALESCE(EXCLUDED.ticket_created_at, clean_tickets.ticket_created_at)" in cursor.statement


def test_postgres_repository_propagates_non_duplicate_database_errors() -> None:
    # Arrange
    ticket = StoredCleanTicket(
        external_ticket_id="syn-db-error-001",
        summary="Synthetic database error summary",
        details="Synthetic database error details",
        status="open",
        priority="low",
        category="network",
        agent_id_pseudonym=None,
    )
    database_error = RuntimeError("synthetic database unavailable")
    cursor = _RecordingCursor(error=database_error)
    repository = PostgresTicketRepository(connection_factory=lambda: _RecordingConnection(cursor))

    # Act
    with pytest.raises(RuntimeError, match="synthetic database unavailable"):
        repository.save_many((ticket,))

    # Assert
    assert cursor.values == []


def test_postgres_repository_rejects_raw_payload_mapping_before_connection_is_opened() -> None:
    # Arrange
    connection_factory = _FailingConnectionFactory()
    repository = PostgresTicketRepository(connection_factory=connection_factory)
    raw_ticket = {"external_ticket_id": "syn-raw", "payload": {"source": "synthetic"}}

    # Act
    with pytest.raises(TypeError, match="StoredCleanTicket"):
        repository.save_many([raw_ticket])  # type: ignore[list-item]

    # Assert
    assert connection_factory.called is False


def test_schema_sql_contains_clean_allowlist_without_raw_payload_columns() -> None:
    # Arrange
    schema_path = "backend/app/db/schema.sql"

    # Act
    schema_sql = open(schema_path, encoding="utf-8").read()

    # Assert
    assert "CREATE TABLE IF NOT EXISTS clean_tickets" in schema_sql
    for column in ALLOWED_CLEAN_COLUMNS:
        assert re.search(rf"\b{column}\b", schema_sql) is not None
    for raw_column in FORBIDDEN_RAW_COLUMNS:
        assert re.search(rf"\b{raw_column}\b", schema_sql) is None


def test_business_dates_migration_is_idempotent_and_nullable() -> None:
    # Arrange
    migration_path = "backend/app/db/migrations/001_add_ticket_business_dates.sql"

    # Act
    migration_sql = open(migration_path, encoding="utf-8").read()

    # Assert
    for column in ("ticket_created_at", "ticket_updated_at", "ticket_closed_at"):
        assert re.search(rf"ADD COLUMN IF NOT EXISTS {column} TIMESTAMPTZ NULL", migration_sql) is not None


class _FailingConnectionFactory:
    def __init__(self) -> None:
        self.called = False

    def __call__(self) -> object:
        self.called = True
        raise AssertionError("repository must reject raw payloads before opening PostgreSQL connections")


class _RecordingCursor:
    def __init__(self, *, rowcounts: Sequence[int] = (1,), error: Exception | None = None) -> None:
        self.statement = ""
        self.values: list[tuple[Any, ...]] = []
        self.rowcount = 0
        self._rowcounts = tuple(rowcounts)
        self._error = error

    def __enter__(self) -> "_RecordingCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def executemany(self, statement: str, values: Sequence[tuple[Any, ...]]) -> None:
        self.statement = statement
        self.values = list(values)

    def execute(self, statement: str, value: tuple[Any, ...] | None = None) -> None:
        if self._error is not None:
            raise self._error
        self.statement = statement
        if value is None:
            self.rowcount = 0
            return
        self.values.append(value)
        index = len(self.values) - 1
        self.rowcount = self._rowcounts[index] if index < len(self._rowcounts) else self._rowcounts[-1]

    def fetchone(self) -> tuple[bool]:
        index = len(self.values) - 1
        inserted = self._rowcounts[index] if index < len(self._rowcounts) else self._rowcounts[-1]
        return (bool(inserted),)


class _RecordingConnection:
    def __init__(self, cursor: _RecordingCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> "_RecordingConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def cursor(self) -> _RecordingCursor:
        return self._cursor


def _inserted_columns(statement: str) -> tuple[str, ...]:
    match = re.search(r"clean_tickets\s*\((.*?)\)\s*VALUES", statement, flags=re.DOTALL | re.IGNORECASE)
    assert match is not None
    return tuple(column.strip() for column in match.group(1).split(","))
