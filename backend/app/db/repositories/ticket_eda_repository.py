"""Aggregate-only PostgreSQL repository for safe ticket EDA."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

from backend.app.schemas.ticket_eda import (
    DistributionBucket,
    DistributionMetric,
    FieldCompletenessMetric,
    PlaceholderMetric,
    TemporalBucket,
    TemporalDistribution,
    TextLengthMetric,
    TextQualityMetric,
)

ALLOWED_AGGREGATE_COLUMNS: frozenset[str] = frozenset(("status", "priority", "category", "ingested_at"))
INTERNAL_AGGREGATE_TEXT_COLUMNS: frozenset[str] = frozenset(("summary", "details"))
DENIED_EXPOSURE_COLUMNS: frozenset[str] = frozenset(
    ("summary", "details", "external_ticket_id", "agent_id_pseudonym", "payload")
)
KNOWN_PLACEHOLDERS: tuple[str, ...] = ("[EMAIL]", "[PHONE]", "[URL]", "[IP]", "[IDENTIFIER]")
TEXT_SCAN_BATCH_SIZE = 500


class AggregateTicketEdaRepository:
    """PostgreSQL reader returning aggregate metrics only."""

    _instance: "AggregateTicketEdaRepository | None" = None

    def __new__(cls, *args: object, **kwargs: object) -> "AggregateTicketEdaRepository":
        """Create a singleton repository instance."""

        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, connection_factory: Callable[[], Any]) -> None:
        if not hasattr(self, "_initialized"):
            self._connection_factory = connection_factory
            self._initialized = True

    def count_tickets(self) -> int:
        """Return the total number of clean tickets."""

        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(id) FROM clean_tickets")
                return int(cursor.fetchone()[0])

    def get_distribution(self, column: str) -> DistributionMetric:
        """Return anonymous aggregate distribution for an allowlisted column."""

        if column not in ALLOWED_AGGREGATE_COLUMNS - {"ingested_at"}:
            raise ValueError("Column is not approved for aggregate distribution")
        expression = f"NULLIF(BTRIM({column}), '')"
        sql = f"""
            SELECT ranked.bucket_rank, ranked.ticket_count
            FROM (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY COUNT(id) DESC, {expression} ASC) AS bucket_rank,
                    COUNT(id) AS ticket_count
                FROM clean_tickets
                WHERE {expression} IS NOT NULL
                GROUP BY {expression}
            ) AS ranked
            ORDER BY ranked.bucket_rank ASC
        """
        counts_sql = f"""
            SELECT
                COUNT(DISTINCT {expression}) AS non_null_distinct_count,
                COUNT(id) FILTER (WHERE {column} IS NULL) AS null_count,
                COUNT(id) FILTER (WHERE {column} IS NOT NULL AND BTRIM({column}) = '') AS missing_count
            FROM clean_tickets
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(counts_sql)
                counts = cursor.fetchone()
                cursor.execute(sql)
                buckets = [DistributionBucket(rank=int(row[0]), count=int(row[1])) for row in cursor.fetchall()]
        non_null_distinct_count = int(counts[0])
        return DistributionMetric(
            distinct_count=non_null_distinct_count,
            non_null_distinct_count=non_null_distinct_count,
            null_count=int(counts[1]),
            missing_count=int(counts[2]),
            buckets=buckets,
        )

    def get_text_quality(self, column: str) -> TextQualityMetric:
        """Return aggregate text quality metrics for an internal text column."""

        if column not in INTERNAL_AGGREGATE_TEXT_COLUMNS:
            raise ValueError("Text column is not approved for internal aggregate scanning")
        sql = f"""
            SELECT
                COALESCE(MIN(CHAR_LENGTH({column})), 0) AS min_length,
                COALESCE(AVG(CHAR_LENGTH({column})), 0) AS mean_length,
                COALESCE(MAX(CHAR_LENGTH({column})), 0) AS max_length,
                COALESCE((PERCENTILE_CONT(ARRAY[0.5, 0.9, 0.95, 0.99])
                    WITHIN GROUP (ORDER BY CHAR_LENGTH({column})))[1], 0) AS p50,
                COALESCE((PERCENTILE_CONT(ARRAY[0.5, 0.9, 0.95, 0.99])
                    WITHIN GROUP (ORDER BY CHAR_LENGTH({column})))[2], 0) AS p90,
                COALESCE((PERCENTILE_CONT(ARRAY[0.5, 0.9, 0.95, 0.99])
                    WITHIN GROUP (ORDER BY CHAR_LENGTH({column})))[3], 0) AS p95,
                COALESCE((PERCENTILE_CONT(ARRAY[0.5, 0.9, 0.95, 0.99])
                    WITHIN GROUP (ORDER BY CHAR_LENGTH({column})))[4], 0) AS p99,
                COALESCE(AVG(CASE WHEN BTRIM({column}) = '' THEN 1.0 ELSE 0.0 END), 0) AS empty_rate
            FROM clean_tickets
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
        length = TextLengthMetric(
            min=int(row[0]),
            mean=float(row[1]),
            max=int(row[2]),
            p50=float(row[3]),
            p90=float(row[4]),
            p95=float(row[5]),
            p99=float(row[6]),
        )
        return TextQualityMetric(length=length, empty_rate=float(row[7]))

    def get_fallback_untitled_ticket_rate(self) -> float:
        """Return aggregate rate of fallback title usage."""

        sql = """
            SELECT COALESCE(AVG(CASE WHEN LOWER(BTRIM(summary)) = 'untitled ticket' THEN 1.0 ELSE 0.0 END), 0)
            FROM clean_tickets
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                return float(cursor.fetchone()[0])

    def get_placeholder_metrics(self) -> list[PlaceholderMetric]:
        """Return aggregate placeholder counts across sanitized text columns."""

        total = self.count_tickets()
        metrics: list[PlaceholderMetric] = []
        sql = """
            SELECT COUNT(id)
            FROM clean_tickets
            WHERE POSITION(%s IN summary) > 0 OR POSITION(%s IN details) > 0
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                for placeholder in KNOWN_PLACEHOLDERS:
                    cursor.execute(sql, (placeholder, placeholder))
                    count = int(cursor.fetchone()[0])
                    metrics.append(
                        PlaceholderMetric(
                            placeholder=placeholder,
                            rows_with_placeholder=count,
                            rate=_safe_rate(count, total),
                        )
                    )
        return metrics

    def get_temporal_distribution(self) -> TemporalDistribution:
        """Return aggregate daily and weekly ingestion distributions."""

        day_sql = """
            SELECT TO_CHAR(DATE_TRUNC('day', ingested_at), 'YYYY-MM-DD') AS period, COUNT(id)
            FROM clean_tickets
            GROUP BY DATE_TRUNC('day', ingested_at)
            ORDER BY DATE_TRUNC('day', ingested_at) ASC
        """
        week_sql = """
            SELECT TO_CHAR(DATE_TRUNC('week', ingested_at), 'IYYY-IW') AS period, COUNT(id)
            FROM clean_tickets
            GROUP BY DATE_TRUNC('week', ingested_at)
            ORDER BY DATE_TRUNC('week', ingested_at) ASC
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(day_sql)
                by_day = [TemporalBucket(period=str(row[0]), count=int(row[1])) for row in cursor.fetchall()]
                cursor.execute(week_sql)
                by_week = [TemporalBucket(period=str(row[0]), count=int(row[1])) for row in cursor.fetchall()]
        return TemporalDistribution(by_day=by_day, by_week=by_week)

    def get_heuristic_like_pattern_count(self) -> int:
        """Return legacy SQL heuristic-like pattern count for diagnostics only."""

        email_pattern = r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}"
        phone_pattern = r"(\+?[0-9][0-9 .()/-]{7,}[0-9])"
        ip_pattern = r"\m(?:[0-9]{1,3}\.){3}[0-9]{1,3}\M"
        sql = """
            SELECT COUNT(id) FILTER (
                WHERE summary ~* %s OR details ~* %s
                   OR summary ~* %s OR details ~* %s
                   OR summary ~* %s OR details ~* %s
            ) AS rows_with_heuristic_like_pattern
            FROM clean_tickets
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    (email_pattern, email_pattern, phone_pattern, phone_pattern, ip_pattern, ip_pattern),
                )
                row = cursor.fetchone()
        return int(row[0])

    def iter_sanitized_text_pairs(self, batch_size: int = TEXT_SCAN_BATCH_SIZE) -> Iterator[tuple[str, str]]:
        """Yield sanitized text fields for official in-memory aggregate scans only."""

        if batch_size <= 0:
            raise ValueError("Batch size must be positive")
        sql = """
            SELECT COALESCE(summary, ''), COALESCE(details, '')
            FROM clean_tickets
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    for row in rows:
                        yield (str(row[0]), str(row[1]))

    def get_completeness(self) -> list[FieldCompletenessMetric]:
        """Return completeness metrics for output-safe fields only."""

        total = self.count_tickets()
        sql = """
            SELECT
                COUNT(id) FILTER (WHERE status IS NOT NULL AND BTRIM(status) <> '') AS status_count,
                COUNT(id) FILTER (WHERE status IS NULL) AS status_null_count,
                COUNT(id) FILTER (WHERE status IS NOT NULL AND BTRIM(status) = '') AS status_missing_count,
                COUNT(id) FILTER (WHERE priority IS NOT NULL AND BTRIM(priority) <> '') AS priority_count,
                COUNT(id) FILTER (WHERE priority IS NULL) AS priority_null_count,
                COUNT(id) FILTER (WHERE priority IS NOT NULL AND BTRIM(priority) = '') AS priority_missing_count,
                COUNT(id) FILTER (WHERE category IS NOT NULL AND BTRIM(category) <> '') AS category_count,
                COUNT(id) FILTER (WHERE category IS NULL) AS category_null_count,
                COUNT(id) FILTER (WHERE category IS NOT NULL AND BTRIM(category) = '') AS category_missing_count,
                COUNT(id) FILTER (WHERE ingested_at IS NOT NULL) AS time_count,
                COUNT(id) FILTER (WHERE ingested_at IS NULL) AS time_null_count,
                0 AS time_missing_count
            FROM clean_tickets
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
        fields = (
            ("status", row[0], row[1], row[2]),
            ("priority", row[3], row[4], row[5]),
            ("category", row[6], row[7], row[8]),
            ("ingestion_time", row[9], row[10], row[11]),
        )
        return [
            FieldCompletenessMetric(
                field=field,
                populated_count=int(count),
                null_count=int(null_count),
                missing_count=int(missing_count),
                completeness_rate=_safe_rate(int(count), total),
            )
            for field, count, null_count, missing_count in fields
        ]


def _safe_rate(count: int, total: int) -> float:
    """Return a bounded aggregate rate."""

    if total <= 0:
        return 0.0
    return count / total
