"""Synthetic unit tests for provider email sanitization before ML guardrails."""

from __future__ import annotations

import pytest

from backend.app.data.sanitizers import EMAIL_REPLACEMENT, sanitize_provider_text


@pytest.mark.parametrize(
    ("raw_text", "expected_text"),
    [
        ("Contact <qa.person@example.test>", f"Contact {EMAIL_REPLACEMENT}"),
        ("Write mailto:qa.person@example.test", f"Write {EMAIL_REPLACEMENT}"),
        ("<p>Owner: qa.person&#64;example.test</p>", f"Owner: {EMAIL_REPLACEMENT}"),
        ("Owner (qa.person@example.test),", f"Owner ({EMAIL_REPLACEMENT}),"),
        (
            "Escalate to qa.o'neil/team_test-alpha@example.engineering",
            f"Escalate to {EMAIL_REPLACEMENT}",
        ),
        ("FULLWIDTH ｑａ．ｐｅｒｓｏｎ＠ｅｘａｍｐｌｅ．ｔｅｓｔ", f"FULLWIDTH {EMAIL_REPLACEMENT}"),
        ("MixedCase QA.Person@Example.Test", f"MixedCase {EMAIL_REPLACEMENT}"),
    ],
)
def test_sanitize_provider_text_masks_supported_synthetic_email_forms(raw_text: str, expected_text: str) -> None:
    # Arrange
    value = raw_text

    # Act
    sanitized = sanitize_provider_text(value)

    # Assert
    assert sanitized == expected_text


@pytest.mark.parametrize(
    "raw_text",
    [
        "Keep <strong>synthetic text</strong> without mailbox",
        "Mention mailto: synthetic-alias without domain",
        "Ignore qa.person@example without valid long enough suffix",
        "Ignore qa.person at example.test when separator is textual",
    ],
)
def test_sanitize_provider_text_does_not_mask_non_email_synthetic_text(raw_text: str) -> None:
    # Arrange
    value = raw_text

    # Act
    sanitized = sanitize_provider_text(value)

    # Assert
    assert EMAIL_REPLACEMENT not in sanitized
