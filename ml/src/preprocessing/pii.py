"""PII detection and sanitization for synthetic ticket text fields."""

from __future__ import annotations

import html
import re
import unicodedata
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
    normalized_text = normalize_text_for_pii(text)
    for category, pattern in PII_PATTERNS.items():
        matches.extend(
            PiiMatch(category=category, start=match.start(), end=match.end())
            for match in pattern.finditer(normalized_text)
        )
    return tuple(sorted(matches, key=lambda item: (item.start, item.end, item.category)))


def sanitize_text(text: str) -> PiiSanitizationResult:
    """Replace frequent PII in a ticket text field with typed placeholders."""

    sanitized = normalize_text_for_pii(text)
    return _sanitize_with_detector_matches(sanitized)


def normalize_text_for_pii(text: str) -> str:
    """Normalize text before PII detection and sanitization."""

    return unicodedata.normalize("NFKC", html.unescape(text))


def _sanitize_with_detector_matches(text: str) -> PiiSanitizationResult:
    """Apply replacements from detector offsets to keep both flows aligned."""

    matches = detect_pii(text)
    if not matches:
        return PiiSanitizationResult(text=text, removed_categories=())

    sanitized = _replace_non_overlapping_matches(text, matches)
    return PiiSanitizationResult(text=sanitized, removed_categories=_categories_in_order(matches))


def _replace_non_overlapping_matches(text: str, matches: tuple[PiiMatch, ...]) -> str:
    """Replace detector matches while avoiding duplicate overlap edits."""

    chunks: list[str] = []
    cursor = 0
    for match in matches:
        if match.start < cursor:
            continue
        chunks.append(text[cursor : match.start])
        chunks.append(PII_REPLACEMENTS[match.category])
        cursor = match.end
    chunks.append(text[cursor:])
    return "".join(chunks)


def _categories_in_order(matches: tuple[PiiMatch, ...]) -> tuple[str, ...]:
    """Return unique matched categories without exposing matched values."""

    removed_categories: list[str] = []
    for match in matches:
        category = match.category
        if category not in removed_categories:
            removed_categories.append(category)
    return tuple(removed_categories)


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
