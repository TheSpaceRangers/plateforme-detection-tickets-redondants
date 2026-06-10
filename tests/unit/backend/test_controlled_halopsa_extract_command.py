"""Unit tests for the controlled HaloPSA extraction command boundary."""

from __future__ import annotations

import builtins
import importlib
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.app.schemas.tickets import IngestionResult


MODULE_NAME = "backend.app.data.commands.controlled_halopsa_extract"


def _valid_env(**overrides: str | None) -> dict[str, str]:
    values = {
        "SYNAPPSE_AGENT_ID_HMAC_SECRET": "synthetic-hmac-value",
        "HALOPSA_BASE_URL": "https://halopsa.invalid.test",
        "HALOPSA_CLIENT_ID": "synthetic-client-id",
        "HALOPSA_CLIENT_SECRET": "synthetic-client-secret",
        "HALOPSA_TENANT": "synthetic-tenant",
        "HALO_SCOPE": "synthetic-scope",
        "HALO_PAGE_SIZE": "2",
    }
    for key, value in overrides.items():
        if value is None:
            values.pop(key, None)
        else:
            values[key] = value
    return values


def _command_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def test_controlled_halopsa_extract_import_is_safe_without_dotenv_network_or_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    original_open = builtins.open
    opened_paths: list[str] = []

    def guarded_open(file: object, *args: object, **kwargs: object) -> Any:
        path = Path(str(file))
        opened_paths.append(str(path))
        if path.name == ".env":
            raise AssertionError("controlled command import must not read .env")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    sys.modules.pop(MODULE_NAME, None)

    # Act
    module = importlib.import_module(MODULE_NAME)

    # Assert
    assert module.REQUIRED_ENV_KEYS == (
        "SYNAPPSE_AGENT_ID_HMAC_SECRET",
        "HALOPSA_BASE_URL",
        "HALOPSA_CLIENT_ID",
        "HALOPSA_CLIENT_SECRET",
        "HALOPSA_TENANT",
        "HALO_SCOPE",
    )
    assert not any(Path(path).name == ".env" for path in opened_paths)


@pytest.mark.parametrize(
    ("missing_key", "missing_value"),
    [
        ("SYNAPPSE_AGENT_ID_HMAC_SECRET", None),
        ("HALOPSA_BASE_URL", " "),
        ("HALOPSA_CLIENT_ID", ""),
        ("HALOPSA_CLIENT_SECRET", None),
        ("HALOPSA_TENANT", "\t"),
        ("HALO_SCOPE", None),
    ],
)
def test_run_controlled_halopsa_extract_blocks_missing_required_env_before_ingestion(
    missing_key: str,
    missing_value: str | None,
) -> None:
    # Arrange
    command = _command_module()
    ingestion_service = MagicMock()
    env = _valid_env(**{missing_key: missing_value})

    # Act
    with pytest.raises(command.ControlledExtractionError, match=missing_key):
        command.run_controlled_halopsa_extract(env=env, ingestion_service=ingestion_service)

    # Assert
    ingestion_service.ingest_tickets.assert_not_called()


def test_build_config_from_env_uses_safe_default_page_size_when_absent() -> None:
    # Arrange
    command = _command_module()
    env = _valid_env(HALO_PAGE_SIZE=None)

    # Act
    config = command.build_config_from_env(env)

    # Assert
    assert config.page_size == 1


@pytest.mark.parametrize(
    ("raw_page_size", "expected_message"),
    [
        ("6", "must not exceed 5"),
        ("0", "strictly positive"),
        ("-1", "strictly positive"),
        ("not-an-integer", "must be an integer"),
    ],
)
def test_build_config_from_env_fails_closed_for_unsafe_page_size(
    raw_page_size: str,
    expected_message: str,
) -> None:
    # Arrange
    command = _command_module()
    env = _valid_env(HALO_PAGE_SIZE=raw_page_size)

    # Act
    with pytest.raises(command.ControlledExtractionError, match=expected_message):
        command.build_config_from_env(env)

    # Assert
    assert env["HALO_PAGE_SIZE"] == raw_page_size


def test_main_with_valid_env_blocks_without_implicit_transport_or_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    command = _command_module()
    for key in command.REQUIRED_ENV_KEYS + ("HALO_PAGE_SIZE",):
        monkeypatch.delenv(key, raising=False)
    for key, value in _valid_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        command,
        "HaloPsaTicketClient",
        MagicMock(side_effect=AssertionError("network client must not be created implicitly")),
    )

    # Act
    exit_code = command.main()

    # Assert
    assert exit_code == 2
    command.HaloPsaTicketClient.assert_not_called()


def test_run_controlled_halopsa_extract_nominal_mocked_ingestion_returns_counts_only() -> None:
    # Arrange
    command = _command_module()
    ingestion_service = MagicMock()
    ingestion_service.ingest_tickets.return_value = IngestionResult(
        extracted_count=3,
        stored_count=2,
        status="completed",
    )

    # Act
    result = command.run_controlled_halopsa_extract(env=_valid_env(), ingestion_service=ingestion_service)

    # Assert
    ingestion_service.ingest_tickets.assert_called_once_with(include_agent_pseudonym=True)
    assert result == command.ControlledExtractionResult(extracted_count=3, stored_count=2, status="completed")
    assert tuple(field.name for field in fields(result)) == ("extracted_count", "stored_count", "status")


def test_run_controlled_halopsa_extract_logs_no_env_values_or_ticket_content(caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    command = _command_module()
    env = _valid_env()
    ingestion_service = MagicMock()
    ingestion_service.ingest_tickets.return_value = IngestionResult(
        extracted_count=1,
        stored_count=1,
        status="completed",
    )
    forbidden_log_fragments = set(env.values()) | {
        "Synthetic laptop cannot reach the service portal",
        "Synthetic diagnostic reports a controlled routing error.",
        "synthetic-agent-001",
    }

    # Act
    with caplog.at_level("INFO", logger=command.__name__):
        result = command.run_controlled_halopsa_extract(env=env, ingestion_service=ingestion_service)

    # Assert
    assert result.status == "completed"
    rendered_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "extracted_count=1" in rendered_logs
    assert not any(fragment in rendered_logs for fragment in forbidden_log_fragments)
