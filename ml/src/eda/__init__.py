"""Aggregate-only EDA helpers for ticket datasets."""

from .quality import TicketDatasetQualityReport, build_ticket_dataset_quality_report
from .ticket_scope import (
    DEFAULT_MIN_TICKET_CREATED_AT,
    EdaDateScopeConfig,
    TicketEdaScopeMetrics,
    build_ticket_eda_scope_metrics,
    filter_records_for_ticket_eda_metrics,
)

__all__ = [
    "DEFAULT_MIN_TICKET_CREATED_AT",
    "EdaDateScopeConfig",
    "TicketEdaScopeMetrics",
    "TicketDatasetQualityReport",
    "build_ticket_dataset_quality_report",
    "build_ticket_eda_scope_metrics",
    "filter_records_for_ticket_eda_metrics",
]
