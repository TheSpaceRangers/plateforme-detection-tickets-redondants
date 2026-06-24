"""Provider text sanitizers applied before ML privacy guardrails."""

from __future__ import annotations

import html
import re
import unicodedata

EMAIL_REPLACEMENT = "[EMAIL]"
_EMAIL_LOCAL_PART = r"[A-Z0-9](?:[A-Z0-9.!#$%&'*+/=?^_`{|}~-]{0,62}[A-Z0-9])?"
_EMAIL_DOMAIN_LABEL = r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
_EMAIL_DOMAIN = rf"(?:{_EMAIL_DOMAIN_LABEL}\.)+[A-Z]{{2,63}}"
_EMAIL_PATTERN = rf"(?<![A-Z0-9.!#$%&'*+/=?^_`{{|}}~-]){_EMAIL_LOCAL_PART}@{_EMAIL_DOMAIN}(?![A-Z0-9-])"
_EMAIL_REGEX = re.compile(_EMAIL_PATTERN, re.IGNORECASE)
_HTML_TAG_REGEX = re.compile(r"</?[A-Z][^>]*>", re.IGNORECASE)
_BRACKETED_EMAIL_PLACEHOLDER_REGEX = re.compile(r"<\s*(\[EMAIL\])\s*>", re.IGNORECASE)
_MAILTO_PLACEHOLDER_REGEX = re.compile(r"\bmailto:\s*(\[EMAIL\])", re.IGNORECASE)


def sanitize_provider_text(value: object | None) -> str:
    """Normalize rich provider text and mask detector-compatible email patterns."""

    if value is None:
        return ""

    normalized_text = _normalize_text(str(value).strip())
    masked_text = _mask_email_patterns(normalized_text)
    text_without_tags = _strip_html_tags(masked_text)
    return _normalize_placeholder_wrappers(text_without_tags).strip()


def _normalize_text(text: str) -> str:
    """Decode HTML entities and normalize Unicode confusables before matching."""

    return unicodedata.normalize("NFKC", html.unescape(text))


def _mask_email_patterns(text: str) -> str:
    """Replace email patterns with the same placeholder used by ML guardrails."""

    return _EMAIL_REGEX.sub(EMAIL_REPLACEMENT, text)


def _strip_html_tags(text: str) -> str:
    """Remove HTML tags after masking so angle-bracketed emails are preserved."""

    return _HTML_TAG_REGEX.sub(" ", text)


def _normalize_placeholder_wrappers(text: str) -> str:
    """Remove wrappers that can surround already-masked email placeholders."""

    without_brackets = _BRACKETED_EMAIL_PLACEHOLDER_REGEX.sub(r"\1", text)
    return _MAILTO_PLACEHOLDER_REGEX.sub(r"\1", without_brackets)
