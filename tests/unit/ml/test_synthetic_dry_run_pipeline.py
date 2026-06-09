"""Synthetic dry-run coverage for the future ticket extraction pipeline."""

from __future__ import annotations

import json
from typing import Mapping

import pytest

from src.preprocessing import AgentIdPolicy, PiiResidualError, build_preprocessed_ticket_dataset, detect_pii
from src.preprocessing.pii import assert_no_residual_pii
from src.preprocessing.pseudonymization import MissingPseudonymizationSecretError


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
    """Explicit policy adds only HMAC pseudonyms and never exports raw agent_id."""

    monkeypatch.setenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", "synthetic-dry-run-secret")

    dataset = build_preprocessed_ticket_dataset(
        _simulate_ticket_extraction(),
        AgentIdPolicy(include_pseudonymized=True),
    )
    export_payload = _prepare_storage_export(dataset)

    assert all("agent_id" not in record for record in dataset)
    assert all(str(record["agent_id_pseudonym"]).startswith("hmac_sha256:") for record in dataset)
    assert "agent-synthetic-001" not in export_payload
    assert "agent-synthetic-002" not in export_payload
    assert "agent_id_pseudonym" in export_payload


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
