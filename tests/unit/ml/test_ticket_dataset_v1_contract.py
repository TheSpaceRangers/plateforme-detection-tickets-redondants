"""Official QA tests for ticket dataset v1 dry-run contract tooling."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.datasets.contract import (
    FEATURE_ALLOWLIST,
    REPORT_ALLOWLIST,
    DatasetContractError,
    assert_safe_report_keys,
    validate_feature_columns,
    validate_raw_input_columns,
)
from src.datasets.dry_run_report import build_ticket_dataset_v1_dry_run_report
from src.datasets.ticket_dataset_v1_dry_run import main
from src.datasets.transforms import build_safe_ticket_features, planned_feature_columns
from src.preprocessing.pii import PII_REPLACEMENTS, detect_pii


FORBIDDEN_REPORT_KEYS = {
    "summary",
    "details",
    "raw_text",
    "cleaned_text",
    "external_ticket_id",
    "agent_id",
    "agent_id_pseudonym",
    "payload",
    "ticket_id",
    "user_id",
    "client_id",
    "customer_id",
    "account_id",
}


def _safe_records() -> list[dict[str, object]]:
    return [
        {
            "summary": "Synthetic portal access issue",
            "details": "Synthetic non-sensitive diagnostic narrative",
            "ticket_created_at": "2025-03-10T08:15:00+00:00",
        },
        {
            "summary": "Synthetic archive case",
            "details": "Synthetic historical record excluded by scope",
            "ticket_created_at": "2024-12-31",
        },
    ]


def _assert_report_contains_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        assert FORBIDDEN_REPORT_KEYS.isdisjoint({str(key).lower() for key in value})
        for nested_value in value.values():
            _assert_report_contains_no_forbidden_keys(nested_value)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_report_contains_no_forbidden_keys(item)


def _gate_statuses(report: Mapping[str, object]) -> dict[str, bool]:
    return {str(gate["name"]): bool(gate["passed"]) for gate in report["gates"]}  # type: ignore[index]


def test_contract_accepts_only_feature_allowlist_and_aggregate_report_keys() -> None:
    # Arrange
    records = _safe_records()

    # Act
    feature_validation = validate_feature_columns(FEATURE_ALLOWLIST)
    report = build_ticket_dataset_v1_dry_run_report(records)

    # Assert
    assert feature_validation.is_valid is True
    assert set(planned_feature_columns()) == FEATURE_ALLOWLIST
    assert set(report) == REPORT_ALLOWLIST
    assert report["status"] == "pass"
    assert set(report["planned_dataset_columns"]) == FEATURE_ALLOWLIST
    _assert_report_contains_no_forbidden_keys(report)


def test_contract_rejects_report_keys_outside_aggregate_allowlist() -> None:
    # Arrange
    unsafe_report = {"status": "pass", "summary": "synthetic row-level text"}

    # Act / Assert
    with pytest.raises(DatasetContractError):
        assert_safe_report_keys(unsafe_report)


@pytest.mark.parametrize(
    "forbidden_column",
    [
        "external_ticket_id",
        "agent_id_pseudonym",
        "payload",
        "foo_id",
        "session_uuid",
        "created_at",
        "priority",
        "category",
        "raw_text",
        "cleaned_text",
    ],
)
def test_contract_blocks_forbidden_raw_input_columns(forbidden_column: str) -> None:
    # Arrange
    records = [{"summary": "Synthetic", "details": "Synthetic", "ticket_created_at": "2025-01-01", forbidden_column: "x"}]

    # Act
    validation = validate_raw_input_columns(records)
    report = build_ticket_dataset_v1_dry_run_report(records)

    # Assert
    assert validation.is_valid is False
    assert report["status"] == "fail"
    assert report["forbidden_column_count"] >= 1
    assert _gate_statuses(report)["no_forbidden_columns"] is False


def test_contract_accepts_required_raw_input_columns() -> None:
    # Arrange
    records = [{"summary": "Synthetic", "details": "Synthetic", "ticket_created_at": "2025-01-01"}]

    # Act
    validation = validate_raw_input_columns(records)
    report = build_ticket_dataset_v1_dry_run_report(records)

    # Assert
    assert validation.is_valid is True
    assert report["status"] == "pass"
    assert _gate_statuses(report)["no_forbidden_columns"] is True


def test_dry_run_cli_rejects_output_path_and_writes_no_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    output_path = tmp_path / "blocked-output.jsonl"

    # Act
    exit_code = main(["--synthetic", "--output", str(output_path)])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    # Assert
    assert exit_code == 2
    assert output_path.exists() is False
    assert report["status"] == "fail"
    assert _gate_statuses(report)["no_dataset_output_path"] is False


def test_dry_run_cli_without_output_path_passes_and_writes_no_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    output_path = tmp_path / "unexpected-output.jsonl"

    # Act
    exit_code = main(["--synthetic"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    # Assert
    assert exit_code == 0
    assert output_path.exists() is False
    assert report["status"] == "pass"
    assert _gate_statuses(report)["no_dataset_output_path"] is True


def test_transform_sanitizes_and_truncates_synthetic_text_without_residual_pii() -> None:
    # Arrange
    long_text = "A" * 700
    records = [
        {
            "summary": "Synthetic contact qa.person@example.test",
            "details": f"Call 06 12 34 56 78 then visit https://example.test/help {long_text}",
            "ticket_created_at": "2025-04-05",
        }
    ]

    # Act
    rows, metrics = build_safe_ticket_features(records)
    row = rows[0].to_mapping()
    transformed_text = str(row["cleaned_text_truncated"])

    # Assert
    assert len(transformed_text) == 512
    assert PII_REPLACEMENTS["email"].lower() in transformed_text
    assert PII_REPLACEMENTS["fr_phone"].lower() in transformed_text
    assert PII_REPLACEMENTS["url"].lower() in transformed_text
    assert detect_pii(transformed_text) == ()
    assert metrics.pii_official_residual_count == 0
    assert metrics.transformed_count == 1


def test_transform_excludes_records_with_missing_or_out_of_scope_dates() -> None:
    # Arrange
    records = [
        {"summary": "Synthetic", "details": "Synthetic", "ticket_created_at": None},
        {"summary": "Synthetic", "details": "Synthetic", "ticket_created_at": "2024-12-31"},
    ]

    # Act
    rows, metrics = build_safe_ticket_features(records)

    # Assert
    assert rows == []
    assert metrics.transformed_count == 0
    assert metrics.pii_official_residual_count == 0
    assert metrics.secret_scan_count == 0


def test_dates_are_rounded_to_allowed_calendar_features_only() -> None:
    # Arrange
    records = [{"summary": "Synthetic", "details": "Synthetic", "ticket_created_at": "2025-06-02T13:14:15+00:00"}]

    # Act
    rows, _metrics = build_safe_ticket_features(records)
    row = rows[0].to_mapping()

    # Assert
    assert {"created_month", "created_week", "created_day_of_week"}.issubset(row)
    assert "ticket_created_at" not in row
    assert "created_at" not in row
    assert "timestamp" not in row
    assert validate_feature_columns(row.keys()).is_valid is True


def test_exact_timestamp_feature_columns_are_rejected() -> None:
    # Arrange
    columns = tuple(FEATURE_ALLOWLIST) + ("ticket_created_at",)

    # Act
    validation = validate_feature_columns(columns)

    # Assert
    assert validation.is_valid is False
    assert validation.forbidden_column_count == 1
    assert validation.exact_timestamp_column_count == 1


def test_residual_secret_pattern_blocks_report_gate() -> None:
    # Arrange
    records = [{"summary": "Synthetic", "details": "token: synthetic-placeholder", "ticket_created_at": "2025-01-01"}]

    # Act
    report = build_ticket_dataset_v1_dry_run_report(records)

    # Assert
    assert report["status"] == "fail"
    assert report["secret_scan_count"] == 1
    assert _gate_statuses(report)["no_detected_secrets"] is False


def test_report_passes_when_no_residual_pii_or_secret_is_detected() -> None:
    # Arrange
    records = [{"summary": "Synthetic", "details": "Non-sensitive synthetic text", "ticket_created_at": "2025-01-01"}]

    # Act
    report = build_ticket_dataset_v1_dry_run_report(records)

    # Assert
    assert report["status"] == "pass"
    assert report["pii_official_residual_count"] == 0
    assert report["secret_scan_count"] == 0
    assert _gate_statuses(report)["no_residual_pii"] is True
    assert _gate_statuses(report)["no_detected_secrets"] is True


def test_report_contains_no_ticket_content_or_row_level_values() -> None:
    # Arrange
    source_summary = "Unique synthetic source summary marker"
    source_details = "Unique synthetic source details marker"
    records = [{"summary": source_summary, "details": source_details, "ticket_created_at": "2025-01-01"}]

    # Act
    report = build_ticket_dataset_v1_dry_run_report(records)
    serialized_report = json.dumps(report, ensure_ascii=True, sort_keys=True)

    # Assert
    assert set(report) == REPORT_ALLOWLIST
    _assert_report_contains_no_forbidden_keys(report)
    assert source_summary not in serialized_report
    assert source_details not in serialized_report
    assert "cleaned_text_truncated" in report["planned_dataset_columns"]
