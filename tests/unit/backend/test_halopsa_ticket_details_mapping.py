"""Unit tests for safe HaloPSA details mapping with synthetic payloads only."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import pytest

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient
from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig
from backend.app.data.extractors.halopsa_ticket_extractor import (
    HaloPsaTicketExtractor,
    InvalidHaloPsaTicketPayloadError,
)

SYNTHETIC_SENSITIVE_MARKER = "SYNTHETIC-SENSITIVE-MARKER-MUST-NOT-LEAK"


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
        "id": "halo-details-syn-001",
        "summary": "Synthetic details mapping input",
        "details": "Synthetic details text",
        "status": "open",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("detail_alias", "expected_details"),
    [
        ("details", "Synthetic details alias value"),
        ("description", "Synthetic description alias value"),
        ("detail", "Synthetic detail alias value"),
        ("body", "Synthetic body alias value"),
        ("note", "Synthetic note alias value"),
        ("symptom", "Synthetic symptom alias value"),
        ("problem", "Synthetic problem alias value"),
    ],
)
def test_halopsa_extractor_maps_supported_details_aliases(
    detail_alias: str,
    expected_details: str,
) -> None:
    # Arrange
    payload = _synthetic_payload()
    payload.pop("details")
    payload[detail_alias] = expected_details
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].details == expected_details


def test_halopsa_extractor_uses_first_non_empty_details_alias() -> None:
    # Arrange
    payload = _synthetic_payload(
        details=" ",
        description="",
        detail=None,
        body="Synthetic first non-empty details value",
        note="Synthetic later details value",
    )
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].details == "Synthetic first non-empty details value"


def test_halopsa_extractor_uses_empty_details_when_all_detail_aliases_are_absent() -> None:
    # Arrange
    payload = _synthetic_payload()
    payload.pop("details")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].details == ""


def test_halopsa_extractor_accepts_title_as_minimal_summary_alias() -> None:
    # Arrange
    payload = _synthetic_payload(title="Synthetic minimal title")
    payload.pop("summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == "Synthetic minimal title"


@pytest.mark.parametrize(
    ("missing_field", "expected_message_fragment"),
    [
        ("id", "id"),
        ("summary", "summary"),
    ],
)
def test_halopsa_extractor_fails_closed_when_minimal_required_fields_are_absent(
    missing_field: str,
    expected_message_fragment: str,
) -> None:
    # Arrange
    payload = _synthetic_payload()
    payload.pop(missing_field)
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    with pytest.raises(InvalidHaloPsaTicketPayloadError) as exc_info:
        tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert expected_message_fragment in str(exc_info.value)


def test_halopsa_extractor_error_message_does_not_leak_sensitive_ticket_content() -> None:
    # Arrange
    payload = _synthetic_payload(
        id=SYNTHETIC_SENSITIVE_MARKER,
        summary=" ",
        details=SYNTHETIC_SENSITIVE_MARKER,
        description=SYNTHETIC_SENSITIVE_MARKER,
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
    assert SYNTHETIC_SENSITIVE_MARKER not in message


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
