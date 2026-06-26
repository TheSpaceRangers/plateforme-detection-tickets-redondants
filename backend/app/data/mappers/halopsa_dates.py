"""Centralized HaloPSA business date mapping."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone

TICKET_CREATED_AT_ALIASES: tuple[str, ...] = (
    "created",
    "datecreated",
    "date_created",
    "dateoccurred",
    "date_opened",
    "opened_at",
    "dateopened",
)
TICKET_UPDATED_AT_ALIASES: tuple[str, ...] = ("updated", "last_update", "lastupdated", "dateupdated")
TICKET_CLOSED_AT_ALIASES: tuple[str, ...] = ("closed", "closed_at", "dateclosed", "resolved_at")


def map_halopsa_business_dates(payload: Mapping[str, object]) -> dict[str, datetime | None]:
    """Return canonical nullable business dates from allowlisted HaloPSA aliases."""

    return {
        "ticket_created_at": first_valid_datetime(payload, TICKET_CREATED_AT_ALIASES),
        "ticket_updated_at": first_valid_datetime(payload, TICKET_UPDATED_AT_ALIASES),
        "ticket_closed_at": first_valid_datetime(payload, TICKET_CLOSED_AT_ALIASES),
    }


def first_valid_datetime(payload: Mapping[str, object], aliases: tuple[str, ...]) -> datetime | None:
    """Return the first parseable date value; invalid source dates fail closed to None."""

    for alias in aliases:
        if alias not in payload:
            continue
        parsed_value = parse_provider_datetime(payload[alias])
        if parsed_value is not None:
            return parsed_value
    return None


def parse_provider_datetime(value: object) -> datetime | None:
    """Parse common provider date values without raising on invalid input."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, datetime):
        return _ensure_timezone(value)
    if isinstance(value, (int, float)):
        return _parse_epoch(value)
    if isinstance(value, str):
        return _parse_datetime_text(value)
    return None


def _parse_datetime_text(value: str) -> datetime | None:
    """Parse ISO-like text and fail closed for unsupported provider formats."""

    normalized_value = value.strip()
    if not normalized_value:
        return None
    try:
        return _ensure_timezone(datetime.fromisoformat(normalized_value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _parse_epoch(value: int | float) -> datetime | None:
    """Parse safe epoch values and reject implausible numeric dates."""

    timestamp = float(value)
    if timestamp <= 0:
        return None
    if timestamp > 10_000_000_000:
        timestamp = timestamp / 1000
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _ensure_timezone(value: datetime) -> datetime:
    """Normalize naive provider dates to UTC to match PostgreSQL TIMESTAMPTZ."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
