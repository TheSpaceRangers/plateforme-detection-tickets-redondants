"""Fail-closed HaloPSA extraction command boundary.

This module is import-safe: it does not read environment variables, open network
connections, or persist tickets at import time. The default CLI path validates
runtime configuration and then stops unless an explicit network transport and a
repository-backed ingestion service are injected by integration code.

HALO_PAGE_SIZE defaults to 1 and is capped by HALOPSA_MAX_PAGE_SIZE.
HALOPSA_MAX_TOTAL_TICKETS defaults to a safe one-page ceiling.
HALO_PAGE_NO defaults to 1 when absent.
SYNAPPSE_COMPLIANCE_GO_REAL_EXTRACTION=true is required before any real network or write wiring.
HALOPSA_ENABLE_NETWORK=true is still required before the real HTTP transport is built.
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from backend.app.data.extractors.halopsa_client import HaloPsaTicketClient, HaloPsaTransport
from backend.app.data.extractors.halopsa_config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_PAGE_NO,
    DEFAULT_RATE_LIMIT_PER_MINUTE,
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_TICKETS_PATH,
    DEFAULT_TOKEN_PATH,
    SAFE_DEFAULT_PAGE_SIZE,
    SAFE_MAX_PAGE_SIZE,
    SAFE_MAX_TOTAL_TICKETS,
    HaloPsaExtractorConfig,
    InvalidHaloPsaConfigurationError,
)
from backend.app.data.extractors.halopsa_http_transport import HaloPsaHttpTransport
from backend.app.data.extractors.halopsa_ticket_extractor import HaloPsaTicketExtractor
from backend.app.db.postgres_config import (
    PostgresConnectionConfig,
    PostgresConfigurationError,
    is_postgres_write_enabled,
)
from backend.app.db.repositories.ticket_repository import PostgresTicketRepository, TicketRepository
from backend.app.schemas.tickets import IngestionResult
from backend.app.services.ticket_ingestion_service import TicketIngestionService

_REAL_HALOPSA_HTTP_TRANSPORT_TYPE = HaloPsaHttpTransport

REQUIRED_ENV_KEYS: tuple[str, ...] = (
    "HALOPSA_BASE_URL",
    "HALOPSA_CLIENT_ID",
    "HALOPSA_CLIENT_SECRET",
    "HALOPSA_TENANT",
    "HALO_SCOPE",
)
NETWORK_ENABLE_KEY = "HALOPSA_ENABLE_NETWORK"
COMPLIANCE_GO_REAL_EXTRACTION_KEY = "SYNAPPSE_COMPLIANCE_GO_REAL_EXTRACTION"
INCLUDE_AGENT_PSEUDONYM_KEY = "SYNAPPSE_INCLUDE_AGENT_PSEUDONYM"
TRUE_ENV_VALUES = frozenset(("1", "true", "yes", "on"))
PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_LOCAL_DOTENV_PATH = PROJECT_ROOT / "backend" / ".env"


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
    ignored_count: int = 0


def build_config_from_env(env: Mapping[str, str]) -> HaloPsaExtractorConfig:
    """Build a validated HaloPSA config from explicit environment mapping."""

    missing_keys = tuple(key for key in REQUIRED_ENV_KEYS if not env.get(key, "").strip())
    if missing_keys:
        raise ControlledExtractionError(f"Missing required runtime variables: {', '.join(missing_keys)}")

    configured_max_page_size = _parse_capped_positive_int(
        env.get("HALOPSA_MAX_PAGE_SIZE"),
        default_value=SAFE_MAX_PAGE_SIZE,
        hard_cap=SAFE_MAX_PAGE_SIZE,
        field_name="HALOPSA_MAX_PAGE_SIZE",
    )
    max_total_tickets = _parse_capped_positive_int(
        env.get("HALOPSA_MAX_TOTAL_TICKETS"),
        default_value=SAFE_MAX_TOTAL_TICKETS,
        hard_cap=SAFE_MAX_TOTAL_TICKETS,
        field_name="HALOPSA_MAX_TOTAL_TICKETS",
    )
    page_size = _parse_page_size(env.get("HALO_PAGE_SIZE"), configured_max_page_size=configured_max_page_size)
    page_no = _parse_positive_int(
        env.get("HALO_PAGE_NO"),
        default_value=DEFAULT_PAGE_NO,
        field_name="HALO_PAGE_NO",
    )
    config = HaloPsaExtractorConfig(
        base_url=env["HALOPSA_BASE_URL"].strip(),
        client_id=env["HALOPSA_CLIENT_ID"].strip(),
        client_secret=env["HALOPSA_CLIENT_SECRET"].strip(),
        tenant=env["HALOPSA_TENANT"].strip(),
        scope=env["HALO_SCOPE"].strip(),
        page_size=page_size,
        max_total_tickets=max_total_tickets,
        page_no=page_no,
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
        rate_limit_per_minute=_parse_positive_int(
            env.get("HALOPSA_RATE_LIMIT_PER_MINUTE"),
            default_value=DEFAULT_RATE_LIMIT_PER_MINUTE,
            field_name="HALOPSA_RATE_LIMIT_PER_MINUTE",
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
    if _requires_real_extraction_approval(
        env=env,
        transport=transport,
        repository=repository,
        ingestion_service=ingestion_service,
    ) and not _has_compliance_go_for_real_extraction(env):
        raise ControlledExtractionError("Compliance GO for real HaloPSA extraction is not explicitly enabled")
    if _is_real_http_transport(transport) and not _is_network_enabled(env):
        raise ControlledExtractionError("HaloPSA network transport is not explicitly enabled")
    if isinstance(repository, PostgresTicketRepository) and not is_postgres_write_enabled(env):
        raise ControlledExtractionError("PostgreSQL ticket writes are not explicitly enabled")
    selected_transport = transport or _build_explicit_network_transport(env)
    selected_repository = repository or _build_explicit_postgres_repository(env, selected_transport, ingestion_service)
    service = ingestion_service or _build_ingestion_service(config, selected_transport, selected_repository)

    safe_logger.info("Controlled HaloPSA extraction started")
    result = service.ingest_tickets(include_agent_pseudonym=_should_include_agent_pseudonym(env))
    ignored_count = getattr(result, "ignored_count", 0)
    safe_logger.info(
        "Controlled HaloPSA extraction completed with extracted_count=%s stored_count=%s ignored_count=%s",
        result.extracted_count,
        result.stored_count,
        ignored_count,
    )
    return ControlledExtractionResult(
        extracted_count=result.extracted_count,
        stored_count=result.stored_count,
        ignored_count=ignored_count,
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
        if not _has_compliance_go_for_real_extraction(env):
            raise ControlledExtractionError("Compliance GO for real HaloPSA extraction is not explicitly enabled")
        return HaloPsaHttpTransport()
    return None


def _build_explicit_postgres_repository(
    env: Mapping[str, str],
    transport: HaloPsaTransport | None,
    ingestion_service: IngestionService | None,
) -> TicketRepository | None:
    """Create the real PostgreSQL repository only for the default runtime path."""

    if ingestion_service is not None or transport is None:
        return None
    if not is_postgres_write_enabled(env):
        raise ControlledExtractionError("PostgreSQL ticket writes are not explicitly enabled")
    try:
        postgres_config = PostgresConnectionConfig.from_env(env)
    except PostgresConfigurationError as exc:
        raise ControlledExtractionError(str(exc)) from exc
    return PostgresTicketRepository(
        connection_factory=_build_postgres_connection_factory(postgres_config),
        initialize_schema=True,
    )


def _build_postgres_connection_factory(config: PostgresConnectionConfig) -> Callable[[], object]:
    """Build a lazy psycopg connection factory without opening a connection now."""

    try:
        import psycopg
    except ImportError as exc:
        raise ControlledExtractionError("PostgreSQL driver psycopg is not installed") from exc

    def connect() -> object:
        """Open one PostgreSQL connection when ingestion reaches repository storage."""

        return psycopg.connect(**config.connection_kwargs())

    return connect


def _is_network_enabled(env: Mapping[str, str]) -> bool:
    """Return whether the runtime explicitly opted in to HaloPSA network calls."""

    return env.get(NETWORK_ENABLE_KEY, "").strip().lower() in TRUE_ENV_VALUES


def _has_compliance_go_for_real_extraction(env: Mapping[str, str]) -> bool:
    """Return whether compliance explicitly approved real extraction side effects."""

    return env.get(COMPLIANCE_GO_REAL_EXTRACTION_KEY, "").strip().lower() in TRUE_ENV_VALUES


def _should_include_agent_pseudonym(env: Mapping[str, str]) -> bool:
    """Return whether agent pseudonym storage is explicitly enabled after compliance GO."""

    if env.get(INCLUDE_AGENT_PSEUDONYM_KEY, "").strip().lower() not in TRUE_ENV_VALUES:
        return False
    if not _has_compliance_go_for_real_extraction(env):
        raise ControlledExtractionError("Agent pseudonym export requires explicit compliance GO")
    if not env.get("SYNAPPSE_AGENT_ID_HMAC_SECRET", "").strip():
        raise ControlledExtractionError("Agent pseudonym export requires SYNAPPSE_AGENT_ID_HMAC_SECRET")
    return True


def _requires_real_extraction_approval(
    *,
    env: Mapping[str, str],
    transport: HaloPsaTransport | None,
    repository: TicketRepository | None,
    ingestion_service: IngestionService | None,
) -> bool:
    """Detect runtime paths that could perform real network calls or database writes."""

    if ingestion_service is not None and transport is None and repository is None:
        return False
    return (
        _is_network_enabled(env)
        or is_postgres_write_enabled(env)
        or _is_real_http_transport(transport)
        or isinstance(repository, PostgresTicketRepository)
    )


def _is_real_http_transport(transport: HaloPsaTransport | None) -> bool:
    """Detect the real HTTP transport without depending on monkeypatchable symbols."""

    return isinstance(transport, _REAL_HALOPSA_HTTP_TRANSPORT_TYPE)


def _parse_page_size(raw_page_size: str | None, *, configured_max_page_size: int) -> int:
    """Parse HALO_PAGE_SIZE with a safe default and strict application cap."""

    if raw_page_size is None or not raw_page_size.strip():
        return SAFE_DEFAULT_PAGE_SIZE
    try:
        page_size = int(raw_page_size)
    except ValueError as exc:
        raise ControlledExtractionError("HALO_PAGE_SIZE must be an integer") from exc
    if page_size <= 0:
        raise ControlledExtractionError("HALO_PAGE_SIZE must be strictly positive")
    if page_size > configured_max_page_size:
        raise ControlledExtractionError("HALO_PAGE_SIZE exceeds configured maximum")
    return page_size


def _parse_capped_positive_int(
    raw_value: str | None,
    *,
    default_value: int,
    hard_cap: int,
    field_name: str,
) -> int:
    """Parse a positive integer that cannot exceed the hard safety cap."""

    value = _parse_positive_int(raw_value, default_value=default_value, field_name=field_name)
    if value > hard_cap:
        raise ControlledExtractionError(f"{field_name} exceeds hard safety cap")
    return value


def _parse_positive_int(raw_value: str | None, *, default_value: int, field_name: str) -> int:
    """Parse a strictly positive integer runtime setting without exposing its raw value."""

    if raw_value is None or not raw_value.strip():
        return default_value
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ControlledExtractionError(f"{field_name} must be an integer") from exc
    if value <= 0:
        raise ControlledExtractionError(f"{field_name} must be strictly positive")
    return value


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
