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
    PiiScanMetric,
    PlaceholderMetric,
    TemporalBucket,
    TemporalDistribution,
    TextLengthMetric,
    TextQualityMetric,
)
from backend.app.services.ticket_eda_service import AggregateTicketEdaService


FORBIDDEN_KEYS = {"summary", "details", "external_ticket_id", "agent_id_pseudonym", "payload"}
FORBIDDEN_TEXT_MARKERS = FORBIDDEN_KEYS | {"john@example.test", "+33123456789", "raw ticket text", "secret"}
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
            buckets=[DistributionBucket(rank=1, count=3), DistributionBucket(rank=2, count=1)],
        ),
        priority_distribution=DistributionMetric(distinct_count=1, buckets=[DistributionBucket(rank=1, count=4)]),
        category_distribution=DistributionMetric(distinct_count=2, buckets=[DistributionBucket(rank=1, count=2)]),
        short_text=TextQualityMetric(length=length, empty_rate=0.25),
        long_text=TextQualityMetric(length=length, empty_rate=0.0),
        fallback_untitled_ticket_rate=0.25,
        placeholders=[PlaceholderMetric(placeholder="[EMAIL]", rows_with_placeholder=1, rate=0.25)],
        temporal_distribution=TemporalDistribution(
            by_day=[TemporalBucket(period="2026-06-01", count=4)],
            by_week=[TemporalBucket(period="2026-23", count=4)],
        ),
        pii_scan=PiiScanMetric(rows_scanned=4, rows_with_pii_detected=1, detection_rate=0.25),
        completeness=[FieldCompletenessMetric(field="status", populated_count=3, completeness_rate=0.75)],
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
            (2,),
            (0, 10.5, 42, 9.0, 20.0, 30.0, 40.0, 0.1),
            (0.2,),
            (7,),
            (2,),
            (1,),
            (0,),
            (3,),
            (1,),
            (7, 2),
            (7,),
            (5, 6, 4, 7),
        ]
        self._fetchall_queue: list[list[tuple[Any, ...]]] = [
            [(1, 4), (2, 3)],
            [("2026-06-01", 4), ("2026-06-02", 3)],
            [("2026-23", 7)],
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
    assert repository.get_temporal_distribution().by_week[0].count == 7
    assert repository.get_pii_scan().rows_with_pii_detected == 2
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


class SyntheticRepository:
    """Repository mock returning deterministic synthetic aggregate metrics."""

    def count_tickets(self) -> int:
        return 4

    def get_distribution(self, column: str) -> DistributionMetric:
        distributions = {
            "status": DistributionMetric(distinct_count=2, buckets=[DistributionBucket(rank=1, count=3), DistributionBucket(rank=2, count=1)]),
            "priority": DistributionMetric(distinct_count=2, buckets=[DistributionBucket(rank=1, count=2), DistributionBucket(rank=2, count=2)]),
            "category": DistributionMetric(distinct_count=1, buckets=[DistributionBucket(rank=1, count=4)]),
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
            by_day=[TemporalBucket(period="2026-06-01", count=1), TemporalBucket(period="2026-06-02", count=3)],
            by_week=[TemporalBucket(period="2026-23", count=4)],
        )

    def get_pii_scan(self) -> PiiScanMetric:
        return PiiScanMetric(rows_scanned=4, rows_with_pii_detected=2, detection_rate=0.5)

    def get_completeness(self) -> list[FieldCompletenessMetric]:
        return [
            FieldCompletenessMetric(field="status", populated_count=4, completeness_rate=1.0),
            FieldCompletenessMetric(field="priority", populated_count=3, completeness_rate=0.75),
            FieldCompletenessMetric(field="category", populated_count=2, completeness_rate=0.5),
            FieldCompletenessMetric(field="ingestion_time", populated_count=4, completeness_rate=1.0),
        ]


def test_service_calculates_synthetic_aggregate_metrics_from_repository_mock() -> None:
    # Arrange
    service = AggregateTicketEdaService(repository=SyntheticRepository())

    # Act
    report = service.build_report()

    # Assert
    assert report.total_tickets == 4
    assert report.status_distribution.buckets[0].count == 3
    assert report.priority_distribution.distinct_count == 2
    assert report.short_text.length.mean == 8.0
    assert report.long_text.length.p99 == 40
    assert report.fallback_untitled_ticket_rate == 0.25
    assert report.placeholders[0].rate == 0.5
    assert report.temporal_distribution.by_day[1].period == "2026-06-02"
    assert report.pii_scan.detection_rate == 0.5
    assert report.completeness[1].completeness_rate == 0.75
    assert_no_forbidden_content(model_to_dict(report))


def test_pii_scan_is_aggregate_only_and_does_not_expose_matches_or_source_text() -> None:
    # Arrange
    cursor = FakeCursor()
    repository = AggregateTicketEdaRepository(connection_factory=lambda: FakeConnection(cursor))
    cursor._fetchone_queue = [(10, 3)]

    # Act
    pii_scan = repository.get_pii_scan()
    payload = model_to_dict(pii_scan)

    # Assert
    assert payload == {"rows_scanned": 10, "rows_with_pii_detected": 3, "detection_rate": 0.3}
    assert_no_forbidden_content(payload)
    assert all(params is not None for _sql, params in cursor.statements)
    assert all("john@example.test" not in str(params) and "+33123456789" not in str(params) for _sql, params in cursor.statements)


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
