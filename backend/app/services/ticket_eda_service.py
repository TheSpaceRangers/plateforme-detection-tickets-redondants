"""Service layer for secure aggregate ticket EDA."""

from __future__ import annotations

from typing import Any, Protocol

from backend.app.schemas.ticket_eda import AggregateTicketEdaReport

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

    def get_pii_scan(self) -> Any:
        """Return aggregate PII scan metrics."""

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
            placeholders=self._repository.get_placeholder_metrics(),
            temporal_distribution=self._repository.get_temporal_distribution(),
            pii_scan=self._repository.get_pii_scan(),
            completeness=self._repository.get_completeness(),
        )
        self.validate_no_forbidden_output(report)
        return report

    def validate_no_forbidden_output(self, report: AggregateTicketEdaReport) -> None:
        """Fail closed if report keys or string values include forbidden exposure markers."""

        payload = _model_to_mapping(report)
        _assert_safe_mapping(payload)


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
