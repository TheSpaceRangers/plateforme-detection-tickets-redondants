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
from src.preprocessing.pii import sanitize_text, sanitize_ticket_text_fields
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


def test_preprocess_does_not_sanitize_plain_identifier_words_without_values() -> None:
    """Identifier-like words without values are not treated as residual PII."""

    tickets = [{"summary": "Champ login.", "details": "Le champ client_id."}]

    dataset = build_preprocessed_ticket_dataset(tickets)

    assert dataset == [{"summary": "Champ login.", "details": "Le champ client_id."}]


def test_sanitize_ticket_text_fields_masks_simple_email_in_details() -> None:
    """A simple synthetic email in details is replaced by the email placeholder."""

    # Arrange
    ticket = {"summary": "Demande synthétique", "details": "Contacter user@example.com"}

    # Act
    sanitized_ticket = sanitize_ticket_text_fields(ticket)

    # Assert
    assert sanitized_ticket["details"] == "Contacter [EMAIL]"
    assert detect_pii(str(sanitized_ticket["details"])) == ()


def test_sanitize_text_masks_uppercase_subdomain_plus_address_email() -> None:
    """A complex synthetic email with uppercase, subdomain, and plus addressing is masked."""

    # Arrange
    text = "Escalade vers USER+ALERT@HELPDESK.EXAMPLE.COM"

    # Act
    result = sanitize_text(text)

    # Assert
    assert result.text == "Escalade vers [EMAIL]"
    assert result.removed_categories == ("email",)
    assert detect_pii(result.text) == ()


def test_sanitize_text_masks_email_without_absorbing_terminal_punctuation() -> None:
    """Terminal punctuation next to a synthetic email remains outside the placeholder."""

    # Arrange
    text = "Réponse attendue de support@example.com, puis clôture."

    # Act
    result = sanitize_text(text)

    # Assert
    assert result.text == "Réponse attendue de [EMAIL], puis clôture."
    assert detect_pii(result.text) == ()


def test_assert_no_residual_pii_fails_closed_on_unsanitized_email_in_details() -> None:
    """Residual synthetic email in details blocks the record before storage/export."""

    # Arrange
    unsafe_records = [{"summary": "Diagnostic", "details": "Contact support@example.com"}]

    # Act / Assert
    with pytest.raises(PiiResidualError) as exc_info:
        assert_no_residual_pii(unsafe_records)
    assert "field=details" in str(exc_info.value)
    assert "categories=email" in str(exc_info.value)
    assert "support@example.com" not in str(exc_info.value)


def test_assert_no_residual_pii_accepts_sanitized_email_placeholder_in_details() -> None:
    """A sanitized email placeholder is not treated as residual PII."""

    # Arrange
    records = [{"summary": "Diagnostic", "details": "Contact [EMAIL]"}]

    # Act
    assert_no_residual_pii(records)

    # Assert
    assert records[0]["details"] == "Contact [EMAIL]"


def test_sanitize_text_does_not_overmask_at_sign_or_incomplete_domain() -> None:
    """Non-email text containing an at sign or incomplete domain is preserved."""

    # Arrange
    text = "Notifier @support puis vérifier utilisateur@example"

    # Act
    result = sanitize_text(text)

    # Assert
    assert result.text == text
    assert result.removed_categories == ()
