"""PII detection and sanitization for synthetic ticket text fields."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Mapping, Pattern


TEXT_FIELDS: tuple[str, str] = ("summary", "details")

_EMAIL_LOCAL_PART = r"[A-Z0-9](?:[A-Z0-9.!#$%&'*+/=?^_`{|}~-]{0,62}[A-Z0-9])?"
_EMAIL_DOMAIN_LABEL = r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
_EMAIL_DOMAIN = rf"(?:{_EMAIL_DOMAIN_LABEL}\.)+[A-Z]{{2,63}}"
_EMAIL_PATTERN = rf"(?<![A-Z0-9.!#$%&'*+/=?^_`{{|}}~-]){_EMAIL_LOCAL_PART}@{_EMAIL_DOMAIN}(?![A-Z0-9-])"


@dataclass(frozen=True)
class PiiMatch:
    """Detected PII metadata without exposing the matched value."""

    category: str
    start: int
    end: int



@dataclass(frozen=True)
class PiiSanitizationResult:
    """Sanitized text plus categories removed during preprocessing."""

    text: str
    removed_categories: tuple[str, ...]


class PiiResidualError(ValueError):
    """Raised when residual PII is found after sanitization."""


PII_PATTERNS: Mapping[str, Pattern[str]] = {
    "email": re.compile(_EMAIL_PATTERN, re.IGNORECASE),
    "fr_phone": re.compile(r"(?<!\d)(?:\+33|0033|0)\s*[1-9](?:[\s.-]*\d{2}){4}(?!\d)"),
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
    ),
    "url": re.compile(r"\b(?:https?://|www\.)[^\s<>'\"]+", re.IGNORECASE),
    "obvious_identifier": re.compile(
        r"\b(?:agent_id|user_id|client_id|customer_id|account_id|identifiant|login|username)\b\s*[:=#-]?\s*[A-Z0-9._@-]{3,}",
        re.IGNORECASE,
    ),
}

PII_REPLACEMENTS: Mapping[str, str] = {
    "email": "[EMAIL]",
    "fr_phone": "[PHONE]",
    "ipv4": "[IP]",
    "url": "[URL]",
    "obvious_identifier": "[IDENTIFIER]",
}


def detect_pii(text: str) -> tuple[PiiMatch, ...]:
    """Detect supported PII categories without returning sensitive values."""

    matches: list[PiiMatch] = []
    for category, pattern in PII_PATTERNS.items():
        matches.extend(
            PiiMatch(category=category, start=match.start(), end=match.end()) for match in pattern.finditer(text)
        )
    return tuple(sorted(matches, key=lambda item: (item.start, item.end, item.category)))


def sanitize_text(text: str) -> PiiSanitizationResult:
    """Replace frequent PII in a ticket text field with typed placeholders."""

    sanitized = text
    removed_categories: list[str] = []
    for category, pattern in PII_PATTERNS.items():
        sanitized, replacement_count = pattern.subn(PII_REPLACEMENTS[category], sanitized)
        if replacement_count:
            removed_categories.append(category)
    return PiiSanitizationResult(text=sanitized, removed_categories=tuple(removed_categories))


def sanitize_ticket_text_fields(ticket: Mapping[str, object]) -> dict[str, object]:
    """Sanitize only the ticket summary and details text fields."""

    sanitized_ticket = dict(ticket)
    for field in TEXT_FIELDS:
        raw_value = ticket.get(field, "")
        result = sanitize_text(str(raw_value) if raw_value is not None else "")
        sanitized_ticket[field] = result.text
    return sanitized_ticket


def assert_no_residual_pii(records: Iterable[Mapping[str, object]], fields: tuple[str, ...] = TEXT_FIELDS) -> None:
    """Block dataset creation when residual PII remains in checked text fields."""

    residuals: list[str] = []
    for row_index, record in enumerate(records):
        for field in fields:
            value = str(record.get(field, "") or "")
            categories = sorted({match.category for match in detect_pii(value)})
            if categories:
                residuals.append(f"row={row_index}, field={field}, categories={','.join(categories)}")
    if residuals:
        raise PiiResidualError("Residual PII detected after sanitization: " + "; ".join(residuals))
