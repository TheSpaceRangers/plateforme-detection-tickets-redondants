"""Synthetic dry-run coverage for the future ticket extraction pipeline."""

from __future__ import annotations

import json
from typing import Mapping

import pytest

from src.preprocessing import AgentIdPolicy, PiiResidualError, build_preprocessed_ticket_dataset, detect_pii
from src.preprocessing.pii import assert_no_residual_pii
from src.preprocessing.pseudonymization import MissingPseudonymizationSecretError
from src.eda.quality import build_ticket_dataset_quality_report
from src.ml_contract.contract import validate_feature_columns, validate_raw_input_columns
from src.ml_contract.dry_run_report import build_ticket_dataset_v1_dry_run_report
from src.ml_contract.synthetic_source import synthetic_ticket_source_records


def _simulate_ticket_extraction() -> list[dict[str, object]]:
    """Return ticket-like synthetic records without calling any external source."""

    return [
        {
            "ticket_id": "synthetic-ticket-001",
            "summary": "Portail indisponible pour synthetic.user@example.test",
            "details": "Diagnostic depuis 10.0.0.42, rappel au 06 00 00 00 00, login: synthetic-user",
            "agent_id": "agent-synthetic-001",
            "category": "access",
        },
        {
            "ticket_id": "synthetic-ticket-002",
            "summary": "Imprimante synthétique bloquée",
            "details": "Bourrage papier étage fictif, aucun contact utilisateur réel",
            "agent_id": "agent-synthetic-002",
            "category": "hardware",
        },
    ]


def _prepare_storage_export(records: list[Mapping[str, object]]) -> str:
    """Prepare cleaned records as an in-memory JSON payload for a future exporter."""

    assert_no_residual_pii(records)
    return json.dumps(records, ensure_ascii=False, sort_keys=True)


def test_synthetic_dry_run_prepares_only_cleaned_records_without_raw_json_file() -> None:
    """Synthetic extraction is cleaned in memory before storage/export preparation."""

    extracted_tickets = _simulate_ticket_extraction()

    dataset = build_preprocessed_ticket_dataset(extracted_tickets)
    export_payload = _prepare_storage_export(dataset)

    assert len(dataset) == 2
    assert all("agent_id" not in record for record in dataset)
    assert all(detect_pii(str(record.get("summary", ""))) == () for record in dataset)
    assert all(detect_pii(str(record.get("details", ""))) == () for record in dataset)
    assert "synthetic.user@example.test" not in export_payload
    assert "06 00 00 00 00" not in export_payload
    assert "10.0.0.42" not in export_payload
    assert "agent-synthetic-001" not in export_payload
    assert "[EMAIL]" in export_payload
    assert "[PHONE]" in export_payload
    assert "[IP]" in export_payload


def test_synthetic_dry_run_can_pseudonymize_agent_id_only_with_explicit_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit policy can create HMAC pseudonyms, but not as a default ML dataset field."""

    monkeypatch.setenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", "synthetic-dry-run-secret")

    dataset = build_preprocessed_ticket_dataset(
        _simulate_ticket_extraction(),
        AgentIdPolicy(include_pseudonymized=True),
    )

    assert all("agent_id" not in record for record in dataset)
    assert all(str(record["agent_id_pseudonym"]).startswith("hmac_sha256:") for record in dataset)
    assert validate_feature_columns(dataset[0].keys()).is_valid is False


@pytest.mark.parametrize("secret", [None, ""])
def test_synthetic_dry_run_agent_id_pseudonymization_fails_closed_without_secret(
    monkeypatch: pytest.MonkeyPatch,
    secret: str | None,
) -> None:
    """Explicit agent_id pseudonymization is blocked when HMAC secret is absent or empty."""

    if secret is None:
        monkeypatch.delenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", raising=False)
    else:
        monkeypatch.setenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", secret)

    with pytest.raises(MissingPseudonymizationSecretError):
        build_preprocessed_ticket_dataset(
            _simulate_ticket_extraction(),
            AgentIdPolicy(include_pseudonymized=True),
        )


def test_synthetic_dry_run_blocks_storage_export_when_residual_pii_is_detected() -> None:
    """Storage/export preparation is fail-closed if a residual PII record appears."""

    unsafe_prepared_records = [
        {
            "ticket_id": "synthetic-ticket-blocked",
            "summary": "Record déjà préparé",
            "details": "Contact résiduel blocked.user@example.test",
        }
    ]

    with pytest.raises(PiiResidualError):
        _prepare_storage_export(unsafe_prepared_records)


def test_contract_dry_run_exposes_quality_and_lot3_readiness_without_training() -> None:
    """Dry-run report includes aggregate EDA quality and Lot 3 gates without training."""

    report = build_ticket_dataset_v1_dry_run_report(synthetic_ticket_source_records())

    assert report["status"] == "pass"
    assert report["included_count"] == 5
    assert report["pii_official_residual_count"] == 0
    assert report["secret_scan_count"] == 0
    assert report["quality_report"]["duplicate_signature_count"] == 1
    assert report["quality_report"]["missing_value_counts"]["summary"] == 1
    assert report["quality_report"]["missing_value_counts"]["ticket_created_at"] == 1
    assert report["lot3_readiness"]["training_enabled"] is False
    assert report["lot3_readiness"]["labels_required"] is True
    assert report["lot3_readiness"]["pairwise_generation_possible"] is True
    assert "group" in str(report["lot3_readiness"]["split_strategy"])
    assert "pair" in str(report["lot3_readiness"]["anti_leak_strategy"])


def test_contract_blocks_external_ticket_id_and_agent_pseudonym_in_ml_outputs() -> None:
    """Indirect IDs and pseudonymized agent IDs are forbidden in ML datasets/reports by default."""

    raw_validation = validate_raw_input_columns(
        [
            {
                "summary": "Synthétique",
                "details": "Sans PII",
                "ticket_created_at": "2026-01-01",
                "external_ticket_id": "EXT-1",
            }
        ]
    )
    feature_validation = validate_feature_columns(["cleaned_text_truncated", "agent_id_pseudonym"])

    assert raw_validation.is_valid is False
    assert raw_validation.forbidden_column_count == 1
    assert feature_validation.is_valid is False
    assert feature_validation.forbidden_column_count == 1


def test_quality_report_counts_only_aggregate_metrics() -> None:
    """Quality report returns counts and distributions only, never row-level text."""

    report = build_ticket_dataset_quality_report(synthetic_ticket_source_records()).to_safe_output()

    assert set(report) == {
        "missing_value_counts",
        "duplicate_signature_count",
        "source_column_count",
        "non_allowlisted_source_column_count",
        "text_length_bucket_distribution",
    }
    assert report["non_allowlisted_source_column_count"] == 0
    assert "Connexion applicative" not in json.dumps(report, ensure_ascii=False)
