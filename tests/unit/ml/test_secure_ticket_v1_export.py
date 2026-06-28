"""Official QA tests for controlled secure ticket v1 export tooling."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Sequence

import pytest

from src.ml_contract import secure_export, storage_guard, ticket_v1_export
from src.ml_contract.secure_export import ScanResult, SecureExportError, export_ticket_v1_securely
from src.ml_contract.storage_guard import SecureStorageTarget, StorageGuardError, validate_secure_output_path


SENSITIVE_SYNTHETIC_SUMMARY = "Synthetic row marker alpha"
SENSITIVE_SYNTHETIC_DETAILS = "Synthetic row marker beta"
FORBIDDEN_CI_PATH_PARTS = ("dataset", "datasets", "dump", "artifacts", "models", "logs")


class PassingScanner:
    """Aggregate-only scanner fixture returning a safe result."""

    def scan_path(self, path: Path) -> ScanResult:
        # Arrange/Act are performed by the caller; Assert-equivalent safety is the aggregate-only result.
        return ScanResult(pii_official_residual_count=0, secret_scan_count=0)


class FailingScanner:
    """Aggregate-only scanner fixture returning a blocked result."""

    def scan_path(self, path: Path) -> ScanResult:
        # Arrange/Act are performed by the caller; Assert-equivalent safety is the aggregate-only result.
        return ScanResult(pii_official_residual_count=1, secret_scan_count=0)


def _safe_records() -> list[dict[str, object]]:
    return [
        {
            "summary": SENSITIVE_SYNTHETIC_SUMMARY,
            "details": SENSITIVE_SYNTHETIC_DETAILS,
            "ticket_created_at": "2025-01-15T09:30:00+00:00",
        }
    ]


def _write_placeholder_parquet(_rows: Sequence[dict[str, object]], target: SecureStorageTarget) -> None:
    storage_guard.prepare_secure_parent_directory(target)
    target.path.write_bytes(b"synthetic-placeholder")
    os.chmod(target.path, target.file_mode)


def test_cli_dry_run_is_default_passes_and_creates_no_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Arrange
    unexpected_output = tmp_path / "unexpected.parquet"

    # Act
    exit_code = ticket_v1_export.main([])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    # Assert
    assert exit_code == 0
    assert unexpected_output.exists() is False
    assert captured.err == ""
    assert report["status"] == "pass"


def test_api_real_export_refuses_without_explicit_flag_and_writes_nothing(tmp_path: Path) -> None:
    # Arrange
    output_path = tmp_path / "blocked.parquet"

    # Act / Assert
    with pytest.raises(SecureExportError, match="explicit --real-export flag"):
        export_ticket_v1_securely(_safe_records(), output_path=output_path)
    assert output_path.exists() is False


def test_api_real_export_accepts_explicit_flag_with_synthetic_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    output_path = tmp_path / "accepted.parquet"
    monkeypatch.setattr(secure_export, "write_parquet_securely", _write_placeholder_parquet)

    # Act
    report = export_ticket_v1_securely(
        _safe_records(), real_export=True, output_path=output_path, scanner=PassingScanner()
    )

    # Assert
    assert output_path.exists() is True
    assert report["status"] == "pass"
    assert report["output_extension"] == ".parquet"


def test_output_path_inside_repository_is_rejected_before_write(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    repo_output_path = Path.cwd() / "blocked.parquet"
    write_attempted = False

    def fail_if_called(_rows: Sequence[dict[str, object]], _target: SecureStorageTarget) -> None:
        nonlocal write_attempted
        write_attempted = True

    monkeypatch.setattr(secure_export, "write_parquet_securely", fail_if_called)

    # Act / Assert
    with pytest.raises(StorageGuardError, match="outside the repository"):
        export_ticket_v1_securely(_safe_records(), real_export=True, output_path=repo_output_path)
    assert write_attempted is False
    assert repo_output_path.exists() is False


def test_storage_writer_applies_secure_modes_and_umask(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    output_path = tmp_path / "secure" / "permissions.parquet"
    target = SecureStorageTarget(path=output_path)
    umask_calls: list[int] = []

    def fake_umask(value: int) -> int:
        umask_calls.append(value)
        return 0o022

    def fake_parquet_writer(_rows: Sequence[dict[str, object]], temporary_path: Path) -> None:
        temporary_path.write_bytes(b"synthetic-placeholder")

    monkeypatch.setattr(storage_guard, "_ensure_parquet_support", lambda: None)
    monkeypatch.setattr(storage_guard, "_write_parquet", fake_parquet_writer)
    monkeypatch.setattr(storage_guard.os, "umask", fake_umask)

    # Act
    storage_guard.write_parquet_securely([{"synthetic_feature": "value"}], target)

    # Assert
    assert output_path.exists() is True
    assert (output_path.parent.stat().st_mode & 0o777) == 0o700
    assert (output_path.stat().st_mode & 0o777) == 0o600
    assert umask_calls == [0o077, 0o022]


def test_export_purges_file_when_post_write_scan_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    output_path = tmp_path / "purged.parquet"
    monkeypatch.setattr(secure_export, "write_parquet_securely", _write_placeholder_parquet)

    # Act / Assert
    with pytest.raises(SecureExportError, match="Post-write aggregate PII/secret scan failed"):
        export_ticket_v1_securely(
            _safe_records(), real_export=True, output_path=output_path, scanner=FailingScanner()
        )
    assert output_path.exists() is False


def test_no_row_level_text_is_emitted_to_streams_or_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    output_path = tmp_path / "safe-report.parquet"
    monkeypatch.setattr(secure_export, "write_parquet_securely", _write_placeholder_parquet)

    # Act
    report = export_ticket_v1_securely(
        _safe_records(), real_export=True, output_path=output_path, scanner=PassingScanner()
    )
    captured = capsys.readouterr()
    serialized_report = json.dumps(report, ensure_ascii=True, sort_keys=True)

    # Assert
    assert SENSITIVE_SYNTHETIC_SUMMARY not in captured.out
    assert SENSITIVE_SYNTHETIC_SUMMARY not in captured.err
    assert SENSITIVE_SYNTHETIC_SUMMARY not in serialized_report
    assert SENSITIVE_SYNTHETIC_DETAILS not in captured.out
    assert SENSITIVE_SYNTHETIC_DETAILS not in captured.err
    assert SENSITIVE_SYNTHETIC_DETAILS not in serialized_report


def test_parquet_extension_is_required_and_accepted_with_synthetic_path(tmp_path: Path) -> None:
    # Arrange
    accepted_path = tmp_path / "accepted.parquet"
    rejected_path = tmp_path / "rejected.csv"

    # Act
    target = validate_secure_output_path(accepted_path)

    # Assert
    assert target.path == accepted_path.resolve()
    with pytest.raises(StorageGuardError, match=".parquet extension"):
        validate_secure_output_path(rejected_path)


def test_cli_real_export_blocks_after_guardrails_with_source_provider_not_configured(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Arrange
    output_path = tmp_path / "guarded.parquet"

    # Act
    exit_code = ticket_v1_export.main(["--real-export", "--output", str(output_path)])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    # Assert
    assert exit_code == 2
    assert output_path.exists() is False
    assert captured.err == ""
    assert report["status"] == "fail"
    assert report["gates"] == [{"name": "source_provider_not_configured", "passed": False}]


def test_new_test_file_path_contains_no_forbidden_ci_path_parts() -> None:
    # Arrange
    test_path_parts = {part.lower() for part in Path(__file__).resolve().parts}

    # Act
    forbidden_matches = sorted(test_path_parts.intersection(FORBIDDEN_CI_PATH_PARTS))

    # Assert
    assert forbidden_matches == []
