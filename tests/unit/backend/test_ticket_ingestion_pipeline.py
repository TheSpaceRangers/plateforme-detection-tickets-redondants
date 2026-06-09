"""Synthetic ingestion/storage tests without real HaloPSA or PostgreSQL access."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.app.data.extractors.synthetic_ticket_extractor import SyntheticTicketExtractor
from backend.app.db.repositories.ticket_repository import InMemoryTicketRepository, PostgresTicketRepository
from backend.app.schemas.tickets import IncomingSyntheticTicket, IngestionResult, StoredCleanTicket
from backend.app.services import ticket_ingestion_service as ingestion_module
from backend.app.services.ticket_ingestion_service import TicketIngestionService
from ml.src.preprocessing.pii import PiiResidualError
from ml.src.preprocessing.pseudonymization import DEFAULT_SECRET_ENV_VAR, MissingPseudonymizationSecretError


def _synthetic_ticket(**overrides: object) -> IncomingSyntheticTicket:
    values: dict[str, object] = {
        "external_ticket_id": "syn-unit-001",
        "summary": "Synthetic workstation cannot open the portal",
        "details": "Synthetic endpoint receives a controlled access error.",
        "status": "open",
        "priority": "medium",
        "category": "identity_access",
        "agent_id": "synthetic-agent-001",
    }
    values.update(overrides)
    return IncomingSyntheticTicket(**values)  # type: ignore[arg-type]


def test_ingest_synthetic_tickets_stores_only_clean_tickets_with_matching_counts() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(), _synthetic_ticket(external_ticket_id="syn-unit-002")))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=2, stored_count=2, status="completed")
    assert result.stored_count == result.extracted_count
    assert all(isinstance(ticket, StoredCleanTicket) for ticket in repository.tickets)
    assert all(not hasattr(ticket, "agent_id") for ticket in repository.tickets)


def test_ingest_synthetic_tickets_blocks_residual_pii_before_repository_save() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(category="owner synthetic@example.test"),))
    repository = MagicMock()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    with pytest.raises(PiiResidualError):
        service.ingest_synthetic_tickets()

    # Assert
    repository.save_many.assert_not_called()


@pytest.mark.parametrize("forbidden_field", ["raw_json", "raw_payload", "payload", "halopsa_payload"])
def test_stored_clean_ticket_rejects_raw_payload_fields_before_repository(forbidden_field: str) -> None:
    # Arrange
    guarded_record: dict[str, object] = {
        "external_ticket_id": "syn-unit-raw",
        "summary": "Synthetic clean summary",
        "details": "Synthetic clean details",
        "status": "open",
        "priority": "low",
        "category": "network",
        forbidden_field: {"source": "synthetic"},
    }

    # Act
    with pytest.raises(ValueError, match="Forbidden storage fields"):
        StoredCleanTicket.from_guarded_mapping(guarded_record)

    # Assert
    assert forbidden_field in guarded_record


def test_ingestion_rejects_raw_payload_before_repository_save(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(),))
    repository = MagicMock()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    guarded_record_with_raw_payload = {
        "external_ticket_id": "syn-unit-raw-service",
        "summary": "Synthetic clean summary",
        "details": "Synthetic clean details",
        "status": "open",
        "priority": "low",
        "category": "network",
        "raw_json": {"source": "synthetic"},
    }
    monkeypatch.setattr(
        ingestion_module,
        "build_preprocessed_ticket_dataset",
        lambda tickets, agent_id_policy: [guarded_record_with_raw_payload],
    )

    # Act
    with pytest.raises(ValueError, match="Forbidden storage fields"):
        service.ingest_synthetic_tickets()

    # Assert
    repository.save_many.assert_not_called()


def test_repository_boundary_rejects_raw_mapping_without_durable_storage() -> None:
    # Arrange
    repository = InMemoryTicketRepository()
    raw_mapping = {"payload": {"source": "synthetic"}}

    # Act
    with pytest.raises(TypeError, match="StoredCleanTicket"):
        repository.save_many([raw_mapping])  # type: ignore[list-item]

    # Assert
    assert repository.tickets == ()


def test_agent_id_is_excluded_by_default_from_stored_objects_and_postgres_mapping() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(agent_id="synthetic-agent-private"),))
    memory_repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=memory_repository)
    cursor = _RecordingCursor()
    postgres_repository = PostgresTicketRepository(connection_factory=lambda: _RecordingConnection(cursor))

    # Act
    service.ingest_synthetic_tickets()
    postgres_repository.save_many(memory_repository.tickets)

    # Assert
    stored_ticket = memory_repository.tickets[0]
    assert not hasattr(stored_ticket, "agent_id")
    assert stored_ticket.agent_id_pseudonym is None
    inserted_columns = _inserted_columns(cursor.statement)
    assert "agent_id" not in inserted_columns
    assert "agent_id_pseudonym" in inserted_columns
    assert cursor.values == [
        (
            stored_ticket.external_ticket_id,
            stored_ticket.summary,
            stored_ticket.details,
            stored_ticket.status,
            stored_ticket.priority,
            stored_ticket.category,
            None,
        )
    ]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("category", "owner synthetic@example.test"),
        ("external_ticket_id", "synthetic@example.test"),
    ],
)
def test_residual_pii_in_non_sanitized_fields_blocks_before_storage(field: str, value: str) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(**{field: value}),))
    repository = MagicMock()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    with pytest.raises(PiiResidualError) as error:
        service.ingest_synthetic_tickets()

    # Assert
    assert f"field={field}" in str(error.value)
    repository.save_many.assert_not_called()


def test_services_extractors_and_repositories_do_not_share_state() -> None:
    # Arrange
    extractor_one = SyntheticTicketExtractor(tickets=(_synthetic_ticket(external_ticket_id="syn-isolated-001"),))
    extractor_two = SyntheticTicketExtractor(tickets=(_synthetic_ticket(external_ticket_id="syn-isolated-002"),))
    repository_one = InMemoryTicketRepository()
    repository_two = InMemoryTicketRepository()
    service_one = TicketIngestionService(extractor=extractor_one, repository=repository_one)
    service_two = TicketIngestionService(extractor=extractor_two, repository=repository_two)

    # Act
    result_one = service_one.ingest_synthetic_tickets()
    result_two = service_two.ingest_synthetic_tickets()

    # Assert
    assert result_one == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert result_two == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert repository_one.tickets != repository_two.tickets
    assert repository_one.tickets[0].external_ticket_id == "syn-isolated-001"
    assert repository_two.tickets[0].external_ticket_id == "syn-isolated-002"


def test_hmac_pseudonymization_fails_closed_without_runtime_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.delenv(DEFAULT_SECRET_ENV_VAR, raising=False)
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(agent_id="synthetic-agent-private"),))
    repository = MagicMock()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    with pytest.raises(MissingPseudonymizationSecretError) as error:
        service.ingest_synthetic_tickets(include_agent_pseudonym=True)

    # Assert
    assert DEFAULT_SECRET_ENV_VAR in str(error.value)
    assert "synthetic-agent-private" not in str(error.value)
    repository.save_many.assert_not_called()


class _RecordingCursor:
    def __init__(self) -> None:
        self.statement = ""
        self.values: list[tuple[Any, ...]] = []

    def __enter__(self) -> "_RecordingCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def executemany(self, statement: str, values: Sequence[tuple[Any, ...]]) -> None:
        self.statement = statement
        self.values = list(values)


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
