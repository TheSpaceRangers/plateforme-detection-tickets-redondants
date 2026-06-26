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


def test_ingest_synthetic_tickets_counts_duplicate_external_ticket_id_as_ignored() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(), _synthetic_ticket()))
    repository = _UniqueExternalIdRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result.extracted_count == 2
    assert result.stored_count == 1
    assert result.ignored_count == 1
    assert result.status == "completed"


def test_ingest_synthetic_tickets_counts_new_ticket_as_stored_not_ignored() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(external_ticket_id="syn-new-001"),))
    repository = _UniqueExternalIdRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result.extracted_count == 1
    assert result.stored_count == 1
    assert result.ignored_count == 0
    assert result.status == "completed"


def test_ingest_synthetic_tickets_propagates_repository_database_errors_fail_closed() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(external_ticket_id="syn-db-error-002"),))
    repository = MagicMock()
    repository.save_many.side_effect = RuntimeError("synthetic database unavailable")
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    with pytest.raises(RuntimeError, match="synthetic database unavailable"):
        service.ingest_synthetic_tickets()

    # Assert
    repository.save_many.assert_called_once()


def test_ingest_synthetic_tickets_sanitizes_phone_pii_before_repository_save() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(category="callback 0612345678"),))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert repository.tickets[0].category == "callback [PHONE]"


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
            None,
            None,
            None,
        )
    ]


@pytest.mark.parametrize(
    ("field", "value", "expected_value"),
    [
        ("category", "owner synthetic@example.test", "owner [EMAIL]"),
        ("external_ticket_id", "synthetic@example.test", "[EMAIL]"),
    ],
)
def test_synthetic_email_in_residual_scan_fields_is_sanitized_before_storage(
    field: str,
    value: str,
    expected_value: str,
) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(**{field: value}),))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    stored_ticket = repository.tickets[0]
    assert getattr(stored_ticket, field) == expected_value
    assert "@" not in getattr(stored_ticket, field)


def test_ingestion_pre_sanitizes_scanned_fields_before_ml_preprocessing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(
        tickets=(
            _synthetic_ticket(
                external_ticket_id="qa.person@example.test",
                summary="Contact <qa.person@example.test>",
                details="<p>Owner qa.person&#64;example.test</p>",
                status="mailto:qa.person@example.test",
                priority="owner (qa.person@example.test)",
                category="qa.o'neil/team_test-alpha@example.engineering",
            ),
        )
    )
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)
    captured_records: list[dict[str, object]] = []

    def _record_preprocessed_dataset(tickets: object, agent_id_policy: object) -> list[dict[str, object]]:
        captured_records.extend(dict(ticket) for ticket in tickets)  # type: ignore[arg-type]
        return [
            {field: value for field, value in record.items() if field != "agent_id"}
            for record in captured_records
        ]

    monkeypatch.setattr(ingestion_module, "build_preprocessed_ticket_dataset", _record_preprocessed_dataset)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert captured_records == [
        {
            "external_ticket_id": "[EMAIL]",
            "summary": "Contact [EMAIL]",
            "details": "Owner [EMAIL]",
            "status": "[EMAIL]",
            "priority": "owner ([EMAIL])",
            "category": "[EMAIL]",
            "ticket_created_at": None,
            "ticket_updated_at": None,
            "ticket_closed_at": None,
            "agent_id": "synthetic-agent-001",
        }
    ]


def test_ingestion_still_calls_final_residual_scan_after_preprocessing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(summary="Contact qa.person@example.test"),))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)
    calls: list[tuple[list[dict[str, object]], tuple[str, ...]]] = []

    def _record_residual_scan(records: list[dict[str, object]], fields: tuple[str, ...]) -> None:
        calls.append((records, fields))

    monkeypatch.setattr(ingestion_module, "assert_no_residual_pii", _record_residual_scan)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert len(calls) == 1
    assert calls[0][1] == ingestion_module.RESIDUAL_PII_TEXT_FIELDS


def test_ingestion_pipeline_runs_provider_sanitizer_ml_preprocessing_then_residual_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(summary="Contact qa.person@example.test"),))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)
    observed_steps: list[str] = []

    original_provider_sanitizer = ingestion_module.sanitize_provider_text
    original_preprocessor = ingestion_module.build_preprocessed_ticket_dataset
    original_residual_scan = ingestion_module.assert_no_residual_pii

    def _record_provider_sanitizer(value: object | None) -> str:
        observed_steps.append("provider")
        return original_provider_sanitizer(value)

    def _record_ml_preprocessing(tickets: object, agent_id_policy: object) -> list[dict[str, object]]:
        observed_steps.append("ml_preprocessing")
        return original_preprocessor(tickets, agent_id_policy=agent_id_policy)  # type: ignore[arg-type]

    def _record_residual_scan(records: list[dict[str, object]], fields: tuple[str, ...]) -> None:
        observed_steps.append("residual_scan")
        original_residual_scan(records, fields=fields)

    monkeypatch.setattr(ingestion_module, "sanitize_provider_text", _record_provider_sanitizer)
    monkeypatch.setattr(ingestion_module, "build_preprocessed_ticket_dataset", _record_ml_preprocessing)
    monkeypatch.setattr(ingestion_module, "assert_no_residual_pii", _record_residual_scan)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert observed_steps[:6] == ["provider"] * 6
    assert observed_steps[6:] == ["ml_preprocessing", "residual_scan"]
    assert repository.tickets[0].summary == "Contact [EMAIL]"


def test_ingestion_does_not_save_when_final_residual_scan_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(summary="Synthetic clean summary"),))
    repository = MagicMock()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    def _fail_residual_scan(records: list[dict[str, object]], fields: tuple[str, ...]) -> None:
        raise RuntimeError("synthetic residual scan failure")

    monkeypatch.setattr(ingestion_module, "assert_no_residual_pii", _fail_residual_scan)

    # Act
    with pytest.raises(RuntimeError, match="synthetic residual scan failure"):
        service.ingest_synthetic_tickets()

    # Assert
    repository.save_many.assert_not_called()


def test_ingestion_fails_closed_when_provider_sanitizer_is_no_op_before_final_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(category="owner qa.person@example.test"),))
    repository = MagicMock()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    monkeypatch.setattr(ingestion_module, "sanitize_provider_text", lambda value: str(value or ""))

    # Act
    with pytest.raises(PiiResidualError) as error:
        service.ingest_synthetic_tickets()

    # Assert
    assert "field=category" in str(error.value)
    assert "categories=email" in str(error.value)
    assert "qa.person@example.test" not in str(error.value)
    repository.save_many.assert_not_called()


def test_hmac_pseudonym_phone_like_digest_is_not_scanned_as_residual_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(agent_id="synthetic-agent-private"),))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)
    phone_like_hmac_digest = "hmac_sha256:0612345678abcdef0612345678abcdef0612345678abcdef0612345678abcdef"
    guarded_record_with_phone_like_pseudonym = {
        "external_ticket_id": "syn-unit-hmac-phone-like",
        "summary": "Synthetic clean summary",
        "details": "Synthetic clean details",
        "status": "open",
        "priority": "low",
        "category": "network",
        "agent_id_pseudonym": phone_like_hmac_digest,
    }
    monkeypatch.setattr(
        ingestion_module,
        "build_preprocessed_ticket_dataset",
        lambda tickets, agent_id_policy: [guarded_record_with_phone_like_pseudonym],
    )

    # Act
    result = service.ingest_tickets(include_agent_pseudonym=True)

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert repository.tickets[0].agent_id_pseudonym == phone_like_hmac_digest


def test_synthetic_phone_pii_in_non_pseudonymized_text_field_is_masked_before_storage() -> None:
    # Arrange
    extractor = SyntheticTicketExtractor(tickets=(_synthetic_ticket(category="callback 0612345678"),))
    repository = InMemoryTicketRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_synthetic_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert repository.tickets[0].category == "callback [PHONE]"


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
        self.rowcount = 0

    def __enter__(self) -> "_RecordingCursor":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def executemany(self, statement: str, values: Sequence[tuple[Any, ...]]) -> None:
        self.statement = statement
        self.values = list(values)

    def execute(self, statement: str, value: tuple[Any, ...] | None = None) -> None:
        self.statement = statement
        if value is None:
            self.rowcount = 0
            return
        self.values.append(value)
        self.rowcount = 1

    def fetchone(self) -> tuple[bool]:
        return (True,)


class _UniqueExternalIdRepository:
    def __init__(self) -> None:
        self._seen_external_ids: set[str] = set()
        self.tickets: list[StoredCleanTicket] = []

    def save_many(self, tickets: Sequence[StoredCleanTicket]) -> int:
        stored_count = 0
        for ticket in tickets:
            if ticket.external_ticket_id in self._seen_external_ids:
                continue
            self._seen_external_ids.add(ticket.external_ticket_id)
            self.tickets.append(ticket)
            stored_count += 1
        return stored_count


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
