"""Real HaloPSA HTTP transport guarded behind explicit runtime activation."""

from __future__ import annotations

import json
import time
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from backend.app.data.extractors.halopsa_config import HaloPsaExtractorConfig


class HaloPsaHttpTransportError(RuntimeError):
    """Raised when the HaloPSA HTTP transport cannot complete safely."""


class HaloPsaHttpTransport:
    """HTTP transport for HaloPSA OAuth client credentials and ticket retrieval."""

    def __init__(self) -> None:
        self._last_request_at: float | None = None

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
            rate_limit_per_minute=config.rate_limit_per_minute,
        )
        return tuple(self._extract_ticket_items(response)[: config.max_total_tickets])

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
            url=_build_halopsa_url(config.base_url, config.token_path),
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            body=urlencode(form_values).encode("utf-8"),
            timeout_seconds=config.request_timeout_seconds,
            max_retries=config.max_retries,
            rate_limit_per_minute=config.rate_limit_per_minute,
        )
        token = response.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise HaloPsaHttpTransportError("HaloPSA OAuth response did not include an access token")
        return token

    def _build_tickets_url(self, config: HaloPsaExtractorConfig) -> str:
        """Build a bounded ticket endpoint URL using only non-sensitive query values."""

        config.validate()
        endpoint = _build_halopsa_url(config.base_url, config.tickets_path)
        separator = "&" if "?" in endpoint else "?"
        query_params = {
            "pageinate": "true",
            "page_size": config.page_size,
            "page_no": config.page_no,
        }
        return f"{endpoint}{separator}{urlencode(query_params)}"

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes | None,
        timeout_seconds: float,
        max_retries: int,
        rate_limit_per_minute: int,
    ) -> Mapping[str, Any]:
        """Execute a bounded JSON request and return parsed JSON without sensitive details in errors."""

        last_error: Exception | None = None
        for _attempt in range(max_retries + 1):
            self._respect_rate_limit(rate_limit_per_minute)
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

    def _respect_rate_limit(self, rate_limit_per_minute: int) -> None:
        """Throttle outbound requests according to the configured minute rate."""

        min_interval_seconds = 60.0 / rate_limit_per_minute
        now = time.monotonic()
        if self._last_request_at is not None:
            elapsed_seconds = now - self._last_request_at
            if elapsed_seconds < min_interval_seconds:
                time.sleep(min_interval_seconds - elapsed_seconds)
                now = time.monotonic()
        self._last_request_at = now

    def _extract_ticket_items(self, response: Mapping[str, Any]) -> tuple[Mapping[str, object], ...]:
        """Return provider ticket mappings from accepted HaloPSA list containers."""

        items = _first_present_ticket_container(response, ("tickets", "results", "data", "items"))
        if not isinstance(items, list):
            raise HaloPsaHttpTransportError("HaloPSA ticket response did not include a ticket list")
        return tuple(item for item in items if isinstance(item, Mapping))


def _first_present_ticket_container(response: Mapping[str, Any], container_names: tuple[str, ...]) -> Any:
    """Return the first present ticket list container without treating empty lists as absent."""

    for container_name in container_names:
        if container_name in response:
            return response[container_name]
    return None


def _build_halopsa_url(base_url: str, endpoint_path: str) -> str:
    """Build a HaloPSA URL while avoiding duplicated API path segments."""

    split_base = urlsplit(base_url.strip())
    normalized_base_path = split_base.path.rstrip("/")
    normalized_endpoint_path = endpoint_path.strip()
    endpoint_query = ""
    if "?" in normalized_endpoint_path:
        normalized_endpoint_path, endpoint_query = normalized_endpoint_path.split("?", 1)
    base_segments = _path_segments(normalized_base_path)
    endpoint_segments = _path_segments(normalized_endpoint_path)

    if normalized_endpoint_path.startswith("/"):
        if _starts_with_api_segment(endpoint_segments) and _ends_with_api_segment(base_segments):
            path_segments = (*base_segments, *endpoint_segments[1:])
        elif _starts_with_api_segment(endpoint_segments):
            path_segments = tuple(endpoint_segments)
        else:
            path_segments = tuple(endpoint_segments)
    else:
        if _starts_with_api_segment(endpoint_segments) and _ends_with_api_segment(base_segments):
            endpoint_segments = endpoint_segments[1:]
        path_segments = (*base_segments, *endpoint_segments)

    path = "/" + "/".join(path_segments) if path_segments else ""
    return urlunsplit((split_base.scheme, split_base.netloc, path, endpoint_query, ""))


def _path_segments(path: str) -> tuple[str, ...]:
    """Return non-empty URL path segments without decoding provider values."""

    return tuple(segment for segment in path.strip("/").split("/") if segment)


def _starts_with_api_segment(path_segments: tuple[str, ...]) -> bool:
    """Return whether URL path segments start with the HaloPSA API segment."""

    return bool(path_segments) and path_segments[0].lower() == "api"


def _ends_with_api_segment(path_segments: tuple[str, ...]) -> bool:
    """Return whether URL path segments end with the HaloPSA API segment."""

    return bool(path_segments) and path_segments[-1].lower() == "api"
