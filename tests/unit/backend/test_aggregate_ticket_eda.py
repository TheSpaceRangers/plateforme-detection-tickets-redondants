"""Official QA tests for secure aggregate-only ticket EDA tooling."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from backend.app.data.commands import aggregate_ticket_eda
from backend.app.db.repositories.ticket_eda_repository import AggregateTicketEdaRepository
from backend.app.schemas.ticket_eda import (
    AggregateTicketEdaReport,
    DistributionBucket,
    DistributionMetric,
    FieldCompletenessMetric,
    PiiCategoryResidualMetric,
    PiiScanMetric,
    PlaceholderMetric,
    TemporalBucket,
    TemporalDistribution,
    TemporalFieldMetric,
    TicketCreatedTemporalBuckets,
    TextLengthMetric,
    TextQualityMetric,
)
from backend.app.services.ticket_eda_service import AggregateTicketEdaService


FORBIDDEN_KEYS = {"summary", "details", "external_ticket_id", "agent_id_pseudonym", "payload"}
FORBIDDEN_TEXT_MARKERS = FORBIDDEN_KEYS | {"raw ticket text", "secret"}
REMOVED_PII_SCAN_FIELDS = {"rows_with_pii_detected", "detection_rate"}
WRITE_SQL_RE = re.compile(r"\b(insert|update|delete|merge|copy|create|alter|drop|truncate)\b", re.IGNORECASE)


@pytest.fixture(autouse=True)
def reset_singletons() -> None:
    """Arrange: reset backend singletons to isolate official QA tests."""

    AggregateTicketEdaRepository._instance = None
    AggregateTicketEdaService._instance = None


def safe_report() -> AggregateTicketEdaReport:
    """Arrange helper returning a complete aggregate-only report."""

    length = TextLengthMetric(min=0, mean=12.5, max=30, p50=10, p90=20, p95=25, p99=30)
    return AggregateTicketEdaReport(
        total_tickets=4,
        status_distribution=DistributionMetric(
            distinct_count=2,
            non_null_distinct_count=2,
            null_count=0,
            missing_count=0,
            buckets=[DistributionBucket(rank=1, count=3), DistributionBucket(rank=2, count=1)],
        ),
        priority_distribution=DistributionMetric(
            distinct_count=1,
            non_null_distinct_count=1,
            null_count=1,
            missing_count=1,
            buckets=[DistributionBucket(rank=1, count=2)],
        ),
        category_distribution=DistributionMetric(
            distinct_count=2,
            non_null_distinct_count=2,
            null_count=0,
            missing_count=1,
            buckets=[DistributionBucket(rank=1, count=2)],
        ),
        short_text=TextQualityMetric(length=length, empty_rate=0.25),
        long_text=TextQualityMetric(length=length, empty_rate=0.0),
        fallback_untitled_ticket_rate=0.25,
        placeholder_counts=[PlaceholderMetric(placeholder="[EMAIL]", rows_with_placeholder=1, rate=0.25)],
        temporal_distribution=TemporalDistribution(
            ticket_created_at=TemporalFieldMetric(min_at="2026-01-01T00:00:00Z", max_at="2026-02-01T00:00:00Z", populated_count=4, null_count=0, missing_count=0),
            ticket_updated_at=TemporalFieldMetric(min_at=None, max_at=None, populated_count=0, null_count=4, missing_count=4),
            ticket_closed_at=TemporalFieldMetric(min_at=None, max_at=None, populated_count=0, null_count=4, missing_count=4),
            ingested_at=TemporalFieldMetric(min_at="2026-06-01T00:00:00Z", max_at="2026-06-02T00:00:00Z", populated_count=4, null_count=0, missing_count=0),
            ticket_created_buckets=TicketCreatedTemporalBuckets(
                by_month=[TemporalBucket(period="2026-01", count=4)],
                by_year=[TemporalBucket(period="2026", count=4)],
            ),
        ),
        pii_scan=PiiScanMetric(
            rows_scanned=4,
            pii_residual_official_count=1,
            residual_detection_rate=0.25,
            residual_categories=[PiiCategoryResidualMetric(category="EMAIL", rows_with_residual=1)],
            heuristic_like_pattern_count=2,
        ),
        completeness=[FieldCompletenessMetric(field="status", populated_count=3, null_count=1, missing_count=0, completeness_rate=0.75)],
    )


def model_to_dict(model: Any) -> dict[str, Any]:
    """Arrange helper compatible with Pydantic v1/v2."""

    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def assert_no_forbidden_content(value: Any) -> None:
    """Assert recursively that serialized output exposes no denied keys or raw markers."""

    if isinstance(value, dict):
        assert FORBIDDEN_KEYS.isdisjoint({str(key).lower() for key in value})
        for item in value.values():
            assert_no_forbidden_content(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_forbidden_content(item)
    elif isinstance(value, str):
        normalized = value.lower()
        assert not any(marker in normalized for marker in FORBIDDEN_TEXT_MARKERS)


class SyntheticPiiMatch:
    """Synthetic detector match exposing only an aggregate category."""

    def __init__(self, category: str) -> None:
        self.category = category


def test_report_json_contains_no_forbidden_keys_or_raw_sensitive_markers() -> None:
    # Arrange
    report = safe_report()

    # Act
    payload = json.loads(aggregate_ticket_eda._report_to_json(report))

    # Assert
    assert_no_forbidden_content(payload)


def test_service_validation_rejects_injected_forbidden_key() -> None:
    # Arrange
    class InjectedForbiddenReport:
        def model_dump(self) -> dict[str, Any]:
            return {"total_tickets": 1, "nested": [{"summary": "raw ticket text"}]}

    service = AggregateTicketEdaService(repository=object())

    # Act / Assert
    with pytest.raises(ValueError, match="Forbidden output key"):
        service.validate_no_forbidden_output(InjectedForbiddenReport())  # type: ignore[arg-type]


class FakeCursor:
    """Fake PostgreSQL cursor returning aggregate rows and recording SQL."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple[Any, ...] | None]] = []
        self._fetchone_queue: list[tuple[Any, ...]] = [
            (7,),
            (2, 1, 1),
            (0, 10.5, 42, 9.0, 20.0, 30.0, 40.0, 0.1),
            (0.2,),
            (7,),
            (2,),
            (1,),
            (0,),
            (3,),
            (1,),
            ("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", 6, 1),
            ("2026-01-02T00:00:00Z", "2026-02-02T00:00:00Z", 5, 2),
            (None, None, 0, 7),
            ("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z", 7, 0),
            (2,),
            (7,),
            (5, 1, 1, 6, 1, 0, 4, 2, 1, 7, 0, 6, 1, 0, 7, 7, 0, 0),
        ]
        self._fetchall_queue: list[list[tuple[Any, ...]]] = [
            [(1, 4), (2, 3)],
            [("2026-01", 4), ("2026-02", 3)],
            [("2026", 7)],
        ]

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        self.statements.append((sql, params))

    def fetchone(self) -> tuple[Any, ...]:
        return self._fetchone_queue.pop(0)

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self._fetchall_queue.pop(0)

    def fetchmany(self, size: int) -> list[tuple[Any, ...]]:
        return []


class FakeConnection:
    """Fake PostgreSQL connection exposing one fake cursor."""

    def __init__(self, cursor: FakeCursor) -> None:
        self._cursor = cursor

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self._cursor


def test_repository_uses_read_only_aggregate_sql_with_fake_cursor() -> None:
    # Arrange
    cursor = FakeCursor()
    repository = AggregateTicketEdaRepository(connection_factory=lambda: FakeConnection(cursor))

    # Act
    assert repository.count_tickets() == 7
    assert repository.get_distribution("status").distinct_count == 2
    assert repository.get_text_quality("summary").length.max == 42
    assert repository.get_fallback_untitled_ticket_rate() == 0.2
    assert len(repository.get_placeholder_metrics()) == 5
    temporal_distribution = repository.get_temporal_distribution()
    assert temporal_distribution.ticket_created_at.populated_count == 6
    assert temporal_distribution.ingested_at.populated_count == 7
    assert temporal_distribution.ticket_created_buckets.by_year[0].count == 7
    assert repository.get_heuristic_like_pattern_count() == 2
    assert repository.get_completeness()[0].field == "status"

    # Assert
    statements = [sql.lower() for sql, _params in cursor.statements]
    assert statements
    assert all("select *" not in sql for sql in statements)
    assert all(not WRITE_SQL_RE.search(sql) for sql in statements)
    assert all("external_ticket_id" not in sql and "agent_id_pseudonym" not in sql and "payload" not in sql for sql in statements)
    for sql in statements:
        if "summary" in sql or "details" in sql:
            assert any(token in sql for token in ("char_length", "btrim", "position", "~*", "lower"))


def test_repository_rejects_forbidden_distribution_column() -> None:
    # Arrange
    repository = AggregateTicketEdaRepository(connection_factory=lambda: FakeConnection(FakeCursor()))

    # Act / Assert
    with pytest.raises(ValueError, match="not approved"):
        repository.get_distribution("external_ticket_id")


def test_repository_temporal_distribution_uses_business_dates_separately_from_ingestion_time() -> None:
    # Arrange
    cursor = FakeCursor()
    cursor._fetchone_queue = [
        ("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", 6, 1),
        ("2026-01-02T00:00:00Z", "2026-02-02T00:00:00Z", 5, 2),
        (None, None, 0, 7),
        ("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z", 7, 0),
    ]
    cursor._fetchall_queue = [[("2026-01", 4), ("2026-02", 3)], [("2026", 7)]]
    repository = AggregateTicketEdaRepository(connection_factory=lambda: FakeConnection(cursor))

    # Act
    temporal_distribution = repository.get_temporal_distribution()

    # Assert
    assert temporal_distribution.ticket_created_at.min_at == "2026-01-01T00:00:00Z"
    assert temporal_distribution.ingested_at.min_at == "2026-06-01T00:00:00Z"
    assert temporal_distribution.ticket_created_buckets.by_month[0].period == "2026-01"
    statements = [sql.lower() for sql, _params in cursor.statements]
    assert any("min(ticket_created_at)" in sql and "max(ticket_created_at)" in sql for sql in statements)
    assert any("min(ingested_at)" in sql and "max(ingested_at)" in sql for sql in statements)
    assert any("date_trunc(%s, ticket_created_at)" in sql for sql in statements)


def test_repository_rejects_unsupported_ticket_created_bucket_granularity() -> None:
    # Arrange
    repository = AggregateTicketEdaRepository(connection_factory=lambda: FakeConnection(FakeCursor()))

    # Act / Assert
    with pytest.raises(ValueError, match="Unsupported"):
        repository.get_ticket_created_buckets("day")


class SyntheticRepository:
    """Repository mock returning deterministic synthetic aggregate metrics."""

    def count_tickets(self) -> int:
        return 4

    def get_distribution(self, column: str) -> DistributionMetric:
        distributions = {
            "status": DistributionMetric(
                distinct_count=2,
                non_null_distinct_count=2,
                null_count=0,
                missing_count=0,
                buckets=[DistributionBucket(rank=1, count=3), DistributionBucket(rank=2, count=1)],
            ),
            "priority": DistributionMetric(
                distinct_count=2,
                non_null_distinct_count=2,
                null_count=1,
                missing_count=1,
                buckets=[DistributionBucket(rank=1, count=1), DistributionBucket(rank=2, count=1)],
            ),
            "category": DistributionMetric(
                distinct_count=1,
                non_null_distinct_count=1,
                null_count=1,
                missing_count=0,
                buckets=[DistributionBucket(rank=1, count=3)],
            ),
        }
        return distributions[column]

    def get_text_quality(self, column: str) -> TextQualityMetric:
        metrics = {
            "summary": TextQualityMetric(
                length=TextLengthMetric(min=0, mean=8.0, max=16, p50=8, p90=14, p95=15, p99=16),
                empty_rate=0.25,
            ),
            "details": TextQualityMetric(
                length=TextLengthMetric(min=10, mean=20.0, max=40, p50=18, p90=35, p95=38, p99=40),
                empty_rate=0.0,
            ),
        }
        return metrics[column]

    def get_fallback_untitled_ticket_rate(self) -> float:
        return 0.25

    def get_placeholder_metrics(self) -> list[PlaceholderMetric]:
        return [PlaceholderMetric(placeholder="[PHONE]", rows_with_placeholder=2, rate=0.5)]

    def get_temporal_distribution(self) -> TemporalDistribution:
        return TemporalDistribution(
            ticket_created_at=TemporalFieldMetric(min_at="2026-01-01T00:00:00Z", max_at="2026-02-01T00:00:00Z", populated_count=3, null_count=1, missing_count=1),
            ticket_updated_at=TemporalFieldMetric(min_at=None, max_at=None, populated_count=0, null_count=4, missing_count=4),
            ticket_closed_at=TemporalFieldMetric(min_at=None, max_at=None, populated_count=0, null_count=4, missing_count=4),
            ingested_at=TemporalFieldMetric(min_at="2026-06-01T00:00:00Z", max_at="2026-06-02T00:00:00Z", populated_count=4, null_count=0, missing_count=0),
            ticket_created_buckets=TicketCreatedTemporalBuckets(
                by_month=[TemporalBucket(period="2026-01", count=1), TemporalBucket(period="2026-02", count=3)],
                by_year=[TemporalBucket(period="2026", count=4)],
            ),
        )

    def get_heuristic_like_pattern_count(self) -> int:
        return 2

    def iter_sanitized_text_pairs(self, batch_size: int = 500) -> Any:
        return iter((("[EMAIL]", "[PHONE]"), ("synthetic-residual", ""), ("[URL]", "[IP]"), ("", "")))

    def get_completeness(self) -> list[FieldCompletenessMetric]:
        return [
            FieldCompletenessMetric(field="status", populated_count=4, null_count=0, missing_count=0, completeness_rate=1.0),
            FieldCompletenessMetric(field="priority", populated_count=2, null_count=1, missing_count=1, completeness_rate=0.5),
            FieldCompletenessMetric(field="category", populated_count=3, null_count=1, missing_count=0, completeness_rate=0.75),
            FieldCompletenessMetric(field="ticket_created_at", populated_count=3, null_count=1, missing_count=1, completeness_rate=0.75),
            FieldCompletenessMetric(field="ticket_updated_at", populated_count=0, null_count=4, missing_count=4, completeness_rate=0.0),
            FieldCompletenessMetric(field="ticket_closed_at", populated_count=0, null_count=4, missing_count=4, completeness_rate=0.0),
            FieldCompletenessMetric(field="ingested_at", populated_count=4, null_count=0, missing_count=0, completeness_rate=1.0),
        ]


def test_service_calculates_synthetic_aggregate_metrics_from_repository_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    def synthetic_detect_pii(text: str) -> list[SyntheticPiiMatch]:
        return [SyntheticPiiMatch("EMAIL")] if text == "synthetic-residual" else []

    monkeypatch.setattr("backend.app.services.ticket_eda_service.detect_pii", synthetic_detect_pii)
    service = AggregateTicketEdaService(repository=SyntheticRepository())

    # Act
    report = service.build_report()

    # Assert
    assert report.total_tickets == 4
    assert report.status_distribution.buckets[0].count == 3
    assert report.priority_distribution.null_count == 1
    assert report.priority_distribution.missing_count == 1
    assert report.priority_distribution.non_null_distinct_count == 2
    assert report.short_text.length.mean == 8.0
    assert report.long_text.length.p99 == 40
    assert report.fallback_untitled_ticket_rate == 0.25
    assert report.placeholder_counts[0].rate == 0.5
    assert report.temporal_distribution.ticket_created_buckets.by_month[1].period == "2026-02"
    assert report.temporal_distribution.ingested_at.populated_count == 4
    assert report.pii_scan.pii_residual_official_count == 1
    assert report.pii_scan.residual_detection_rate == 0.25
    assert report.pii_scan.heuristic_like_pattern_count == 2
    assert report.completeness[1].completeness_rate == 0.5
    payload = model_to_dict(report)
    assert REMOVED_PII_SCAN_FIELDS.isdisjoint(payload["pii_scan"])
    assert_no_forbidden_content(payload)


def test_placeholders_are_not_official_residual_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    class PlaceholderOnlyRepository(SyntheticRepository):
        def iter_sanitized_text_pairs(self, batch_size: int = 500) -> Any:
            return iter((("[EMAIL]", "[PHONE]"), ("[URL]", "[IP]")))

    detector_calls: list[str] = []

    def synthetic_detect_pii(text: str) -> list[SyntheticPiiMatch]:
        detector_calls.append(text)
        return []

    monkeypatch.setattr("backend.app.services.ticket_eda_service.detect_pii", synthetic_detect_pii)
    service = AggregateTicketEdaService(repository=PlaceholderOnlyRepository())

    # Act
    pii_scan = service.build_report().pii_scan
    payload = model_to_dict(pii_scan)

    # Assert
    assert detector_calls
    assert pii_scan.rows_scanned == 2
    assert pii_scan.pii_residual_official_count == 0
    assert pii_scan.residual_detection_rate == 0.0
    assert pii_scan.residual_categories == []
    assert REMOVED_PII_SCAN_FIELDS.isdisjoint(payload)
    assert_no_forbidden_content(payload)


def test_official_detector_counts_only_synthetic_residual_pii(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    def synthetic_detect_pii(text: str) -> list[SyntheticPiiMatch]:
        return [SyntheticPiiMatch("PHONE")] if text == "synthetic-residual" else []

    monkeypatch.setattr("backend.app.services.ticket_eda_service.detect_pii", synthetic_detect_pii)
    service = AggregateTicketEdaService(repository=SyntheticRepository())

    # Act
    pii_scan = service.build_report().pii_scan

    # Assert
    assert pii_scan.rows_scanned == 4
    assert pii_scan.pii_residual_official_count == 1
    assert pii_scan.residual_detection_rate == 0.25
    assert [(item.category, item.rows_with_residual) for item in pii_scan.residual_categories] == [("PHONE", 1)]


def test_priority_and_category_separate_null_missing_and_non_null_distribution() -> None:
    # Arrange
    repository = SyntheticRepository()

    # Act
    priority = repository.get_distribution("priority")
    category = repository.get_distribution("category")

    # Assert
    assert priority.null_count == 1
    assert priority.missing_count == 1
    assert priority.non_null_distinct_count == 2
    assert sum(bucket.count for bucket in priority.buckets) == 2
    assert category.null_count == 1
    assert category.missing_count == 0
    assert category.non_null_distinct_count == 1
    assert sum(bucket.count for bucket in category.buckets) == 3


def test_command_writes_no_file_and_outputs_safe_json(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    report = safe_report()
    write_attempts: list[str] = []

    def fail_on_write(*args: Any, **kwargs: Any) -> None:
        write_attempts.append("write")
        raise AssertionError("file write is forbidden during aggregate EDA command")

    monkeypatch.setattr(aggregate_ticket_eda, "load_local_dotenv", lambda **_kwargs: False)
    monkeypatch.setattr(aggregate_ticket_eda, "run_aggregate_ticket_eda", lambda *, env: report)
    monkeypatch.setattr(aggregate_ticket_eda.Path, "write_text", fail_on_write)
    monkeypatch.setattr(aggregate_ticket_eda.Path, "write_bytes", fail_on_write)

    # Act
    exit_code = aggregate_ticket_eda.main(dotenv_loader=lambda *_args, **_kwargs: False)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    # Assert
    assert exit_code == 0
    assert captured.err == ""
    assert write_attempts == []
    assert_no_forbidden_content(payload)


def test_command_returns_blocked_error_without_forbidden_fields_on_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    monkeypatch.setattr(aggregate_ticket_eda, "load_local_dotenv", lambda **_kwargs: False)
    monkeypatch.setattr(
        aggregate_ticket_eda,
        "run_aggregate_ticket_eda",
        lambda *, env: (_ for _ in ()).throw(aggregate_ticket_eda.AggregateTicketEdaCommandError("safe failure")),
    )

    # Act
    exit_code = aggregate_ticket_eda.main(dotenv_loader=lambda *_args, **_kwargs: False)
    captured = capsys.readouterr()
    payload = json.loads(captured.err)

    # Assert
    assert exit_code == 2
    assert captured.out == ""
    assert payload == {"error": "aggregate_ticket_eda_blocked", "reason": "safe failure"}
    assert_no_forbidden_content(payload)
