"""Provider text sanitizers applied before ML privacy guardrails."""

from __future__ import annotations

import html
import re
import unicodedata

from ml.src.preprocessing.pii import sanitize_text

_HTML_TAG_REGEX = re.compile(r"</?[A-Z][^>]*>", re.IGNORECASE)
_BRACKETED_EMAIL_PLACEHOLDER_REGEX = re.compile(r"<\s*(\[EMAIL\])\s*>", re.IGNORECASE)
_MAILTO_PLACEHOLDER_REGEX = re.compile(r"\bmailto:\s*(\[EMAIL\])", re.IGNORECASE)


def sanitize_provider_text(value: object | None) -> str:
    """Normalize provider text and apply the ML detector-based PII sanitizer."""

    if value is None:
        return ""

    normalized_text = _normalize_text(str(value).strip())
    sanitized_text = _sanitize_with_ml_detector(normalized_text)
    text_with_plain_placeholders = _normalize_placeholder_wrappers(sanitized_text)
    text_without_tags = _strip_html_tags(text_with_plain_placeholders)
    return _normalize_placeholder_wrappers(text_without_tags).strip()


def _normalize_text(text: str) -> str:
    """Decode HTML entities and normalize Unicode confusables before matching."""

    return unicodedata.normalize("NFKC", html.unescape(text))


def _sanitize_with_ml_detector(text: str) -> str:
    """Replace PII using the ML preprocessing detector as the single source of truth."""

    return sanitize_text(text).text


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags after masking so angle-bracketed emails are preserved."""

    return _HTML_TAG_REGEX.sub(" ", text)


def _normalize_placeholder_wrappers(text: str) -> str:
    """Remove wrappers that can surround already-masked email placeholders."""

    without_mailto = _MAILTO_PLACEHOLDER_REGEX.sub(r"\1", text)
    return _BRACKETED_EMAIL_PLACEHOLDER_REGEX.sub(r"\1", without_mailto)
