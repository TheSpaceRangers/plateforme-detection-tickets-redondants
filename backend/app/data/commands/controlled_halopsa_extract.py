"""Fail-closed HaloPSA extraction command boundary.

This module is import-safe: it does not read environment variables, open network
connections, or persist tickets at import time. The default CLI path validates
runtime configuration and then stops unless an explicit network transport and a
repository-backed ingestion service are injected by integration code.

HALO_PAGE_SIZE defaults to 1 when absent and is capped at 5.
HALOPSA_ENABLE_NETWORK=true is required before the real HTTP transport is built.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient, HaloPsaTransport
from backend.app.data.extractors.halopsa_config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_TICKETS_PATH,
    DEFAULT_TOKEN_PATH,
    MAX_PAGE_SIZE,
    SAFE_DEFAULT_PAGE_SIZE,
    HaloPsaExtractorConfig,
    InvalidHaloPsaConfigurationError,
)
from backend.app.data.extractors.halopsa_http_transport import HaloPsaHttpTransport
from backend.app.data.extractors.halopsa_ticket_extractor import HaloPsaTicketExtractor
from backend.app.db.repositories.ticket_repository import TicketRepository
from backend.app.schemas.tickets import IngestionResult
from backend.app.services.ticket_ingestion_service import TicketIngestionService

REQUIRED_ENV_KEYS: tuple[str, ...] = (
    "SYNAPPSE_AGENT_ID_HMAC_SECRET",
    "HALOPSA_BASE_URL",
    "HALOPSA_CLIENT_ID",
    "HALOPSA_CLIENT_SECRET",
    "HALOPSA_TENANT",
    "HALO_SCOPE",
)
NETWORK_ENABLE_KEY = "HALOPSA_ENABLE_NETWORK"
TRUE_ENV_VALUES = frozenset(("1", "true", "yes", "on"))
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_LOCAL_DOTENV_PATH = PROJECT_ROOT / "ml" / ".env"


class DotenvLoader(Protocol):
    """Mockable dotenv loader contract for local controlled execution."""

    def __call__(self, dotenv_path: str | os.PathLike[str], *, override: bool = False) -> bool:
        """Load a dotenv file without overriding explicitly exported variables."""


class ControlledExtractionError(RuntimeError):
    """Raised when controlled extraction must fail closed before unsafe work."""


class SafeLogger(Protocol):
    """Minimal logger contract restricted to non-sensitive operational events."""

    def info(self, message: str, *args: object) -> None:
        """Log a non-sensitive informational message."""

    def error(self, message: str, *args: object) -> None:
        """Log a non-sensitive error message."""


class IngestionService(Protocol):
    """Mockable boundary for the privacy-guarded TicketIngestionService."""

    def ingest_tickets(self, include_agent_pseudonym: bool = False) -> IngestionResult:
        """Ingest tickets through privacy guardrails before storage."""


@dataclass(frozen=True, slots=True)
class ControlledExtractionResult:
    """Non-sensitive command result with counts only."""

    extracted_count: int
    stored_count: int
    status: str


def build_config_from_env(env: Mapping[str, str]) -> HaloPsaExtractorConfig:
    """Build a validated HaloPSA config from explicit environment mapping."""

    missing_keys = tuple(key for key in REQUIRED_ENV_KEYS if not env.get(key, "").strip())
    if missing_keys:
        raise ControlledExtractionError(f"Missing required runtime variables: {', '.join(missing_keys)}")

    page_size = _parse_page_size(env.get("HALO_PAGE_SIZE"))
    config = HaloPsaExtractorConfig(
        base_url=env["HALOPSA_BASE_URL"].strip(),
        client_id=env["HALOPSA_CLIENT_ID"].strip(),
        client_secret=env["HALOPSA_CLIENT_SECRET"].strip(),
        tenant=env["HALOPSA_TENANT"].strip(),
        scope=env["HALO_SCOPE"].strip(),
        page_size=page_size,
        request_timeout_seconds=_parse_positive_float(
            env.get("HALOPSA_REQUEST_TIMEOUT_SECONDS"),
            default_value=DEFAULT_REQUEST_TIMEOUT_SECONDS,
            field_name="HALOPSA_REQUEST_TIMEOUT_SECONDS",
        ),
        max_retries=_parse_non_negative_int(
            env.get("HALOPSA_MAX_RETRIES"),
            default_value=DEFAULT_MAX_RETRIES,
            field_name="HALOPSA_MAX_RETRIES",
        ),
        token_path=env.get("HALOPSA_TOKEN_PATH", DEFAULT_TOKEN_PATH).strip() or DEFAULT_TOKEN_PATH,
        tickets_path=env.get("HALOPSA_TICKETS_PATH", DEFAULT_TICKETS_PATH).strip() or DEFAULT_TICKETS_PATH,
    )
    try:
        config.validate()
    except InvalidHaloPsaConfigurationError as exc:
        raise ControlledExtractionError(str(exc)) from exc
    return config


def run_controlled_halopsa_extract(
    *,
    env: Mapping[str, str],
    transport: HaloPsaTransport | None = None,
    repository: TicketRepository | None = None,
    ingestion_service: IngestionService | None = None,
    logger: SafeLogger | None = None,
) -> ControlledExtractionResult:
    """Run a minimal controlled extraction through TicketIngestionService.

    Network and storage dependencies are deliberately absent by default. Tests
    should inject mocks; future runtime wiring must inject a real transport and
    repository explicitly after operational approval.
    """

    safe_logger = logger or logging.getLogger(__name__)
    config = build_config_from_env(env)
    if isinstance(transport, HaloPsaHttpTransport) and not _is_network_enabled(env):
        raise ControlledExtractionError("HaloPSA network transport is not explicitly enabled")
    selected_transport = transport or _build_explicit_network_transport(env)
    service = ingestion_service or _build_ingestion_service(config, selected_transport, repository)

    safe_logger.info("Controlled HaloPSA extraction started")
    result = service.ingest_tickets(include_agent_pseudonym=True)
    safe_logger.info(
        "Controlled HaloPSA extraction completed with extracted_count=%s stored_count=%s",
        result.extracted_count,
        result.stored_count,
    )
    return ControlledExtractionResult(
        extracted_count=result.extracted_count,
        stored_count=result.stored_count,
        status=result.status,
    )


def load_local_dotenv(
    *,
    dotenv_path: str | os.PathLike[str] = DEFAULT_LOCAL_DOTENV_PATH,
    dotenv_loader: DotenvLoader = load_dotenv,
) -> bool:
    """Load the explicit local dotenv file without exposing or overriding values."""

    return dotenv_loader(dotenv_path, override=False)


def main(
    *,
    dotenv_path: str | os.PathLike[str] = DEFAULT_LOCAL_DOTENV_PATH,
    dotenv_loader: DotenvLoader = load_dotenv,
) -> int:
    """Validate configuration and fail closed without implicit network or storage."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger = logging.getLogger(__name__)
    load_local_dotenv(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)
    try:
        run_controlled_halopsa_extract(env=os.environ, logger=logger)
    except ControlledExtractionError as exc:
        logger.error("Controlled HaloPSA extraction blocked: %s", exc)
        return 2
    return 0


def _build_ingestion_service(
    config: HaloPsaExtractorConfig,
    transport: HaloPsaTransport | None,
    repository: TicketRepository | None,
) -> TicketIngestionService:
    """Create the standard ingestion service only when dependencies are explicit."""

    if transport is None:
        raise ControlledExtractionError("HaloPSA network transport is not explicitly configured")
    if repository is None:
        raise ControlledExtractionError("Ticket repository is not explicitly configured")

    client = HaloPsaTicketClient(config=config, transport=transport)
    extractor = HaloPsaTicketExtractor(client=client)
    return TicketIngestionService(extractor=extractor, repository=repository)


def _build_explicit_network_transport(env: Mapping[str, str]) -> HaloPsaTransport | None:
    """Create the real transport only when the network enable flag is explicitly true."""

    if _is_network_enabled(env):
        return HaloPsaHttpTransport()
    return None


def _is_network_enabled(env: Mapping[str, str]) -> bool:
    """Return whether the runtime explicitly opted in to HaloPSA network calls."""

    return env.get(NETWORK_ENABLE_KEY, "").strip().lower() in TRUE_ENV_VALUES


def _parse_page_size(raw_page_size: str | None) -> int:
    """Parse HALO_PAGE_SIZE with a safe default and cap values above the maximum."""

    if raw_page_size is None or not raw_page_size.strip():
        return SAFE_DEFAULT_PAGE_SIZE
    try:
        page_size = int(raw_page_size)
    except ValueError as exc:
        raise ControlledExtractionError("HALO_PAGE_SIZE must be an integer") from exc
    if page_size <= 0:
        raise ControlledExtractionError("HALO_PAGE_SIZE must be strictly positive")
    return min(page_size, MAX_PAGE_SIZE)


def _parse_positive_float(raw_value: str | None, *, default_value: float, field_name: str) -> float:
    """Parse a strictly positive float runtime setting without exposing its raw value."""

    if raw_value is None or not raw_value.strip():
        return default_value
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ControlledExtractionError(f"{field_name} must be a number") from exc
    if value <= 0:
        raise ControlledExtractionError(f"{field_name} must be strictly positive")
    return value


def _parse_non_negative_int(raw_value: str | None, *, default_value: int, field_name: str) -> int:
    """Parse a non-negative integer runtime setting without exposing its raw value."""

    if raw_value is None or not raw_value.strip():
        return default_value
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ControlledExtractionError(f"{field_name} must be an integer") from exc
    if value < 0:
        raise ControlledExtractionError(f"{field_name} must be zero or positive")
    return value


if __name__ == "__main__":
    sys.exit(main())
