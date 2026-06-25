"""Unit tests for safe HaloPSA summary mapping with synthetic payloads only."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import pytest

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient
from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig
from backend.app.data.extractors.halopsa_ticket_extractor import (
    UNTITLED_SUMMARY,
    HaloPsaTicketExtractor,
    InvalidHaloPsaTicketPayloadError,
)

SYNTHETIC_EMAIL = "synthetic.user@example.invalid"
SYNTHETIC_SECRET_MARKER = "SYNTHETIC-SENSITIVE-MARKER-MUST-NOT-LEAK"


def test_halopsa_extractor_uses_title_when_summary_is_absent() -> None:
    # Arrange
    payload = _synthetic_payload(title="Synthetic title summary")
    payload.pop("summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == "Synthetic title summary"


def test_halopsa_extractor_uses_title_when_summary_is_blank() -> None:
    # Arrange
    payload = _synthetic_payload(summary=" ", title="Synthetic title summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == "Synthetic title summary"


def test_halopsa_extractor_uses_subject_when_summary_and_title_are_absent() -> None:
    # Arrange
    payload = _synthetic_payload(subject="Synthetic subject summary")
    payload.pop("summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == "Synthetic subject summary"


def test_halopsa_extractor_uses_subject_when_summary_and_title_are_blank() -> None:
    # Arrange
    payload = _synthetic_payload(summary="", title=" ", subject="Synthetic subject summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == "Synthetic subject summary"


def test_halopsa_extractor_uses_synthetic_summary_fallback_when_aliases_are_absent() -> None:
    # Arrange
    payload = _synthetic_payload()
    payload.pop("summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == UNTITLED_SUMMARY


def test_halopsa_extractor_uses_synthetic_summary_fallback_when_aliases_are_blank() -> None:
    # Arrange
    payload = _synthetic_payload(summary="", title=" ", subject=None)
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == UNTITLED_SUMMARY


@pytest.mark.parametrize("detail_alias", ["details", "description"])
def test_halopsa_extractor_never_copies_details_or_description_to_summary(detail_alias: str) -> None:
    # Arrange
    payload = _synthetic_payload(**{detail_alias: "Synthetic detail text must stay out of summary"})
    payload.pop("summary")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert tickets[0].summary == UNTITLED_SUMMARY
    assert tickets[0].summary != tickets[0].details


@pytest.mark.parametrize("summary_alias", ["title", "subject"])
def test_halopsa_extractor_sanitizes_pii_from_summary_aliases(summary_alias: str) -> None:
    # Arrange
    payload = _synthetic_payload(**{summary_alias: f"Synthetic contact {SYNTHETIC_EMAIL}"})
    payload.pop("summary")
    if summary_alias == "subject":
        payload["title"] = " "
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert transport.calls == 1
    assert SYNTHETIC_EMAIL not in tickets[0].summary
    assert "[EMAIL]" in tickets[0].summary


def test_halopsa_extractor_exception_does_not_leak_payload_when_required_id_is_missing() -> None:
    # Arrange
    payload = _synthetic_payload(
        summary=SYNTHETIC_SECRET_MARKER,
        details=SYNTHETIC_SECRET_MARKER,
        description=SYNTHETIC_SECRET_MARKER,
    )
    payload.pop("id")
    transport = _RecordingTransport(payloads=(payload,))
    extractor = _build_extractor(transport)

    # Act
    with pytest.raises(InvalidHaloPsaTicketPayloadError) as exc_info:
        tuple(extractor.extract())

    # Assert
    message = str(exc_info.value)
    assert transport.calls == 1
    assert "id" in message
    assert SYNTHETIC_SECRET_MARKER not in message
    assert "summary" not in message
    assert "details" not in message
    assert "description" not in message


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
        "id": "halo-summary-syn-001",
        "summary": "Synthetic summary input",
        "details": "Synthetic detail input",
        "status": "open",
    }
    payload.update(overrides)
    return payload


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
