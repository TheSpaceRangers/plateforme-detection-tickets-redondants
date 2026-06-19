"""HaloPSA ticket extractor adapter with allowlisted field transformation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient
from backend.app.schemas.tickets import IncomingTicket

UNKNOWN_STATUS = "unknown"
STATUS_FIELD_ALIASES = ("status", "status_id", "statusid", "ticketstatus")
STATUS_OBJECT_ALIASES = ("name", "id")
DETAIL_FIELD_ALIASES = (
    "details",
    "description",
    "detail",
    "body",
    "note",
    "symptom",
    "problem",
)


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
        details=_details_text(payload),
        status=_status_text(payload),
        priority=_optional_text(payload, ("priority",)),
        category=_optional_text(payload, ("category", "ticket_type")),
        agent_id=_optional_text(payload, ("agent_id", "agentId", "assigned_agent_id")),
    )


def _required_text(payload: Mapping[str, object], field_names: tuple[str, ...]) -> str:
    """Return a required text field from accepted provider aliases."""

    value = _first_non_blank_text(payload, field_names)
    if value is None:
        raise InvalidHaloPsaTicketPayloadError(f"Missing required HaloPSA ticket field: {field_names[0]}")
    return value


def _optional_text(payload: Mapping[str, object], field_names: tuple[str, ...]) -> str | None:
    """Return an optional text field from accepted provider aliases."""

    return _first_non_blank_text(payload, field_names)


def _details_text(payload: Mapping[str, object]) -> str:
    """Return ticket details from supported aliases or an explicit safe empty fallback."""

    value = _first_non_blank_text(payload, DETAIL_FIELD_ALIASES)
    if value is None:
        return ""
    return value


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


def _first_non_blank_text(payload: Mapping[str, object], field_names: tuple[str, ...]) -> str | None:
    """Return the first non-blank provider text matching the allowlisted aliases."""

    for field_name in field_names:
        if field_name not in payload:
            continue
        if payload[field_name] is None:
            continue
        value = str(payload[field_name]).strip()
        if value:
            return value
    return None
