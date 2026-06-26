"""Unit tests for HaloPSA business date mapping without provider calls."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone

import pytest

from backend.app.data.extractors.halopsa_ticket_extractor import HaloPsaTicketExtractor
from backend.app.data.mappers.halopsa_dates import map_halopsa_business_dates
from backend.app.schemas.tickets import IncomingTicket, StoredCleanTicket


CREATED_ALIASES = ("created", "datecreated", "date_created", "dateoccurred", "date_opened", "opened_at", "dateopened")
UPDATED_ALIASES = ("updated", "last_update", "lastupdated", "dateupdated")
CLOSED_ALIASES = ("closed", "closed_at", "dateclosed", "resolved_at")


@pytest.mark.parametrize("alias", CREATED_ALIASES)
def test_halopsa_created_aliases_map_to_ticket_created_at(alias: str) -> None:
    # Arrange
    expected = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    payload = {alias: "2026-01-02T03:04:05Z"}

    # Act
    business_dates = map_halopsa_business_dates(payload)

    # Assert
    assert business_dates["ticket_created_at"] == expected
    assert business_dates["ticket_updated_at"] is None
    assert business_dates["ticket_closed_at"] is None


@pytest.mark.parametrize("alias", UPDATED_ALIASES)
def test_halopsa_updated_aliases_map_to_ticket_updated_at(alias: str) -> None:
    # Arrange
    expected = datetime(2026, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
    payload = {alias: "2026-02-03T04:05:06Z"}

    # Act
    business_dates = map_halopsa_business_dates(payload)

    # Assert
    assert business_dates["ticket_created_at"] is None
    assert business_dates["ticket_updated_at"] == expected
    assert business_dates["ticket_closed_at"] is None


@pytest.mark.parametrize("alias", CLOSED_ALIASES)
def test_halopsa_closed_aliases_map_to_ticket_closed_at(alias: str) -> None:
    # Arrange
    expected = datetime(2026, 3, 4, 5, 6, 7, tzinfo=timezone.utc)
    payload = {alias: "2026-03-04T05:06:07Z"}

    # Act
    business_dates = map_halopsa_business_dates(payload)

    # Assert
    assert business_dates["ticket_created_at"] is None
    assert business_dates["ticket_updated_at"] is None
    assert business_dates["ticket_closed_at"] == expected


def test_halopsa_missing_dates_map_to_none() -> None:
    # Arrange
    payload: dict[str, object] = {}

    # Act
    business_dates = map_halopsa_business_dates(payload)

    # Assert
    assert business_dates == {"ticket_created_at": None, "ticket_updated_at": None, "ticket_closed_at": None}


def test_halopsa_invalid_dates_fail_closed_without_exception_or_payload_log(caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    caplog.set_level(logging.DEBUG)
    payload = {"created": "invalid-date", "updated": object(), "closed": -1}

    # Act
    business_dates = map_halopsa_business_dates(payload)

    # Assert
    assert business_dates == {"ticket_created_at": None, "ticket_updated_at": None, "ticket_closed_at": None}
    assert caplog.records == []


def test_halopsa_extractor_propagates_business_dates_from_injected_client() -> None:
    # Arrange
    client = _SyntheticClient(
        (
            {
                "id": "syn-001",
                "summary": "Synthetic summary",
                "details": "Synthetic details",
                "status": "open",
                "dateopened": "2026-04-05T06:07:08Z",
                "lastupdated": "2026-04-06T06:07:08Z",
                "dateclosed": "2026-04-07T06:07:08Z",
            },
        )
    )
    extractor = HaloPsaTicketExtractor(client=client)  # type: ignore[arg-type]

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert tickets[0].ticket_created_at == datetime(2026, 4, 5, 6, 7, 8, tzinfo=timezone.utc)
    assert tickets[0].ticket_updated_at == datetime(2026, 4, 6, 6, 7, 8, tzinfo=timezone.utc)
    assert tickets[0].ticket_closed_at == datetime(2026, 4, 7, 6, 7, 8, tzinfo=timezone.utc)
    assert client.calls == 1


def test_halopsa_extractor_keeps_invalid_business_dates_as_none() -> None:
    # Arrange
    client = _SyntheticClient(
        (
            {
                "id": "syn-002",
                "summary": "Synthetic summary",
                "details": "Synthetic details",
                "status": "open",
                "created": "not-a-date",
                "updated": None,
                "closed": False,
            },
        )
    )
    extractor = HaloPsaTicketExtractor(client=client)  # type: ignore[arg-type]

    # Act
    tickets = tuple(extractor.extract())

    # Assert
    assert tickets[0].ticket_created_at is None
    assert tickets[0].ticket_updated_at is None
    assert tickets[0].ticket_closed_at is None
    assert client.calls == 1


def test_ticket_schemas_preserve_valid_business_dates_in_guardrail_mapping() -> None:
    # Arrange
    created_at = datetime(2026, 5, 6, 7, 8, 9, tzinfo=timezone.utc)
    ticket = IncomingTicket(
        external_ticket_id="syn-003",
        summary="Synthetic summary",
        details="Synthetic details",
        status="open",
        ticket_created_at=created_at,
    )

    # Act
    guarded = ticket.to_guardrail_mapping()
    stored = StoredCleanTicket.from_guarded_mapping(guarded)

    # Assert
    assert guarded["ticket_created_at"] == created_at
    assert stored.ticket_created_at == created_at
    assert stored.ticket_updated_at is None
    assert stored.ticket_closed_at is None


def test_ticket_schema_rejects_non_datetime_business_date_values() -> None:
    # Arrange
    guarded: dict[str, object] = {
        "external_ticket_id": "syn-004",
        "summary": "Synthetic summary",
        "details": "Synthetic details",
        "status": "open",
        "ticket_created_at": "2026-05-06T07:08:09Z",
    }

    # Act / Assert
    with pytest.raises(ValueError, match="Business date fields"):
        StoredCleanTicket.from_guarded_mapping(guarded)


class _SyntheticClient:
    def __init__(self, payloads: Iterable[Mapping[str, object]]) -> None:
        self._payloads = tuple(payloads)
        self.calls = 0

    def fetch_ticket_payloads(self) -> Iterable[Mapping[str, object]]:
        self.calls += 1
        return self._payloads
