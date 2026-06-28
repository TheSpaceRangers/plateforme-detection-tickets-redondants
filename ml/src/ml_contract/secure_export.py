"""Controlled secure export orchestration for ML ticket contract v1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterable, Mapping, Protocol

from .contract import DATASET_VERSION, MIN_TICKET_CREATED_AT, validate_feature_columns, validate_raw_input_columns
from .storage_guard import (
    PARQUET_EXTENSION,
    StorageGuardError,
    purge_file,
    read_parquet_rows,
    validate_secure_output_path,
    write_parquet_securely,
)
from .transforms import build_safe_ticket_features, planned_feature_columns


DEFAULT_TTL_HOURS = 24
SECURE_EXPORT_REPORT_KEYS: tuple[str, ...] = (
    "dataset_version",
    "mode",
    "status",
    "scope_min_ticket_created_at",
    "total_source_count",
    "included_count",
    "excluded_historical_outlier_count",
    "excluded_missing_ticket_created_at_count",
    "planned_dataset_columns",
    "pii_official_residual_count",
    "secret_scan_count",
    "forbidden_column_count",
    "exact_timestamp_column_count",
    "raw_text_column_count",
    "gates",
    "ttl_hours",
    "expires_at_utc",
    "output_extension",
)


class SecureExportError(ValueError):
    """Raised when a secure export is blocked or fails a safety gate."""


@dataclass(frozen=True)
class ScanResult:
    """Aggregate-only persisted export scan result."""

    pii_official_residual_count: int
    secret_scan_count: int

    @property
    def passed(self) -> bool:
        """Return whether the scan found no residual PII or secrets."""

        return self.pii_official_residual_count == 0 and self.secret_scan_count == 0


@dataclass(frozen=True)
class PreparedExport:
    """Validated rows and destination prepared for controlled export."""

    rows: list[dict[str, object]]
    output_path: Path


class PersistedExportScanner(Protocol):
    """Scanner contract for post-write aggregate scans."""

    def scan_path(self, path: Path) -> ScanResult:
        """Scan a persisted export and return aggregate findings only."""


class ParquetAggregateScanner:
    """Default post-write scanner for persisted Parquet feature exports."""

    def scan_path(self, path: Path) -> ScanResult:
        """Scan persisted rows without returning row-level values or matches."""

        try:
            from src.preprocessing.pii import detect_pii
        except ModuleNotFoundError:  # pragma: no cover
            from ml.src.preprocessing.pii import detect_pii

        from .transforms import _count_secret_findings

        pii_count = 0
        secret_count = 0
        for row in read_parquet_rows(path):
            text_value = str(row.get("cleaned_text_truncated", "") or "")
            pii_count += len(detect_pii(text_value))
            secret_count += _count_secret_findings(text_value)
        return ScanResult(pii_official_residual_count=pii_count, secret_scan_count=secret_count)


def export_ticket_v1_securely(
    records: Iterable[Mapping[str, object]],
    *,
    real_export: bool = False,
    output_path: str | Path | None = None,
    ttl_hours: int = DEFAULT_TTL_HOURS,
    scanner: PersistedExportScanner | None = None,
) -> dict[str, object]:
    """Run a controlled real export only when every explicit safety gate passes."""

    _validate_export_request(real_export=real_export, output_path=output_path, ttl_hours=ttl_hours)
    prepared_export = _prepare_export(records, output_path)
    scan_result = _write_and_scan(prepared_export, scanner)
    return build_secure_export_report(row_count=len(prepared_export.rows), ttl_hours=ttl_hours, scan_result=scan_result)


def build_secure_export_report(*, row_count: int, ttl_hours: int, scan_result: ScanResult) -> dict[str, object]:
    """Build an allowlisted aggregate-only report for a successful secure export."""

    report = _base_export_report(mode="real_export_controlled", status="pass", row_count=row_count)
    report.update(
        pii_official_residual_count=scan_result.pii_official_residual_count,
        secret_scan_count=scan_result.secret_scan_count,
        gates=_success_gates(scan_result),
        ttl_hours=ttl_hours,
        expires_at_utc=_expiry_timestamp(ttl_hours),
        output_extension=PARQUET_EXTENSION,
    )
    _assert_safe_report(report)
    return {key: report[key] for key in SECURE_EXPORT_REPORT_KEYS}


def build_blocked_secure_export_report(reason: str) -> dict[str, object]:
    """Build an aggregate-only report for a blocked export attempt."""

    report = _base_export_report(mode="real_export_blocked", status="fail", row_count=0)
    report.update(
        pii_official_residual_count=0,
        secret_scan_count=0,
        gates=({"name": reason, "passed": False},),
        ttl_hours=DEFAULT_TTL_HOURS,
        expires_at_utc=None,
        output_extension=PARQUET_EXTENSION,
    )
    _assert_safe_report(report)
    return {key: report[key] for key in SECURE_EXPORT_REPORT_KEYS}


def _validate_export_request(*, real_export: bool, output_path: str | Path | None, ttl_hours: int) -> None:
    """Validate explicit export activation and TTL before any write."""

    if not real_export:
        raise SecureExportError("Real export requires the explicit --real-export flag.")
    if output_path is None:
        raise SecureExportError("Real export requires an explicit output path.")
    if ttl_hours <= 0:
        raise SecureExportError("Export TTL must be a positive number of hours.")


def _prepare_export(records: Iterable[Mapping[str, object]], output_path: str | Path | None) -> PreparedExport:
    """Validate destination, contract, transforms, and pre-export aggregate scans."""

    target = validate_secure_output_path(_require_output_path(output_path))
    source_records = list(records)
    raw_validation = validate_raw_input_columns(source_records)
    feature_rows, transform_metrics = build_safe_ticket_features(source_records)
    feature_validation = validate_feature_columns(planned_feature_columns())
    if not raw_validation.is_valid or not feature_validation.is_valid:
        raise SecureExportError("Contract validation failed before export.")
    if transform_metrics.pii_official_residual_count or transform_metrics.secret_scan_count:
        raise SecureExportError("Pre-export aggregate PII/secret scan failed.")
    return PreparedExport(rows=[row.to_mapping() for row in feature_rows], output_path=target.path)


def _write_and_scan(prepared_export: PreparedExport, scanner: PersistedExportScanner | None) -> ScanResult:
    """Write the prepared export, then purge it if post-write scan fails."""

    target = validate_secure_output_path(prepared_export.output_path)
    write_parquet_securely(prepared_export.rows, target)
    scan_result = (scanner or ParquetAggregateScanner()).scan_path(target.path)
    if not scan_result.passed:
        purge_file(target.path)
        raise SecureExportError("Post-write aggregate PII/secret scan failed; export file purged.")
    return scan_result


def _base_export_report(*, mode: str, status: str, row_count: int) -> dict[str, object]:
    """Build common aggregate report fields."""

    return {
        "dataset_version": DATASET_VERSION,
        "mode": mode,
        "status": status,
        "scope_min_ticket_created_at": MIN_TICKET_CREATED_AT,
        "total_source_count": row_count,
        "included_count": row_count,
        "excluded_historical_outlier_count": 0,
        "excluded_missing_ticket_created_at_count": 0,
        "planned_dataset_columns": planned_feature_columns(),
        "forbidden_column_count": 0,
        "exact_timestamp_column_count": 0,
        "raw_text_column_count": 0,
    }


def _success_gates(scan_result: ScanResult) -> tuple[dict[str, bool | str], ...]:
    """Return aggregate gates for a successful controlled export."""

    return (
        {"name": "real_export_explicitly_enabled", "passed": True},
        {"name": "output_path_outside_git", "passed": True},
        {"name": "secure_permissions_requested", "passed": True},
        {"name": "post_write_scan_passed", "passed": scan_result.passed},
    )


def _expiry_timestamp(ttl_hours: int) -> str:
    """Return the UTC expiry timestamp for the configured TTL."""

    return (datetime.now(UTC).replace(microsecond=0) + timedelta(hours=ttl_hours)).isoformat()


def _require_output_path(output_path: str | Path | None) -> str | Path:
    """Narrow the output path type after request validation."""

    if output_path is None:
        raise SecureExportError("Real export requires an explicit output path.")
    return output_path


def normalize_block_reason(error: Exception) -> str:
    """Map implementation exceptions to safe aggregate gate names."""

    if isinstance(error, StorageGuardError):
        return "storage_guard_failed"
    if isinstance(error, SecureExportError):
        return "secure_export_guard_failed"
    return "secure_export_unavailable"


def _assert_safe_report(report: Mapping[str, object]) -> None:
    """Reject any report field outside the aggregate-safe allowlist."""

    if set(report) - set(SECURE_EXPORT_REPORT_KEYS):
        raise SecureExportError("Unsafe export report fields detected.")
