"""Aggregate-only dry-run report for ticket dataset v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

try:  # pragma: no cover - compatibility for both `src.*` and repository-root imports.
    from src.eda.ticket_scope import build_ticket_eda_scope_metrics
except ModuleNotFoundError:  # pragma: no cover
    from ml.src.eda.ticket_scope import build_ticket_eda_scope_metrics

from .contract import (
    DATASET_VERSION,
    MIN_TICKET_CREATED_AT,
    REPORT_KEYS,
    assert_safe_report_keys,
    validate_feature_columns,
    validate_raw_input_columns,
)
from .transforms import build_safe_ticket_features, planned_feature_columns


@dataclass(frozen=True)
class GateStatus:
    """Safe aggregate status for one blocking dataset gate."""

    name: str
    passed: bool

    def to_mapping(self) -> dict[str, bool | str]:
        """Return an aggregate-only representation of the gate."""

        return {"name": self.name, "passed": self.passed}


def build_ticket_dataset_v1_dry_run_report(
    records: Iterable[Mapping[str, object]],
    *,
    output_path_attempted: bool = False,
) -> dict[str, object]:
    """Validate contract/transforms and return only an aggregate safe report."""

    source_records = list(records)
    raw_validation = validate_raw_input_columns(source_records)
    scope_metrics = build_ticket_eda_scope_metrics(source_records)
    feature_rows, transform_metrics = build_safe_ticket_features(source_records)
    feature_validation = validate_feature_columns(planned_feature_columns())
    row_column_valid = _all_feature_rows_match_contract(feature_rows)

    forbidden_column_count = raw_validation.forbidden_column_count + feature_validation.forbidden_column_count
    exact_timestamp_column_count = (
        raw_validation.exact_timestamp_column_count + feature_validation.exact_timestamp_column_count
    )
    raw_text_column_count = raw_validation.raw_text_column_count + feature_validation.raw_text_column_count

    gates = (
        GateStatus("no_forbidden_columns", forbidden_column_count == 0),
        GateStatus("no_residual_pii", transform_metrics.pii_official_residual_count == 0),
        GateStatus("no_detected_secrets", transform_metrics.secret_scan_count == 0),
        GateStatus("no_exact_timestamps", exact_timestamp_column_count == 0),
        GateStatus("no_raw_text_columns", raw_text_column_count == 0),
        GateStatus("feature_rows_match_allowlist", row_column_valid),
        GateStatus("no_dataset_output_path", not output_path_attempted),
    )
    status = "pass" if all(gate.passed for gate in gates) else "fail"

    report: dict[str, object] = {
        "dataset_version": DATASET_VERSION,
        "mode": "dry_run_no_export",
        "status": status,
        "scope_min_ticket_created_at": MIN_TICKET_CREATED_AT,
        "total_source_count": scope_metrics.total_source_count,
        "included_count": scope_metrics.included_count,
        "excluded_historical_outlier_count": scope_metrics.excluded_historical_outlier_count,
        "excluded_missing_ticket_created_at_count": scope_metrics.excluded_missing_ticket_created_at_count,
        "planned_dataset_columns": planned_feature_columns(),
        "pii_official_residual_count": transform_metrics.pii_official_residual_count,
        "secret_scan_count": transform_metrics.secret_scan_count,
        "forbidden_column_count": forbidden_column_count,
        "exact_timestamp_column_count": exact_timestamp_column_count,
        "raw_text_column_count": raw_text_column_count,
        "gates": tuple(gate.to_mapping() for gate in gates),
    }
    assert_safe_report_keys(report)
    return {key: report[key] for key in REPORT_KEYS}


def _all_feature_rows_match_contract(feature_rows: list[object]) -> bool:
    """Verify in-memory rows expose only planned feature keys."""

    expected_columns = set(planned_feature_columns())
    for row in feature_rows:
        to_mapping = getattr(row, "to_mapping", None)
        if not callable(to_mapping) or set(to_mapping()) != expected_columns:
            return False
    return True
