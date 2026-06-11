"""Real HaloPSA HTTP transport guarded behind explicit runtime activation."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig


class HaloPsaHttpTransportError(RuntimeError):
    """Raised when the HaloPSA HTTP transport cannot complete safely."""


class HaloPsaHttpTransport:
    """HTTP transport for HaloPSA OAuth client credentials and ticket retrieval."""

    def fetch_tickets(self, config: HaloPsaExtractorConfig) -> Iterable[Mapping[str, object]]:
        """Fetch one bounded ticket page from HaloPSA without logging raw provider data."""

        config.validate()
        token = self._fetch_access_token(config)
        response = self._request_json(
            method="GET",
            url=self._build_tickets_url(config),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            body=None,
            timeout_seconds=config.request_timeout_seconds,
            max_retries=config.max_retries,
        )
        return tuple(self._extract_ticket_items(response))

    def _fetch_access_token(self, config: HaloPsaExtractorConfig) -> str:
        """Request an OAuth client credentials token from HaloPSA."""

        form_values = {
            "grant_type": "client_credentials",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "tenant": config.tenant,
        }
        if config.scope.strip():
            form_values["scope"] = config.scope.strip()

        response = self._request_json(
            method="POST",
            url=urljoin(_ensure_trailing_slash(config.base_url), config.token_path.lstrip("/")),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            body=urlencode(form_values).encode("utf-8"),
            timeout_seconds=config.request_timeout_seconds,
            max_retries=config.max_retries,
        )
        token = response.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise HaloPsaHttpTransportError("HaloPSA OAuth response did not include an access token")
        return token

    def _build_tickets_url(self, config: HaloPsaExtractorConfig) -> str:
        """Build a bounded ticket endpoint URL using only non-sensitive query values."""

        endpoint = urljoin(_ensure_trailing_slash(config.base_url), config.tickets_path.lstrip("/"))
        separator = "&" if "?" in endpoint else "?"
        return f"{endpoint}{separator}{urlencode({'page_size': config.page_size})}"

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_seconds: float,
        max_retries: int,
    ) -> Mapping[str, Any]:
        """Execute a bounded JSON request and return parsed JSON without sensitive details in errors."""

        last_error: Exception | None = None
        for _attempt in range(max_retries + 1):
            request = Request(url=url, data=body, headers=dict(headers), method=method)
            try:
                with urlopen(request, timeout=timeout_seconds) as response:  # nosec B310: explicit opt-in transport
                    decoded = response.read().decode("utf-8")
                parsed = json.loads(decoded)
                if not isinstance(parsed, dict):
                    raise HaloPsaHttpTransportError("HaloPSA response JSON must be an object")
                return parsed
            except HTTPError as exc:
                if 400 <= exc.code < 500:
                    raise HaloPsaHttpTransportError(f"HaloPSA HTTP request failed with status {exc.code}") from exc
                last_error = exc
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
        raise HaloPsaHttpTransportError("HaloPSA HTTP request failed after bounded retries") from last_error

    def _extract_ticket_items(self, response: Mapping[str, Any]) -> tuple[Mapping[str, object], ...]:
        """Return provider ticket mappings from accepted HaloPSA list containers."""

        items = response.get("tickets") or response.get("results") or response.get("data")
        if items is None and isinstance(response.get("items"), list):
            items = response["items"]
        if not isinstance(items, list):
            raise HaloPsaHttpTransportError("HaloPSA ticket response did not include a ticket list")
        return tuple(item for item in items if isinstance(item, Mapping))


def _ensure_trailing_slash(value: str) -> str:
    """Return a URL prefix suitable for urllib.parse.urljoin."""

    return value if value.endswith("/") else f"{value}/"
