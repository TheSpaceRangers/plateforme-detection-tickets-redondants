"""Pydantic schemas for aggregate-only ticket EDA outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DistributionBucket(BaseModel):
    """Anonymous aggregate distribution bucket."""

    rank: int = Field(ge=1)
    count: int = Field(ge=0)


class DistributionMetric(BaseModel):
    """Distinct count and anonymous distribution for one controlled dimension."""

    distinct_count: int = Field(ge=0)
    non_null_distinct_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    buckets: list[DistributionBucket]


class TextLengthMetric(BaseModel):
    """Aggregate text length percentiles without exposing text content."""

    min: int = Field(ge=0)
    mean: float = Field(ge=0)
    max: int = Field(ge=0)
    p50: float = Field(ge=0)
    p90: float = Field(ge=0)
    p95: float = Field(ge=0)
    p99: float = Field(ge=0)


class TextQualityMetric(BaseModel):
    """Aggregate quality metrics for sanitized ticket text fields."""

    length: TextLengthMetric
    empty_rate: float = Field(ge=0, le=1)


class PlaceholderMetric(BaseModel):
    """Aggregate placeholder occurrence metrics."""

    placeholder: str
    rows_with_placeholder: int = Field(ge=0)
    rate: float = Field(ge=0, le=1)


class PiiCategoryResidualMetric(BaseModel):
    """Aggregate official residual PII count for one detector category."""

    category: str
    rows_with_residual: int = Field(ge=0)


class TemporalBucket(BaseModel):
    """Aggregate ticket count for a time period."""

    period: str
    count: int = Field(ge=0)


class TemporalFieldMetric(BaseModel):
    """Nullable timestamp range and completeness for a non-sensitive date field."""

    min_at: str | None = None
    max_at: str | None = None
    populated_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)


class TicketCreatedTemporalBuckets(BaseModel):
    """Aggregate buckets based only on ticket_created_at business dates."""

    by_month: list[TemporalBucket]
    by_year: list[TemporalBucket]


class TemporalDistribution(BaseModel):
    """Aggregate temporal metrics separating business dates from ingestion time."""

    ticket_created_at: TemporalFieldMetric
    ticket_updated_at: TemporalFieldMetric
    ticket_closed_at: TemporalFieldMetric
    ingested_at: TemporalFieldMetric
    ticket_created_buckets: TicketCreatedTemporalBuckets


class PiiScanMetric(BaseModel):
    """Aggregate official PII residual scan result without leaking text."""

    rows_scanned: int = Field(ge=0)
    pii_residual_official_count: int = Field(ge=0)
    residual_detection_rate: float = Field(ge=0, le=1)
    residual_categories: list[PiiCategoryResidualMetric]
    heuristic_like_pattern_count: int | None = Field(default=None, ge=0)


class FieldCompletenessMetric(BaseModel):
    """Completeness metric for an allowed aggregate field."""

    field: str
    populated_count: int = Field(ge=0)
    null_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)
    completeness_rate: float = Field(ge=0, le=1)


class AggregateTicketEdaReport(BaseModel):
    """Safe aggregate-only EDA report for clean tickets."""

    total_tickets: int = Field(ge=0)
    total_source_count: int = Field(ge=0)
    included_count: int = Field(ge=0)
    excluded_historical_outlier_count: int = Field(ge=0)
    excluded_missing_ticket_created_at_count: int = Field(ge=0)
    applied_min_ticket_created_at: str
    status_distribution: DistributionMetric
    priority_distribution: DistributionMetric
    category_distribution: DistributionMetric
    short_text: TextQualityMetric
    long_text: TextQualityMetric
    fallback_untitled_ticket_rate: float = Field(ge=0, le=1)
    placeholder_counts: list[PlaceholderMetric]
    temporal_distribution: TemporalDistribution
    pii_scan: PiiScanMetric
    completeness: list[FieldCompletenessMetric]
