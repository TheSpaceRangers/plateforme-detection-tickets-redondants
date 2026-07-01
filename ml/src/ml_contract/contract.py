"""Strict aggregate-safe contract for ticket dataset v1 dry-run tooling."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Pattern


DATASET_VERSION = "ticket_dataset_v1"

MIN_TICKET_CREATED_AT = "2025-01-01"

MAX_CLEANED_TEXT_CHARS = 512


RAW_INPUT_ALLOWLIST: frozenset[str] = frozenset({"summary", "details", "ticket_created_at"})

FEATURE_COLUMNS: tuple[str, ...] = (
    "cleaned_text_truncated",
    "created_day_of_week",
    "created_month",
    "created_week",
    "cleaned_text_length",
    "text_length_bucket",
    "has_email_placeholder",
    "has_phone_placeholder",
    "has_url_placeholder",
)

FEATURE_ALLOWLIST: frozenset[str] = frozenset(FEATURE_COLUMNS)

REPORT_KEYS: tuple[str, ...] = (
    "dataset_version",
    "mode",
    "status",
    "scope_min_ticket_created_at",
    "total_source_count",
    "included_count",
    "excluded_historical_outlier_count",
    "excluded_missing_ticket_created_at_count",
    "planned_dataset_columns",
    "pii_official_residual_count",
    "secret_scan_count",
    "forbidden_column_count",
    "exact_timestamp_column_count",
    "raw_text_column_count",
    "quality_report",
    "lot3_readiness",
    "gates",
)

REPORT_ALLOWLIST: frozenset[str] = frozenset(REPORT_KEYS)

DENYLIST_COLUMNS: frozenset[str] = frozenset(
    {
        "external_ticket_id",
        "agent_id",
        "agent_id_pseudonym",
        "payload",
        "id",
        "ticket_id",
        "user_id",
        "client_id",
        "customer_id",
        "account_id",
        "created_at",
        "updated_at",
        "ticket_created_at",
        "closed_at",
        "resolved_at",
        "priority",
        "category",
        "summary",
        "details",
        "raw_text",
        "cleaned_text",
    }
)

DENYLIST_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"(^|_)(id|uuid|guid)($|_)", re.IGNORECASE),
    re.compile(r"timestamp|payload|priority|category", re.IGNORECASE),
    re.compile(r"(^|_)(summary|details|raw_text|cleaned_text)($|_)", re.IGNORECASE),
)

EXACT_TIMESTAMP_PATTERNS: tuple[Pattern[str], ...] = (
    re.compile(r"(^|_)created_at$", re.IGNORECASE),
    re.compile(r"timestamp", re.IGNORECASE),
    re.compile(r"_at$", re.IGNORECASE),
)


class DatasetContractError(ValueError):
    """Raised when the ticket dataset v1 contract is violated."""


@dataclass(frozen=True)
class ContractValidationResult:
    """Aggregate-only contract validation result."""

    forbidden_column_count: int
    exact_timestamp_column_count: int
    raw_text_column_count: int

    @property
    def is_valid(self) -> bool:
        """Return whether no structural contract violation was detected."""

        return (
            self.forbidden_column_count == 0
            and self.exact_timestamp_column_count == 0
            and self.raw_text_column_count == 0
        )


def validate_raw_input_columns(records: Iterable[Mapping[str, object]]) -> ContractValidationResult:
    """Validate transient raw input columns without exposing source values."""

    columns = _collect_columns(records)
    forbidden = {column for column in columns if _is_forbidden_input_column(column)}
    exact_timestamps = {column for column in columns if _is_exact_timestamp_column(column)} - RAW_INPUT_ALLOWLIST
    raw_text = {column for column in columns if _is_raw_text_column(column)} - RAW_INPUT_ALLOWLIST
    return ContractValidationResult(
        forbidden_column_count=len(forbidden),
        exact_timestamp_column_count=len(exact_timestamps),
        raw_text_column_count=len(raw_text),
    )


def validate_feature_columns(columns: Iterable[str]) -> ContractValidationResult:
    """Validate final feature columns against the strict allowlist and denylist."""

    column_set = set(columns)
    forbidden = {column for column in column_set if column not in FEATURE_ALLOWLIST or _is_forbidden_output_column(column)}
    exact_timestamps = {column for column in column_set if _is_exact_timestamp_column(column)}
    raw_text = {column for column in column_set if _is_raw_text_column(column)}
    return ContractValidationResult(
        forbidden_column_count=len(forbidden),
        exact_timestamp_column_count=len(exact_timestamps),
        raw_text_column_count=len(raw_text),
    )


def assert_safe_report_keys(report: Mapping[str, object]) -> None:
    """Block reports containing fields outside the aggregate-safe allowlist."""

    unexpected_keys = set(report) - REPORT_ALLOWLIST
    if unexpected_keys:
        raise DatasetContractError("Unsafe dry-run report fields detected.")


def _collect_columns(records: Iterable[Mapping[str, object]]) -> set[str]:
    """Collect source columns without keeping row values."""

    columns: set[str] = set()
    for record in records:
        columns.update(str(key) for key in record.keys())
    return columns


def _is_forbidden_input_column(column: str) -> bool:
    """Return whether a source column is outside the transient raw input contract."""

    normalized = column.lower()
    return normalized not in RAW_INPUT_ALLOWLIST


def _is_forbidden_output_column(column: str) -> bool:
    """Return whether an output feature column is explicitly unsafe."""

    normalized = column.lower()
    if normalized in FEATURE_ALLOWLIST:
        return False
    return normalized in DENYLIST_COLUMNS or any(pattern.search(normalized) for pattern in DENYLIST_PATTERNS)


def _is_exact_timestamp_column(column: str) -> bool:
    """Return whether a column name suggests timestamp precision."""

    normalized = column.lower()
    return any(pattern.search(normalized) for pattern in EXACT_TIMESTAMP_PATTERNS)


def _is_raw_text_column(column: str) -> bool:
    """Return whether a column name suggests raw or untruncated text."""

    return column.lower() in {"summary", "details", "raw_text", "cleaned_text"}
