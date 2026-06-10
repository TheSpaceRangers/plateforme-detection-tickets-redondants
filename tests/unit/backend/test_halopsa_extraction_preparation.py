"""Unit tests for HaloPSA extraction preparation without real network or secrets."""

from __future__ import annotations

import builtins
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from backend.app.data.extractors.halopsa_client import (
    HaloPsaTicketClient,
    NetworkTransportNotConfiguredError,
)
from backend.app.data.extractors.halopsa_config import (
    HaloPsaExtractorConfig,
    InvalidHaloPsaConfigurationError,
)
from backend.app.data.extractors.halopsa_ticket_extractor import (
    HaloPsaTicketExtractor,
    InvalidHaloPsaTicketPayloadError,
)
from backend.app.schemas.tickets import IncomingTicket, IngestionResult, StoredCleanTicket
from backend.app.services.ticket_ingestion_service import TicketIngestionService


def _valid_config(**overrides: object) -> HaloPsaExtractorConfig:
    values: dict[str, object] = {
        "base_url": "https://halopsa.invalid.test",
        "client_id": "synthetic-client-id",
        "client_secret": "synthetic-client-secret",
        "tenant": "synthetic-tenant",
        "page_size": 2,
    }
    values.update(overrides)
    return HaloPsaExtractorConfig(**values)  # type: ignore[arg-type]


def _synthetic_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "halo-syn-001",
        "summary": "Synthetic laptop cannot reach the service portal",
        "details": "Synthetic diagnostic reports a controlled routing error.",
        "status": "open",
        "priority": "medium",
        "category": "network",
        "agent_id": "synthetic-agent-001",
        "raw_json": {"must_not_be_forwarded": True},
        "secret_note": "synthetic forbidden provider-only value",
    }
    payload.update(overrides)
    return payload


def test_halopsa_client_without_injected_transport_blocks_network_by_default() -> None:
    # Arrange
    client = HaloPsaTicketClient(config=_valid_config())

    # Act
    with pytest.raises(NetworkTransportNotConfiguredError, match="transport must be injected"):
        tuple(client.fetch_ticket_payloads())

    # Assert
    assert client is not None


def test_halopsa_client_with_incomplete_config_fails_closed_before_transport_usage() -> None:
    # Arrange
    transport = _RecordingTransport(payloads=(_synthetic_payload(),))
    incomplete_config = _valid_config(client_secret=" ")

    # Act
    with pytest.raises(InvalidHaloPsaConfigurationError, match="client_secret"):
        HaloPsaTicketClient(config=incomplete_config, transport=transport)

    # Assert
    assert transport.calls == 0


def test_halopsa_config_rejects_non_positive_page_size_before_usage() -> None:
    # Arrange
    config = _valid_config(page_size=0)

    # Act
    with pytest.raises(InvalidHaloPsaConfigurationError, match="page_size"):
        config.validate()

    # Assert
    assert config.page_size == 0


def test_halopsa_extractor_maps_synthetic_allowlisted_payload_to_incoming_ticket() -> None:
    # Arrange
    transport = _RecordingTransport(payloads=(_synthetic_payload(),))
    client = HaloPsaTicketClient(config=_valid_config(), transport=transport)
    extractor = HaloPsaTicketExtractor(client=client)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets == (
        IncomingTicket(
            external_ticket_id="halo-syn-001",
            summary="Synthetic laptop cannot reach the service portal",
            details="Synthetic diagnostic reports a controlled routing error.",
            status="open",
            priority="medium",
            category="network",
            agent_id="synthetic-agent-001",
        ),
    )
    guarded_mapping = tickets[0].to_guardrail_mapping()
    assert "raw_json" not in guarded_mapping
    assert "secret_note" not in guarded_mapping


def test_halopsa_extractor_rejects_payload_missing_required_allowlisted_field() -> None:
    # Arrange
    transport = _RecordingTransport(payloads=(_synthetic_payload(summary=" "),))
    client = HaloPsaTicketClient(config=_valid_config(), transport=transport)
    extractor = HaloPsaTicketExtractor(client=client)

    # Act
    with pytest.raises(InvalidHaloPsaTicketPayloadError, match="summary"):
        tuple(extractor.extract())

    # Assert
    assert transport.calls == 1


def test_ticket_ingestion_service_ingests_halopsa_tickets_via_source_agnostic_interface() -> None:
    # Arrange
    transport = _RecordingTransport(
        payloads=(
            _synthetic_payload(id="halo-syn-101"),
            _synthetic_payload(id="halo-syn-102", priority="low", agent_id="synthetic-agent-002"),
        )
    )
    extractor = HaloPsaTicketExtractor(client=HaloPsaTicketClient(config=_valid_config(), transport=transport))
    repository = _RecordingRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=2, stored_count=2, status="completed")
    assert transport.calls == 1
    assert len(repository.saved_batches) == 1
    assert all(isinstance(ticket, StoredCleanTicket) for ticket in repository.saved_batches[0])


def test_ticket_ingestion_service_does_not_send_raw_payload_or_forbidden_fields_to_repository() -> None:
    # Arrange
    transport = _RecordingTransport(payloads=(_synthetic_payload(payload={"blocked": True}),))
    extractor = HaloPsaTicketExtractor(client=HaloPsaTicketClient(config=_valid_config(), transport=transport))
    repository = _RecordingRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_tickets()

    # Assert
    assert result.stored_count == 1
    stored_ticket = repository.saved_batches[0][0]
    assert not hasattr(stored_ticket, "agent_id")
    for forbidden_field in ("raw_json", "raw_payload", "payload", "halopsa_payload"):
        assert not hasattr(stored_ticket, forbidden_field)


def test_halopsa_preparation_tests_do_not_need_or_read_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    original_open = builtins.open
    opened_paths: list[str] = []

    def fail_on_dotenv(file: object, *args: object, **kwargs: object) -> Any:
        path = Path(str(file))
        opened_paths.append(str(path))
        if path.name == ".env":
            raise AssertionError(".env must not be read by HaloPSA preparation tests")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fail_on_dotenv)
    transport = _RecordingTransport(payloads=(_synthetic_payload(),))
    extractor = HaloPsaTicketExtractor(client=HaloPsaTicketClient(config=_valid_config(), transport=transport))

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert len(tickets) == 1
    assert not any(Path(path).name == ".env" for path in opened_paths)


class _RecordingTransport:
    def __init__(self, payloads: Iterable[Mapping[str, object]]) -> None:
        self._payloads = tuple(payloads)
        self.calls = 0

    def fetch_tickets(self, config: HaloPsaExtractorConfig) -> Iterable[Mapping[str, object]]:
        self.calls += 1
        assert config.tenant == "synthetic-tenant"
        return self._payloads


class _RecordingRepository:
    def __init__(self) -> None:
        self.saved_batches: list[tuple[StoredCleanTicket, ...]] = []

    def save_many(self, tickets: Sequence[StoredCleanTicket]) -> int:
        batch = tuple(tickets)
        self.saved_batches.append(batch)
        return len(batch)
