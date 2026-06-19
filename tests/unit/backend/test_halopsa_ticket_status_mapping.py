"""Unit tests for safe HaloPSA status mapping with synthetic payloads only."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import pytest

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient
from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig
from backend.app.data.extractors.halopsa_ticket_extractor import (
    UNKNOWN_STATUS,
    HaloPsaTicketExtractor,
    InvalidHaloPsaTicketPayloadError,
)

SYNTHETIC_SECRET_MARKER = "SYNTHETIC-SENSITIVE-MARKER-MUST-NOT-LEAK"


def _valid_config() -> HaloPsaExtractorConfig:
    return HaloPsaExtractorConfig(
        base_url="https://halopsa.invalid.test",
        client_id="synthetic-client-id",
        client_secret="synthetic-client-secret",
        tenant="synthetic-tenant",
        page_size=1,
    )


def _synthetic_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "halo-status-syn-001",
        "summary": "Synthetic status mapping input",
        "details": "Synthetic status mapping detail",
        "status": "open",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("payload_override", "expected_status"),
    [
        ({"status": "closed"}, "closed"),
        ({"status_id": 7}, "7"),
        ({"statusid": "8"}, "8"),
        ({"ticketstatus": "in_progress"}, "in_progress"),
        ({"status": {"name": "waiting_customer", "id": 9}}, "waiting_customer"),
        ({"status": {"id": 10}}, "10"),
    ],
)
def test_halopsa_extractor_maps_supported_status_variants(
    payload_override: dict[str, object],
    expected_status: str,
) -> None:
    # Arrange
    payload = _synthetic_payload(**payload_override)
    if "status" not in payload_override:
        payload.pop("status")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].status == expected_status


def test_halopsa_extractor_uses_unknown_when_status_is_absent() -> None:
    # Arrange
    payload = _synthetic_payload()
    payload.pop("status")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].status == UNKNOWN_STATUS


def test_halopsa_extractor_error_message_does_not_leak_sensitive_payload_content() -> None:
    # Arrange
    payload = _synthetic_payload(
        id=SYNTHETIC_SECRET_MARKER,
        summary=" ",
        details=SYNTHETIC_SECRET_MARKER,
    )
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    with pytest.raises(InvalidHaloPsaTicketPayloadError) as exc_info:
        tuple(extractor.extract())

    # Assert
    message = str(exc_info.value)
    assert transport.calls == 1
    assert "summary" in message
    assert SYNTHETIC_SECRET_MARKER not in message


def _build_extractor(transport: _RecordingTransport) -> HaloPsaTicketExtractor:
    client = HaloPsaTicketClient(config=_valid_config(), transport=transport)
    return HaloPsaTicketExtractor(client=client)


class _RecordingTransport:
    def __init__(self, payloads: Iterable[Mapping[str, object]]) -> None:
        self._payloads = tuple(payloads)
        self.calls = 0

    def fetch_tickets(self, config: HaloPsaExtractorConfig) -> Iterable[Mapping[str, object]]:
        self.calls += 1
        assert config.tenant == "synthetic-tenant"
        return self._payloads
