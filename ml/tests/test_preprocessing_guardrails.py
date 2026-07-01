"""Tests for synthetic ticket preprocessing guardrails."""

from __future__ import annotations

import hashlib
import hmac

import pytest

from src.preprocessing import (
    AgentIdPolicy,
    PiiResidualError,
    build_preprocessed_ticket_dataset,
    detect_pii,
)
from src.preprocessing.pii import assert_no_residual_pii
from src.preprocessing.pseudonymization import MissingPseudonymizationSecretError


def test_preprocess_sanitizes_common_pii_and_excludes_agent_id_by_default() -> None:
    """PII in summary/details is replaced and agent_id is omitted by default."""

    tickets = [
        {
            "summary": "VPN KO pour marie.dupont@example.test depuis 192.168.1.15",
            "details": "Rappeler au 06 12 34 56 78 et voir https://support.example.test/t/42 login: mdupont",
            "agent_id": "agent-123",
            "category": "network",
        }
    ]

    dataset = build_preprocessed_ticket_dataset(tickets)

    assert "agent_id" not in dataset[0]
    assert dataset[0]["summary"] == "VPN KO pour [EMAIL] depuis [IP]"
    assert dataset[0]["details"] == "Rappeler au [PHONE] et voir [URL] [IDENTIFIER]"
    assert detect_pii(str(dataset[0]["summary"])) == ()
    assert detect_pii(str(dataset[0]["details"])) == ()


def test_preprocess_keeps_non_pii_text_unchanged() -> None:
    """Safe synthetic text remains available for ML features."""

    tickets = [
        {
            "summary": "Imprimante bloquée",
            "details": "Bourrage papier au troisième étage",
            "agent_id": "a-1",
        }
    ]

    dataset = build_preprocessed_ticket_dataset(tickets)

    assert dataset == [{"summary": "Imprimante bloquée", "details": "Bourrage papier au troisième étage"}]


def test_residual_pii_check_blocks_dataset_creation() -> None:
    """Residual PII detection is fail-closed before storage/export."""

    unsafe_records = [{"summary": "Diagnostic", "details": "Contact root@example.test"}]

    with pytest.raises(PiiResidualError):
        assert_no_residual_pii(unsafe_records)


def test_agent_id_pseudonymization_requires_secret_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit agent_id pseudonymization fails closed when the secret is missing."""

    monkeypatch.delenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", raising=False)
    tickets = [
        {"summary": "Ticket synthétique", "details": "Aucune PII", "agent_id": "agent-123"}
    ]

    with pytest.raises(MissingPseudonymizationSecretError):
        build_preprocessed_ticket_dataset(tickets, AgentIdPolicy(include_pseudonymized=True))


def test_agent_id_pseudonymization_requires_non_empty_secret_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit agent_id pseudonymization fails closed when the secret is empty."""

    monkeypatch.setenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", "")
    tickets = [
        {"summary": "Ticket synthétique", "details": "Aucune PII", "agent_id": "agent-123"}
    ]

    with pytest.raises(MissingPseudonymizationSecretError):
        build_preprocessed_ticket_dataset(tickets, AgentIdPolicy(include_pseudonymized=True))


def test_agent_id_pseudonymization_is_only_added_when_explicitly_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """agent_id can be pseudonymized only through explicit technical configuration."""

    monkeypatch.setenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", "synthetic-test-secret")
    tickets = [
        {"summary": "Ticket synthétique", "details": "Aucune PII", "agent_id": "agent-123"}
    ]

    dataset = build_preprocessed_ticket_dataset(tickets, AgentIdPolicy(include_pseudonymized=True))

    assert "agent_id" not in dataset[0]
    assert dataset[0]["agent_id_pseudonym"].startswith("hmac_sha256:")


def test_agent_id_pseudonymization_matches_exact_hmac_sha256_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Synthetic agent_id pseudonymization returns the exact HMAC-SHA-256 digest."""

    secret = "synthetic-hmac-secret"
    agent_id = "agent-synthetic-456"
    expected_digest = hmac.new(
        secret.encode("utf-8"),
        agent_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    monkeypatch.setenv("SYNAPPSE_AGENT_ID_HMAC_SECRET", secret)
    tickets = [{"summary": "Ticket synthétique", "details": "Aucune PII", "agent_id": agent_id}]

    dataset = build_preprocessed_ticket_dataset(tickets, AgentIdPolicy(include_pseudonymized=True))

    assert dataset[0]["agent_id_pseudonym"] == f"hmac_sha256:{expected_digest}"


def test_preprocess_sanitizes_additional_obvious_identifiers_in_text_fields() -> None:
    """Obvious identifiers in summary and details are sanitized from synthetic text."""

    tickets = [
        {
            "summary": "Erreur portail pour user_id: user-789",
            "details": "Session client_id=client-456 à réinitialiser",
        }
    ]

    dataset = build_preprocessed_ticket_dataset(tickets)

    assert dataset[0]["summary"] == "Erreur portail pour [IDENTIFIER]"
    assert dataset[0]["details"] == "Session [IDENTIFIER] à réinitialiser"
    assert detect_pii(str(dataset[0]["summary"])) == ()
    assert detect_pii(str(dataset[0]["details"])) == ()


def test_preprocess_sanitizes_extended_structured_pii_patterns() -> None:
    """Extended structured PII patterns are removed from synthetic text."""

    tickets = [
        {
            "summary": (
                "Poste 00:1A:2B:3C:4D:5E vu en IPv6 "
                "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
            ),
            "details": (
                "IBAN FR76 3000 6000 0112 3456 7890 189, "
                "carte 4111 1111 1111 1111, NIR 1 84 12 75 123 456 78, "
                "SIRET 123 456 789 00010, external_ticket_id: EXT-42"
            ),
        }
    ]

    dataset = build_preprocessed_ticket_dataset(tickets)

    assert dataset[0]["summary"] == "Poste [DEVICE_IDENTIFIER] vu en IPv6 [IP]"
    assert "[FINANCIAL_IDENTIFIER]" in str(dataset[0]["details"])
    assert "[OFFICIAL_IDENTIFIER]" in str(dataset[0]["details"])
    assert "[ORGANIZATION_IDENTIFIER]" in str(dataset[0]["details"])
    assert "[IDENTIFIER]" in str(dataset[0]["details"])
    assert detect_pii(str(dataset[0]["summary"])) == ()
    assert detect_pii(str(dataset[0]["details"])) == ()


def test_preprocess_does_not_sanitize_plain_identifier_words_without_values() -> None:
    """Identifier-like words without values are not treated as residual PII."""

    tickets = [{"summary": "Champ login.", "details": "Le champ client_id."}]

    dataset = build_preprocessed_ticket_dataset(tickets)

    assert dataset == [{"summary": "Champ login.", "details": "Le champ client_id."}]
