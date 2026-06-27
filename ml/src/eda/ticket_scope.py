"""Business date scoping for aggregate-only ticket EDA/ML metrics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable, Iterable, Mapping

DEFAULT_MIN_TICKET_CREATED_AT = date(2025, 1, 1)
TICKET_CREATED_AT_FIELD = "ticket_created_at"


@dataclass(frozen=True)
class EdaDateScopeConfig:
    """Configuration for excluding historical outliers from EDA/ML metrics."""

    min_ticket_created_at: date = DEFAULT_MIN_TICKET_CREATED_AT


@dataclass(frozen=True)
class TicketEdaScopeMetrics:
    """Aggregate-only counters describing the date scope applied to EDA/ML metrics."""

    total_source_count: int
    included_count: int
    excluded_historical_outlier_count: int
    excluded_missing_ticket_created_at_count: int
    applied_min_ticket_created_at: str

    def to_safe_output(self) -> dict[str, int | str]:
        """Return non-identifying aggregate counters safe for EDA output."""

        return {
            "total_source_count": self.total_source_count,
            "included_count": self.included_count,
            "excluded_historical_outlier_count": self.excluded_historical_outlier_count,
            "excluded_missing_ticket_created_at_count": self.excluded_missing_ticket_created_at_count,
            "applied_min_ticket_created_at": self.applied_min_ticket_created_at,
        }


def build_ticket_eda_scope_metrics(
    records: Iterable[Mapping[str, object]],
    config: EdaDateScopeConfig | None = None,
) -> TicketEdaScopeMetrics:
    """Build aggregate-only scope counters without exposing source ticket content."""

    scope_config = config or EdaDateScopeConfig()
    source_records = list(records)
    included_count = 0
    historical_outlier_count = 0
    missing_ticket_created_at_count = 0

    for record in source_records:
        ticket_created_at = _coerce_ticket_created_date(record.get(TICKET_CREATED_AT_FIELD))
        if ticket_created_at is None:
            missing_ticket_created_at_count += 1
            continue
        if ticket_created_at < scope_config.min_ticket_created_at:
            historical_outlier_count += 1
            continue
        included_count += 1

    return TicketEdaScopeMetrics(
        total_source_count=len(source_records),
        included_count=included_count,
        excluded_historical_outlier_count=historical_outlier_count,
        excluded_missing_ticket_created_at_count=missing_ticket_created_at_count,
        applied_min_ticket_created_at=scope_config.min_ticket_created_at.isoformat(),
    )


def filter_records_for_ticket_eda_metrics(
    records: Iterable[Mapping[str, object]],
    config: EdaDateScopeConfig | None = None,
) -> list[Mapping[str, object]]:
    """Return records included in filtered EDA/ML metrics without mutating source records."""

    scope_config = config or EdaDateScopeConfig()
    return [
        record
        for record in records
        if _is_included_for_ticket_eda(record, min_ticket_created_at=scope_config.min_ticket_created_at)
    ]


def _is_included_for_ticket_eda(record: Mapping[str, object], *, min_ticket_created_at: date) -> bool:
    """Return whether one record belongs to the filtered EDA/ML metric scope."""

    ticket_created_at = _coerce_ticket_created_date(record.get(TICKET_CREATED_AT_FIELD))
    return ticket_created_at is not None and ticket_created_at >= min_ticket_created_at


def _coerce_ticket_created_date(value: object) -> date | None:
    """Normalize supported timestamp values to a date without logging raw input."""

    if value is None:
        return None
    if isinstance(value, datetime):
        normalized = value.astimezone(timezone.utc) if value.tzinfo else value
        return normalized.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return _parse_iso_like_date(value)
    return None


def _parse_iso_like_date(value: str) -> date | None:
    """Parse ISO-like date strings and fail closed to exclusion when unsupported."""

    normalized_value = value.strip()
    if not normalized_value:
        return None
    if normalized_value.endswith("Z"):
        normalized_value = f"{normalized_value[:-1]}+00:00"
    parsers: tuple[Callable[[str], date | datetime], ...] = (datetime.fromisoformat, date.fromisoformat)
    for parser in parsers:
        try:
            parsed = parser(normalized_value)
        except ValueError:
            continue
        if isinstance(parsed, datetime):
            return _coerce_ticket_created_date(parsed)
        return parsed
    return None
