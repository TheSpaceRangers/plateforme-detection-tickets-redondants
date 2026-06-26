"""Service layer for secure aggregate ticket EDA."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Protocol

from backend.app.schemas.ticket_eda import (
    AggregateTicketEdaReport,
    PiiCategoryResidualMetric,
    PiiScanMetric,
)
from ml.src.preprocessing.pii import PII_REPLACEMENTS, detect_pii

FORBIDDEN_OUTPUT_KEYS: frozenset[str] = frozenset(
    ("summary", "details", "external_ticket_id", "agent_id_pseudonym", "payload")
)
FORBIDDEN_OUTPUT_VALUE_TOKENS: frozenset[str] = frozenset(("external_ticket_id", "agent_id_pseudonym", "payload"))


class AggregateTicketEdaReader(Protocol):
    """Repository contract exposing aggregate-only ticket EDA methods."""

    def count_tickets(self) -> int:
        """Return total ticket count."""

    def get_distribution(self, column: str) -> Any:
        """Return anonymous distribution for a controlled dimension."""

    def get_text_quality(self, column: str) -> Any:
        """Return aggregate text quality metrics for an internal text column."""

    def get_fallback_untitled_ticket_rate(self) -> float:
        """Return aggregate fallback title rate."""

    def get_placeholder_metrics(self) -> list[Any]:
        """Return aggregate placeholder metrics."""

    def get_temporal_distribution(self) -> Any:
        """Return aggregate temporal distributions."""

    def get_heuristic_like_pattern_count(self) -> int:
        """Return diagnostic SQL heuristic-like pattern count."""

    def iter_sanitized_text_pairs(self, batch_size: int = 500) -> Iterator[tuple[str, str]]:
        """Yield sanitized text pairs for official in-memory aggregate scans."""

    def get_completeness(self) -> list[Any]:
        """Return allowed-field completeness metrics."""


class AggregateTicketEdaService:
    """Build and validate secure aggregate-only EDA reports."""

    _instance: "AggregateTicketEdaService | None" = None

    def __new__(cls, *args: object, **kwargs: object) -> "AggregateTicketEdaService":
        """Create a singleton service instance."""

        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, repository: AggregateTicketEdaReader) -> None:
        if not hasattr(self, "_initialized"):
            self._repository = repository
            self._initialized = True

    def build_report(self) -> AggregateTicketEdaReport:
        """Build a safe aggregate-only report and fail closed on leak risk."""

        report = AggregateTicketEdaReport(
            total_tickets=self._repository.count_tickets(),
            status_distribution=self._repository.get_distribution("status"),
            priority_distribution=self._repository.get_distribution("priority"),
            category_distribution=self._repository.get_distribution("category"),
            short_text=self._repository.get_text_quality("summary"),
            long_text=self._repository.get_text_quality("details"),
            fallback_untitled_ticket_rate=self._repository.get_fallback_untitled_ticket_rate(),
            placeholder_counts=self._repository.get_placeholder_metrics(),
            temporal_distribution=self._repository.get_temporal_distribution(),
            pii_scan=self._build_official_pii_scan(),
            completeness=self._repository.get_completeness(),
        )
        self.validate_no_forbidden_output(report)
        return report

    def validate_no_forbidden_output(self, report: AggregateTicketEdaReport) -> None:
        """Fail closed if report keys or string values include forbidden exposure markers."""

        payload = _model_to_mapping(report)
        _assert_safe_mapping(payload)

    def _build_official_pii_scan(self) -> PiiScanMetric:
        """Build official residual PII counters using the detector source of truth."""

        rows_scanned = 0
        residual_rows = 0
        category_rows: dict[str, int] = {category: 0 for category in PII_REPLACEMENTS}

        for summary, details in self._repository.iter_sanitized_text_pairs():
            rows_scanned += 1
            categories = _detect_residual_categories(summary, details)
            if categories:
                residual_rows += 1
                for category in categories:
                    category_rows[category] = category_rows.get(category, 0) + 1

        residual_categories = [
            PiiCategoryResidualMetric(category=category, rows_with_residual=count)
            for category, count in sorted(category_rows.items())
            if count > 0
        ]
        return PiiScanMetric(
            rows_scanned=rows_scanned,
            pii_residual_official_count=residual_rows,
            residual_detection_rate=_safe_rate(residual_rows, rows_scanned),
            residual_categories=residual_categories,
            heuristic_like_pattern_count=self._repository.get_heuristic_like_pattern_count(),
        )


def _model_to_mapping(report: AggregateTicketEdaReport) -> dict[str, Any]:
    """Convert a Pydantic report into a plain mapping across Pydantic versions."""

    if hasattr(report, "model_dump"):
        return report.model_dump()
    return report.dict()


def _assert_safe_mapping(value: Any) -> None:
    """Recursively reject forbidden output keys and sensitive marker values."""

    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = str(key).lower()
            if normalized_key in FORBIDDEN_OUTPUT_KEYS:
                raise ValueError("Forbidden output key detected in aggregate EDA report")
            _assert_safe_mapping(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_safe_mapping(item)
        return
    if isinstance(value, str):
        normalized_value = value.lower()
        if any(token in normalized_value for token in FORBIDDEN_OUTPUT_VALUE_TOKENS):
            raise ValueError("Forbidden output value marker detected in aggregate EDA report")


def _detect_residual_categories(summary: str, details: str) -> set[str]:
    """Return official detector categories present in sanitized text fields."""

    categories: set[str] = set()
    for text in (summary, details):
        categories.update(match.category for match in detect_pii(text))
    return categories


def _safe_rate(count: int, total: int) -> float:
    """Return a bounded aggregate rate."""

    if total <= 0:
        return 0.0
    return count / total
