"""HaloPSA ticket extractor adapter with allowlisted field transformation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient
from backend.app.schemas.tickets import IncomingTicket

UNKNOWN_STATUS = "unknown"
STATUS_FIELD_ALIASES = ("status", "status_id", "statusid", "ticketstatus")
STATUS_OBJECT_ALIASES = ("name", "id")


class InvalidHaloPsaTicketPayloadError(ValueError):
    """Raised when a HaloPSA payload cannot be minimized into an incoming ticket."""


class HaloPsaTicketExtractor:
    """Transform transient HaloPSA payloads into ingestion inputs without durable raw JSON storage."""

    def __init__(self, client: HaloPsaTicketClient) -> None:
        self._client = client

    def extract(self) -> Iterable[IncomingTicket]:
        """Fetch through the injected client and return only allowlisted ticket fields."""

        return tuple(_to_incoming_ticket(payload) for payload in self._client.fetch_ticket_payloads())


def _to_incoming_ticket(payload: Mapping[str, object]) -> IncomingTicket:
    """Map a transient provider payload to the canonical pre-guardrail ticket shape."""

    return IncomingTicket(
        external_ticket_id=_required_text(payload, ("id", "ticket_id", "external_ticket_id")),
        summary=_required_text(payload, ("summary", "title")),
        details=_required_text(payload, ("details", "description")),
        status=_status_text(payload),
        priority=_optional_text(payload, ("priority",)),
        category=_optional_text(payload, ("category", "ticket_type")),
        agent_id=_optional_text(payload, ("agent_id", "agentId", "assigned_agent_id")),
    )


def _required_text(payload: Mapping[str, object], field_names: tuple[str, ...]) -> str:
    """Return a required text field from accepted provider aliases."""

    value = _first_present(payload, field_names)
    if value is None or not str(value).strip():
        raise InvalidHaloPsaTicketPayloadError(f"Missing required HaloPSA ticket field: {field_names[0]}")
    return str(value)


def _optional_text(payload: Mapping[str, object], field_names: tuple[str, ...]) -> str | None:
    """Return an optional text field from accepted provider aliases."""

    value = _first_present(payload, field_names)
    if value is None or not str(value).strip():
        return None
    return str(value)


def _status_text(payload: Mapping[str, object]) -> str:
    """Return a normalized status from accepted aliases or a safe fallback."""

    value = _first_present(payload, STATUS_FIELD_ALIASES)
    if isinstance(value, Mapping):
        value = _first_present(value, STATUS_OBJECT_ALIASES)
    if value is None or not str(value).strip():
        return UNKNOWN_STATUS
    return str(value)


def _first_present(payload: Mapping[str, object], field_names: tuple[str, ...]) -> object | None:
    """Return the first provider value matching the allowlisted aliases."""

    for field_name in field_names:
        if field_name in payload:
            return payload[field_name]
    return None
