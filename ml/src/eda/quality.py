"""Aggregate-only quality checks for synthetic ticket dataset preparation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Iterable, Mapping

try:  # pragma: no cover - compatibility for both `src.*` and repository-root imports.
    from src.ml_contract.contract import RAW_INPUT_ALLOWLIST
except ModuleNotFoundError:  # pragma: no cover
    from ml.src.ml_contract.contract import RAW_INPUT_ALLOWLIST


@dataclass(frozen=True)
class TicketDatasetQualityReport:
    """Safe aggregate quality metrics for ticket-like source records."""

    missing_value_counts: dict[str, int]
    duplicate_signature_count: int
    source_column_count: int
    non_allowlisted_source_column_count: int
    text_length_bucket_distribution: dict[str, int]

    def to_safe_output(self) -> dict[str, object]:
        """Return only aggregate counts without source values or row examples."""

        return {
            "missing_value_counts": dict(sorted(self.missing_value_counts.items())),
            "duplicate_signature_count": self.duplicate_signature_count,
            "source_column_count": self.source_column_count,
            "non_allowlisted_source_column_count": self.non_allowlisted_source_column_count,
            "text_length_bucket_distribution": dict(sorted(self.text_length_bucket_distribution.items())),
        }


def build_ticket_dataset_quality_report(records: Iterable[Mapping[str, object]]) -> TicketDatasetQualityReport:
    """Compute aggregate quality metrics without exposing ticket contents."""

    source_records = list(records)
    source_columns = {str(column) for record in source_records for column in record.keys()}
    signatures: dict[str, int] = {}
    text_buckets = {"empty": 0, "short": 0, "medium": 0, "long": 0}

    for record in source_records:
        signature = _safe_record_signature(record)
        signatures[signature] = signatures.get(signature, 0) + 1
        text_buckets[_bucket_combined_text_length(record)] += 1

    return TicketDatasetQualityReport(
        missing_value_counts=_missing_value_counts(source_records),
        duplicate_signature_count=sum(count - 1 for count in signatures.values() if count > 1),
        source_column_count=len(source_columns),
        non_allowlisted_source_column_count=len(source_columns - RAW_INPUT_ALLOWLIST),
        text_length_bucket_distribution=text_buckets,
    )


def _missing_value_counts(records: list[Mapping[str, object]]) -> dict[str, int]:
    """Count missing values for allowlisted raw fields only."""

    counts = {field: 0 for field in sorted(RAW_INPUT_ALLOWLIST)}
    for record in records:
        for field in counts:
            if _is_missing(record.get(field)):
                counts[field] += 1
    return counts


def _is_missing(value: object) -> bool:
    """Return whether a raw value is absent or blank."""

    return value is None or (isinstance(value, str) and not value.strip())


def _safe_record_signature(record: Mapping[str, object]) -> str:
    """Hash allowlisted field presence/values without storing row-level text."""

    material = "\u241f".join(str(record.get(field, "")) for field in sorted(RAW_INPUT_ALLOWLIST))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _bucket_combined_text_length(record: Mapping[str, object]) -> str:
    """Bucket combined text length for distribution-only EDA."""

    length = len(str(record.get("summary", "") or "")) + len(str(record.get("details", "") or ""))
    if length == 0:
        return "empty"
    if length < 80:
        return "short"
    if length < 240:
        return "medium"
    return "long"
