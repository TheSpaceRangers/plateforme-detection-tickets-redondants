"""In-memory safe transformations for ticket dataset v1 dry-run."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping

try:  # pragma: no cover - compatibility for both `src.*` and repository-root imports.
    from src.eda.ticket_scope import _coerce_ticket_created_date
    from src.preprocessing.pii import PII_REPLACEMENTS, detect_pii, sanitize_text
except ModuleNotFoundError:  # pragma: no cover
    from ml.src.eda.ticket_scope import _coerce_ticket_created_date
    from ml.src.preprocessing.pii import PII_REPLACEMENTS, detect_pii, sanitize_text

from .contract import FEATURE_COLUMNS, MAX_CLEANED_TEXT_CHARS, MIN_TICKET_CREATED_AT


SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_=-]{32,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


@dataclass(frozen=True)
class TicketFeatureRow:
    """Safe feature row for contract validation; rows are never exported by dry-run."""

    cleaned_text_truncated: str
    created_month: int
    created_week: int
    created_day_of_week: int
    cleaned_text_length: int
    text_length_bucket: str
    has_email_placeholder: bool
    has_phone_placeholder: bool
    has_url_placeholder: bool

    def to_mapping(self) -> dict[str, object]:
        """Return a mapping with exactly the contract feature columns."""

        return {
            "cleaned_text_truncated": self.cleaned_text_truncated,
            "created_month": self.created_month,
            "created_week": self.created_week,
            "created_day_of_week": self.created_day_of_week,
            "cleaned_text_length": self.cleaned_text_length,
            "text_length_bucket": self.text_length_bucket,
            "has_email_placeholder": self.has_email_placeholder,
            "has_phone_placeholder": self.has_phone_placeholder,
            "has_url_placeholder": self.has_url_placeholder,
        }


@dataclass(frozen=True)
class TransformAggregateMetrics:
    """Aggregate-only metrics produced by safe transformations."""

    transformed_count: int
    pii_official_residual_count: int
    secret_scan_count: int


def build_safe_ticket_features(records: Iterable[Mapping[str, object]]) -> tuple[list[TicketFeatureRow], TransformAggregateMetrics]:
    """Build safe feature rows in memory and aggregate safety metrics only."""

    rows: list[TicketFeatureRow] = []
    pii_residual_count = 0
    secret_scan_count = 0

    for record in records:
        ticket_date = _coerce_ticket_created_date(record.get("ticket_created_at"))
        if ticket_date is None or ticket_date < date.fromisoformat(MIN_TICKET_CREATED_AT):
            continue

        cleaned_text = _build_cleaned_text(record)
        truncated_text = cleaned_text[:MAX_CLEANED_TEXT_CHARS]
        pii_residual_count += len(detect_pii(truncated_text))
        secret_scan_count += _count_secret_findings(truncated_text)
        rows.append(_build_feature_row(truncated_text, ticket_date))

    return rows, TransformAggregateMetrics(
        transformed_count=len(rows),
        pii_official_residual_count=pii_residual_count,
        secret_scan_count=secret_scan_count,
    )


def planned_feature_columns() -> tuple[str, ...]:
    """Return planned dataset columns without row-level values."""

    return FEATURE_COLUMNS


def _build_cleaned_text(record: Mapping[str, object]) -> str:
    """Sanitize and normalize raw text fields into one safe text feature."""

    parts = [str(record.get(field, "") or "") for field in ("summary", "details")]
    sanitized = sanitize_text("\n".join(parts)).text.lower()
    return " ".join(sanitized.split())


def _build_feature_row(text: str, ticket_date: date) -> TicketFeatureRow:
    """Build date-granularized and placeholder-derived features."""

    return TicketFeatureRow(
        cleaned_text_truncated=text,
        created_month=ticket_date.month,
        created_week=ticket_date.isocalendar().week,
        created_day_of_week=ticket_date.weekday(),
        cleaned_text_length=len(text),
        text_length_bucket=_bucket_text_length(len(text)),
        has_email_placeholder=PII_REPLACEMENTS["email"].lower() in text,
        has_phone_placeholder=PII_REPLACEMENTS["fr_phone"].lower() in text,
        has_url_placeholder=PII_REPLACEMENTS["url"].lower() in text,
    )


def _bucket_text_length(length: int) -> str:
    """Bucket text length to avoid exposing exact long-form distribution tails."""

    if length < 80:
        return "short"
    if length < 240:
        return "medium"
    return "long"


def _count_secret_findings(text: str) -> int:
    """Count potential secrets after transformation without returning matches."""

    return sum(len(pattern.findall(text)) for pattern in SECRET_PATTERNS)
