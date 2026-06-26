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


class TemporalBucket(BaseModel):
    """Aggregate ticket count for a time period."""

    period: str
    count: int = Field(ge=0)


class TemporalDistribution(BaseModel):
    """Daily and weekly aggregate distributions based on ingestion time."""

    by_day: list[TemporalBucket]
    by_week: list[TemporalBucket]


class PiiScanMetric(BaseModel):
    """Aggregate PII scan result without leaking matching text."""

    rows_scanned: int = Field(ge=0)
    rows_with_pii_detected: int = Field(ge=0)
    detection_rate: float = Field(ge=0, le=1)


class FieldCompletenessMetric(BaseModel):
    """Completeness metric for an allowed aggregate field."""

    field: str
    populated_count: int = Field(ge=0)
    completeness_rate: float = Field(ge=0, le=1)


class AggregateTicketEdaReport(BaseModel):
    """Safe aggregate-only EDA report for clean tickets."""

    total_tickets: int = Field(ge=0)
    status_distribution: DistributionMetric
    priority_distribution: DistributionMetric
    category_distribution: DistributionMetric
    short_text: TextQualityMetric
    long_text: TextQualityMetric
    fallback_untitled_ticket_rate: float = Field(ge=0, le=1)
    placeholders: list[PlaceholderMetric]
    temporal_distribution: TemporalDistribution
    pii_scan: PiiScanMetric
    completeness: list[FieldCompletenessMetric]
