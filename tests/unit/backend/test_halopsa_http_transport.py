"""Unit tests for the explicit HaloPSA HTTP transport without real network access."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from urllib.error import URLError

import pytest

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient
from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig
from backend.app.data.extractors.halopsa_http_transport import (
    HaloPsaHttpTransport,
    HaloPsaHttpTransportError,
)
from backend.app.data.extractors.halopsa_ticket_extractor import HaloPsaTicketExtractor
from backend.app.schemas.tickets import IngestionResult, StoredCleanTicket
from backend.app.services.ticket_ingestion_service import TicketIngestionService


SYNTHETIC_CLIENT_SECRET = "synthetic-client-secret-never-log"
SYNTHETIC_ACCESS_TOKEN = "synthetic-access-token-never-log"
SYNTHETIC_RAW_PROVIDER_VALUE = "synthetic-provider-only-raw-value"


def _valid_config(**overrides: object) -> HaloPsaExtractorConfig:
    values: dict[str, object] = {
        "base_url": "https://halopsa.invalid.test",
        "client_id": "synthetic-client-id",
        "client_secret": SYNTHETIC_CLIENT_SECRET,
        "tenant": "synthetic-tenant",
        "scope": "synthetic-scope",
        "page_size": 5,
        "request_timeout_seconds": 1.0,
        "max_retries": 0,
    }
    values.update(overrides)
    return HaloPsaExtractorConfig(**values)  # type: ignore[arg-type]


def _synthetic_ticket_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "halo-http-syn-001",
        "summary": "Synthetic portal access is unavailable",
        "details": "Synthetic diagnostic contains only fabricated provider text.",
        "status": "open",
        "priority": "medium",
        "category": "network",
        "agent_id": "synthetic-agent-http-001",
        "raw_json": {"provider_only": SYNTHETIC_RAW_PROVIDER_VALUE},
        "secret_note": SYNTHETIC_RAW_PROVIDER_VALUE,
    }
    payload.update(overrides)
    return payload


def test_http_transport_fetches_one_synthetic_ticket_with_mocked_urlopen(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    from backend.app.data.extractors import halopsa_http_transport as transport_module

    responses = [
        _JsonResponse('{"access_token":"synthetic-access-token-never-log"}'),
        _JsonResponse(
            '{"tickets":[{"id":"halo-http-syn-001","summary":"Synthetic portal access is unavailable"}]}'
        ),
    ]
    requests: list[Any] = []

    def fake_urlopen(request: Any, timeout: float) -> _JsonResponse:
        requests.append(request)
        assert timeout == 1.0
        return responses.pop(0)

    monkeypatch.setattr(transport_module, "urlopen", fake_urlopen)
    transport = HaloPsaHttpTransport()

    # Act
    tickets = tuple(transport.fetch_tickets(_valid_config()))

    # Assert
    assert tickets == ({"id": "halo-http-syn-001", "summary": "Synthetic portal access is unavailable"},)
    assert len(requests) == 2
    assert requests[0].get_method() == "POST"
    assert requests[1].get_method() == "GET"
    assert "page_size=5" in requests[1].full_url


def test_http_transport_rejects_response_without_ticket_list(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    from backend.app.data.extractors import halopsa_http_transport as transport_module

    responses = [_JsonResponse('{"access_token":"synthetic-access-token-never-log"}'), _JsonResponse("{}")]
    monkeypatch.setattr(transport_module, "urlopen", lambda request, timeout: responses.pop(0))
    transport = HaloPsaHttpTransport()

    # Act
    with pytest.raises(HaloPsaHttpTransportError, match="ticket list"):
        tuple(transport.fetch_tickets(_valid_config()))

    # Assert
    assert responses == []


def test_http_transport_network_error_message_does_not_leak_secret_or_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    from backend.app.data.extractors import halopsa_http_transport as transport_module

    def fake_urlopen(request: Any, timeout: float) -> _JsonResponse:
        raise URLError(f"provider failure {SYNTHETIC_CLIENT_SECRET} {SYNTHETIC_RAW_PROVIDER_VALUE}")

    monkeypatch.setattr(transport_module, "urlopen", fake_urlopen)
    transport = HaloPsaHttpTransport()

    # Act
    with pytest.raises(HaloPsaHttpTransportError) as error:
        tuple(transport.fetch_tickets(_valid_config()))

    # Assert
    error_message = str(error.value)
    assert "failed after bounded retries" in error_message
    assert SYNTHETIC_CLIENT_SECRET not in error_message
    assert SYNTHETIC_RAW_PROVIDER_VALUE not in error_message


def test_http_transport_token_error_message_does_not_leak_secret_or_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    from backend.app.data.extractors import halopsa_http_transport as transport_module

    monkeypatch.setattr(transport_module, "urlopen", lambda request, timeout: _JsonResponse("{}"))
    transport = HaloPsaHttpTransport()

    # Act
    with pytest.raises(HaloPsaHttpTransportError) as error:
        tuple(transport.fetch_tickets(_valid_config()))

    # Assert
    error_message = str(error.value)
    assert "access token" in error_message
    assert SYNTHETIC_CLIENT_SECRET not in error_message
    assert SYNTHETIC_ACCESS_TOKEN not in error_message


def test_http_mocked_response_ingests_minimized_ticket_without_raw_provider_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    from backend.app.data.extractors import halopsa_http_transport as transport_module

    responses = [
        _JsonResponse('{"access_token":"synthetic-access-token-never-log"}'),
        _JsonResponse(
            """
            {
              "tickets": [
                {
                  "id": "halo-http-syn-001",
                  "summary": "Synthetic portal access is unavailable",
                  "details": "Synthetic diagnostic contains only fabricated provider text.",
                  "status": "open",
                  "priority": "medium",
                  "category": "network",
                  "agent_id": "synthetic-agent-http-001",
                  "raw_json": {"provider_only": "synthetic-provider-only-raw-value"},
                  "secret_note": "synthetic-provider-only-raw-value"
                }
              ]
            }
            """
        ),
    ]
    monkeypatch.setattr(transport_module, "urlopen", lambda request, timeout: responses.pop(0))
    client = HaloPsaTicketClient(config=_valid_config(), transport=HaloPsaHttpTransport())
    extractor = HaloPsaTicketExtractor(client=client)
    repository = _RecordingRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    result = service.ingest_tickets()

    # Assert
    assert result == IngestionResult(extracted_count=1, stored_count=1, status="completed")
    assert len(repository.saved_batches) == 1
    stored_ticket = repository.saved_batches[0][0]
    assert stored_ticket.external_ticket_id == "halo-http-syn-001"
    assert stored_ticket.summary == "Synthetic portal access is unavailable"
    assert not hasattr(stored_ticket, "agent_id")
    for forbidden_field in ("raw_json", "raw_payload", "payload", "halopsa_payload", "secret_note"):
        assert not hasattr(stored_ticket, forbidden_field)
    assert SYNTHETIC_RAW_PROVIDER_VALUE not in repr(stored_ticket)


def test_http_mocked_response_missing_required_ticket_field_blocks_before_repository_save(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    from backend.app.data.extractors import halopsa_http_transport as transport_module

    responses = [
        _JsonResponse('{"access_token":"synthetic-access-token-never-log"}'),
        _JsonResponse('{"tickets":[{"id":"halo-http-syn-001","summary":" "}]}'),
    ]
    monkeypatch.setattr(transport_module, "urlopen", lambda request, timeout: responses.pop(0))
    client = HaloPsaTicketClient(config=_valid_config(), transport=HaloPsaHttpTransport())
    extractor = HaloPsaTicketExtractor(client=client)
    repository = _RecordingRepository()
    service = TicketIngestionService(extractor=extractor, repository=repository)

    # Act
    with pytest.raises(ValueError, match="summary"):
        service.ingest_tickets()

    # Assert
    assert repository.saved_batches == []


class _JsonResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def __enter__(self) -> "_JsonResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class _RecordingRepository:
    def __init__(self) -> None:
        self.saved_batches: list[tuple[StoredCleanTicket, ...]] = []

    def save_many(self, tickets: Sequence[StoredCleanTicket]) -> int:
        batch = tuple(tickets)
        self.saved_batches.append(batch)
        return len(batch)
