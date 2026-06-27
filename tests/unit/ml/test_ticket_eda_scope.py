"""Official QA tests for ticket_created_at EDA/ML date scoping."""

from __future__ import annotations

from datetime import date
from typing import Any

from src.eda.ticket_scope import (
    EdaDateScopeConfig,
    build_ticket_eda_scope_metrics,
    filter_records_for_ticket_eda_metrics,
)


FORBIDDEN_OUTPUT_KEYS = {
    "id",
    "ids",
    "ticket_id",
    "summary",
    "details",
    "external_ticket_id",
    "agent_id_pseudonym",
    "payload",
    "secret",
    "secrets",
    "password",
    "api_key",
    "token",
}


def assert_no_forbidden_output_fields(value: Any) -> None:
    """Assert recursively that aggregate EDA output exposes no forbidden fields."""

    if isinstance(value, dict):
        assert FORBIDDEN_OUTPUT_KEYS.isdisjoint({str(key).lower() for key in value})
        for item in value.values():
            assert_no_forbidden_output_fields(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_forbidden_output_fields(item)
    elif isinstance(value, str):
        normalized_value = value.lower()
        assert not any(key in normalized_value for key in FORBIDDEN_OUTPUT_KEYS)


def test_ticket_eda_scope_excludes_historical_outliers_and_missing_dates_from_metrics() -> None:
    # Arrange
    records = [
        {"ticket_created_at": "2024-12-31"},
        {"ticket_created_at": "2025-01-01"},
        {"ticket_created_at": "2026-06-01T12:00:00Z"},
        {"ticket_created_at": None},
    ]

    # Act
    metrics = build_ticket_eda_scope_metrics(records)
    included_records = filter_records_for_ticket_eda_metrics(records)
    output = metrics.to_safe_output()

    # Assert
    assert metrics.total_source_count == 4
    assert metrics.included_count == 2
    assert metrics.excluded_historical_outlier_count == 1
    assert metrics.excluded_missing_ticket_created_at_count == 1
    assert metrics.applied_min_ticket_created_at == "2025-01-01"
    assert len(included_records) == 2
    assert output == {
        "total_source_count": 4,
        "included_count": 2,
        "excluded_historical_outlier_count": 1,
        "excluded_missing_ticket_created_at_count": 1,
        "applied_min_ticket_created_at": "2025-01-01",
    }
    assert_no_forbidden_output_fields(output)


def test_ticket_eda_scope_fails_closed_for_invalid_or_absent_ticket_created_at() -> None:
    # Arrange
    records = [
        {"ticket_created_at": "not-a-date"},
        {},
        {"ticket_created_at": "2024-01-01"},
    ]

    # Act
    metrics = build_ticket_eda_scope_metrics(records)
    included_records = filter_records_for_ticket_eda_metrics(records)
    output = metrics.to_safe_output()

    # Assert
    assert metrics.total_source_count == 3
    assert metrics.included_count == 0
    assert metrics.excluded_historical_outlier_count == 1
    assert metrics.excluded_missing_ticket_created_at_count == 2
    assert metrics.applied_min_ticket_created_at == "2025-01-01"
    assert included_records == []
    assert set(output) == {
        "total_source_count",
        "included_count",
        "excluded_historical_outlier_count",
        "excluded_missing_ticket_created_at_count",
        "applied_min_ticket_created_at",
    }
    assert_no_forbidden_output_fields(output)


def test_ticket_eda_scope_explicit_ml_config_changes_boundary_when_requested() -> None:
    # Arrange
    records = [
        {"ticket_created_at": "2025-01-01"},
        {"ticket_created_at": "2025-06-30"},
        {"ticket_created_at": "2025-07-01"},
    ]
    config = EdaDateScopeConfig(min_ticket_created_at=date(2025, 7, 1))

    # Act
    metrics = build_ticket_eda_scope_metrics(records, config=config)
    included_records = filter_records_for_ticket_eda_metrics(records, config=config)

    # Assert
    assert metrics.total_source_count == 3
    assert metrics.included_count == 1
    assert metrics.excluded_historical_outlier_count == 2
    assert metrics.excluded_missing_ticket_created_at_count == 0
    assert metrics.applied_min_ticket_created_at == "2025-07-01"
    assert included_records == [{"ticket_created_at": "2025-07-01"}]
