"""Aggregate-only PostgreSQL repository for safe ticket EDA."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from typing import Any

from backend.app.schemas.ticket_eda import (
    DistributionBucket,
    DistributionMetric,
    FieldCompletenessMetric,
    PlaceholderMetric,
    TemporalFieldMetric,
    TemporalBucket,
    TemporalDistribution,
    TicketCreatedTemporalBuckets,
    TextLengthMetric,
    TextQualityMetric,
)

ALLOWED_AGGREGATE_COLUMNS: frozenset[str] = frozenset(("status", "priority", "category"))
ALLOWED_TEMPORAL_COLUMNS: frozenset[str] = frozenset(
    ("ticket_created_at", "ticket_updated_at", "ticket_closed_at", "ingested_at")
)
INTERNAL_AGGREGATE_TEXT_COLUMNS: frozenset[str] = frozenset(("summary", "details"))
DENIED_EXPOSURE_COLUMNS: frozenset[str] = frozenset(
    ("summary", "details", "external_ticket_id", "agent_id_pseudonym", "payload")
)
KNOWN_PLACEHOLDERS: tuple[str, ...] = ("[EMAIL]", "[PHONE]", "[URL]", "[IP]", "[IDENTIFIER]")
TEXT_SCAN_BATCH_SIZE = 500
DEFAULT_MIN_TICKET_CREATED_AT = date(2025, 1, 1)


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
            self._min_ticket_created_at = DEFAULT_MIN_TICKET_CREATED_AT
            self._initialized = True

    def count_tickets(self) -> int:
        """Return the number of clean tickets included in filtered EDA metrics."""

        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(id) FROM clean_tickets WHERE ticket_created_at >= %s",
                    (self._min_ticket_created_at,),
                )
                return int(cursor.fetchone()[0])

    def count_source_tickets(self) -> int:
        """Return the unfiltered number of clean tickets available at source."""

        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(id) FROM clean_tickets")
                return int(cursor.fetchone()[0])

    def count_historical_outlier_tickets(self) -> int:
        """Return tickets excluded by the default historical outlier boundary."""

        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(id) FROM clean_tickets WHERE ticket_created_at < %s",
                    (self._min_ticket_created_at,),
                )
                return int(cursor.fetchone()[0])

    def count_missing_ticket_created_at_tickets(self) -> int:
        """Return source tickets excluded because ticket_created_at is missing."""

        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(id) FROM clean_tickets WHERE ticket_created_at IS NULL")
                return int(cursor.fetchone()[0])

    def get_applied_min_ticket_created_at(self) -> str:
        """Return the inclusive ticket_created_at date applied to all filtered EDA metrics."""

        return self._min_ticket_created_at.isoformat()

    def get_distribution(self, column: str) -> DistributionMetric:
        """Return anonymous aggregate distribution for an allowlisted column."""

        if column not in ALLOWED_AGGREGATE_COLUMNS:
            raise ValueError("Column is not approved for aggregate distribution")
        expression = f"NULLIF(BTRIM({column}), '')"
        sql = f"""
            SELECT ranked.bucket_rank, ranked.ticket_count
            FROM (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY COUNT(id) DESC, {expression} ASC) AS bucket_rank,
                    COUNT(id) AS ticket_count
                FROM clean_tickets
                WHERE ticket_created_at >= %s AND {expression} IS NOT NULL
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
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(counts_sql, (self._min_ticket_created_at,))
                counts = cursor.fetchone()
                cursor.execute(sql, (self._min_ticket_created_at,))
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
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (self._min_ticket_created_at,))
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
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (self._min_ticket_created_at,))
                return float(cursor.fetchone()[0])

    def get_placeholder_metrics(self) -> list[PlaceholderMetric]:
        """Return aggregate placeholder counts across sanitized text columns."""

        total = self.count_tickets()
        metrics: list[PlaceholderMetric] = []
        sql = """
            SELECT COUNT(id)
            FROM clean_tickets
            WHERE ticket_created_at >= %s AND (POSITION(%s IN summary) > 0 OR POSITION(%s IN details) > 0)
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                for placeholder in KNOWN_PLACEHOLDERS:
                    cursor.execute(sql, (self._min_ticket_created_at, placeholder, placeholder))
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
        """Return aggregate temporal metrics without using ingestion as business proxy."""

        return TemporalDistribution(
            ticket_created_at=self.get_temporal_field_metric("ticket_created_at"),
            ticket_updated_at=self.get_temporal_field_metric("ticket_updated_at"),
            ticket_closed_at=self.get_temporal_field_metric("ticket_closed_at"),
            ingested_at=self.get_temporal_field_metric("ingested_at"),
            ticket_created_buckets=TicketCreatedTemporalBuckets(
                by_month=self.get_ticket_created_buckets("month"),
                by_year=self.get_ticket_created_buckets("year"),
            ),
        )

    def get_temporal_field_metric(self, column: str) -> TemporalFieldMetric:
        """Return min/max and null counts for an allowlisted timestamp column."""

        if column not in ALLOWED_TEMPORAL_COLUMNS:
            raise ValueError("Column is not approved for temporal metrics")
        sql = f"""
            SELECT
                TO_CHAR(MIN({column}) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                TO_CHAR(MAX({column}) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                COUNT(id) FILTER (WHERE {column} IS NOT NULL),
                COUNT(id) FILTER (WHERE {column} IS NULL)
            FROM clean_tickets
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (self._min_ticket_created_at,))
                row = cursor.fetchone()
        return TemporalFieldMetric(
            min_at=str(row[0]) if row[0] is not None else None,
            max_at=str(row[1]) if row[1] is not None else None,
            populated_count=int(row[2]),
            null_count=int(row[3]),
            missing_count=int(row[3]),
        )

    def get_ticket_created_buckets(self, granularity: str) -> list[TemporalBucket]:
        """Return month or year buckets based on ticket_created_at only."""

        format_mask = _ticket_created_bucket_format(granularity)
        sql = f"""
            WITH bucketed_tickets AS (
                SELECT DATE_TRUNC(%s, ticket_created_at) AS bucket_start
                FROM clean_tickets
                WHERE ticket_created_at >= %s
            )
            SELECT TO_CHAR(bucket_start, '{format_mask}') AS period, COUNT(*) AS ticket_count
            FROM bucketed_tickets
            GROUP BY bucket_start
            ORDER BY bucket_start ASC
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (granularity, self._min_ticket_created_at))
                return [TemporalBucket(period=str(row[0]), count=int(row[1])) for row in cursor.fetchall()]

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
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        email_pattern,
                        email_pattern,
                        phone_pattern,
                        phone_pattern,
                        ip_pattern,
                        ip_pattern,
                        self._min_ticket_created_at,
                    ),
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
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (self._min_ticket_created_at,))
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
                COUNT(id) FILTER (WHERE ticket_created_at IS NOT NULL) AS ticket_created_at_count,
                COUNT(id) FILTER (WHERE ticket_created_at IS NULL) AS ticket_created_at_null_count,
                COUNT(id) FILTER (WHERE ticket_updated_at IS NOT NULL) AS ticket_updated_at_count,
                COUNT(id) FILTER (WHERE ticket_updated_at IS NULL) AS ticket_updated_at_null_count,
                COUNT(id) FILTER (WHERE ticket_closed_at IS NOT NULL) AS ticket_closed_at_count,
                COUNT(id) FILTER (WHERE ticket_closed_at IS NULL) AS ticket_closed_at_null_count,
                COUNT(id) FILTER (WHERE ingested_at IS NOT NULL) AS time_count,
                COUNT(id) FILTER (WHERE ingested_at IS NULL) AS time_null_count,
                0 AS time_missing_count
            FROM clean_tickets
            WHERE ticket_created_at >= %s
        """
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, (self._min_ticket_created_at,))
                row = cursor.fetchone()
        fields = (
            ("status", row[0], row[1], row[2]),
            ("priority", row[3], row[4], row[5]),
            ("category", row[6], row[7], row[8]),
            ("ticket_created_at", row[9], row[10], row[10]),
            ("ticket_updated_at", row[11], row[12], row[12]),
            ("ticket_closed_at", row[13], row[14], row[14]),
            ("ingested_at", row[15], row[16], row[17]),
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


def _ticket_created_bucket_format(granularity: str) -> str:
    """Return a safe PostgreSQL TO_CHAR mask for ticket_created_at buckets."""

    if granularity == "month":
        return "YYYY-MM"
    if granularity == "year":
        return "YYYY"
    raise ValueError("Unsupported ticket_created_at bucket granularity")
