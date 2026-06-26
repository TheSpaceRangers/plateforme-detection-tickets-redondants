"""Command line entrypoint for secure aggregate-only ticket EDA."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

from backend.app.db.postgres_config import PostgresConnectionConfig, PostgresConfigurationError
from backend.app.db.repositories.ticket_eda_repository import AggregateTicketEdaRepository
from backend.app.schemas.ticket_eda import AggregateTicketEdaReport
from backend.app.services.ticket_eda_service import AggregateTicketEdaService

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_LOCAL_DOTENV_PATH = PROJECT_ROOT / "backend" / ".env"


class DotenvLoader(Protocol):
    """Mockable dotenv loader contract for local aggregate EDA execution."""

    def __call__(self, dotenv_path: str | os.PathLike[str], *, override: bool = False) -> bool:
        """Load a dotenv file without overriding exported runtime variables."""


class AggregateTicketEdaCommandError(RuntimeError):
    """Raised when aggregate EDA cannot run safely."""


def load_local_dotenv(
    *,
    dotenv_path: str | os.PathLike[str] = DEFAULT_LOCAL_DOTENV_PATH,
    dotenv_loader: DotenvLoader = load_dotenv,
) -> bool:
    """Load local dotenv values without printing or overriding them."""

    return dotenv_loader(dotenv_path, override=False)


def run_aggregate_ticket_eda(*, env: Mapping[str, str]) -> AggregateTicketEdaReport:
    """Build the secure aggregate-only ticket EDA report from PostgreSQL."""

    try:
        postgres_config = PostgresConnectionConfig.read_from_env(env)
    except PostgresConfigurationError as exc:
        raise AggregateTicketEdaCommandError(str(exc)) from exc
    repository = AggregateTicketEdaRepository(connection_factory=_build_postgres_connection_factory(postgres_config))
    service = AggregateTicketEdaService(repository=repository)
    return service.build_report()


def main(
    *,
    dotenv_path: str | os.PathLike[str] = DEFAULT_LOCAL_DOTENV_PATH,
    dotenv_loader: DotenvLoader = load_dotenv,
) -> int:
    """Print a JSON aggregate-only EDA report to stdout and write no files."""

    load_local_dotenv(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)
    try:
        report = run_aggregate_ticket_eda(env=os.environ)
    except (AggregateTicketEdaCommandError, ValueError) as exc:
        print(json.dumps({"error": "aggregate_ticket_eda_blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(_report_to_json(report))
    return 0


def _build_postgres_connection_factory(config: PostgresConnectionConfig) -> Callable[[], object]:
    """Build a lazy psycopg connection factory without opening a connection at import time."""

    try:
        import psycopg
    except ImportError as exc:
        raise AggregateTicketEdaCommandError("PostgreSQL driver psycopg is not installed") from exc

    def connect() -> object:
        """Open one PostgreSQL connection for aggregate read-only queries."""

        connection_kwargs = config.connection_kwargs()
        connection_kwargs.setdefault("options", "-c default_transaction_read_only=on")
        return psycopg.connect(**connection_kwargs)

    return connect


def _report_to_json(report: AggregateTicketEdaReport) -> str:
    """Serialize an aggregate EDA report to deterministic JSON."""

    if hasattr(report, "model_dump_json"):
        return report.model_dump_json(indent=2)
    return report.json(indent=2)


if __name__ == "__main__":
    sys.exit(main())
