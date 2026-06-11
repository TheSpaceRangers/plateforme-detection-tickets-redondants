"""Fail-closed PostgreSQL configuration for controlled ticket storage."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

POSTGRES_WRITE_ENABLE_KEY = "POSTGRES_ENABLE_WRITE"
POSTGRES_DSN_KEY = "POSTGRES_DSN"
POSTGRES_COMPONENT_KEYS: tuple[str, ...] = (
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)
TRUE_ENV_VALUES = frozenset(("1", "true", "yes", "on"))


class PostgresConfigurationError(RuntimeError):
    """Raised when PostgreSQL writes are not explicitly safe to initialize."""


@dataclass(frozen=True, slots=True)
class PostgresConnectionConfig:
    """Credential-safe PostgreSQL connection settings."""

    dsn: str | None = None
    host: str | None = None
    port: int | None = None
    dbname: str | None = None
    user: str | None = None
    password: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "PostgresConnectionConfig":
        """Build connection settings after explicit write activation."""

        if not is_postgres_write_enabled(env):
            raise PostgresConfigurationError("PostgreSQL ticket writes are not explicitly enabled")

        dsn = env.get(POSTGRES_DSN_KEY, "").strip()
        if dsn:
            return cls(dsn=dsn)

        missing_keys = tuple(key for key in POSTGRES_COMPONENT_KEYS if not env.get(key, "").strip())
        if missing_keys:
            raise PostgresConfigurationError(
                f"Incomplete PostgreSQL ticket repository configuration: {', '.join(missing_keys)}"
            )
        return cls(
            host=env["POSTGRES_HOST"].strip(),
            port=_parse_postgres_port(env["POSTGRES_PORT"]),
            dbname=env["POSTGRES_DB"].strip(),
            user=env["POSTGRES_USER"].strip(),
            password=env["POSTGRES_PASSWORD"],
        )

    def connection_kwargs(self) -> dict[str, Any]:
        """Return psycopg keyword arguments without logging secrets."""

        if self.dsn is not None:
            return {"conninfo": self.dsn}
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
        }


def is_postgres_write_enabled(env: Mapping[str, str]) -> bool:
    """Return whether runtime explicitly opted in to PostgreSQL writes."""

    return env.get(POSTGRES_WRITE_ENABLE_KEY, "").strip().lower() in TRUE_ENV_VALUES


def _parse_postgres_port(raw_port: str) -> int:
    """Parse PostgreSQL port without exposing the raw value."""

    try:
        port = int(raw_port)
    except ValueError as exc:
        raise PostgresConfigurationError("POSTGRES_PORT must be an integer") from exc
    if port <= 0:
        raise PostgresConfigurationError("POSTGRES_PORT must be strictly positive")
    return port
