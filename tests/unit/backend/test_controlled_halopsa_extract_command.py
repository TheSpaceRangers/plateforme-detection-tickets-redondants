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
    dotenv_module = importlib.import_module("dotenv")
    dotenv_loader = MagicMock(side_effect=AssertionError("controlled command import must not load dotenv"))
    original_open = builtins.open
    opened_paths: list[str] = []

    def guarded_open(file: object, *args: object, **kwargs: object) -> Any:
        path = Path(str(file))
        opened_paths.append(str(path))
        if path.name == ".env":
            raise AssertionError("controlled command import must not read .env")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(dotenv_module, "load_dotenv", dotenv_loader)
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
    dotenv_loader.assert_not_called()
    assert not any(Path(path).name == ".env" for path in opened_paths)


def test_load_local_dotenv_calls_injected_loader_with_provided_path_and_no_override(tmp_path: Path) -> None:
    # Arrange
    command = _command_module()
    dotenv_path = tmp_path / ".env"
    dotenv_loader = MagicMock(return_value=True)

    # Act
    loaded = command.load_local_dotenv(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)

    # Assert
    assert loaded is True
    dotenv_loader.assert_called_once_with(dotenv_path, override=False)


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


def test_build_config_from_env_keeps_requested_page_size_one() -> None:
    # Arrange
    command = _command_module()
    env = _valid_env(HALO_PAGE_SIZE="1")

    # Act
    config = command.build_config_from_env(env)

    # Assert
    assert config.page_size == 1


def test_build_config_from_env_uses_default_page_no_when_absent() -> None:
    # Arrange
    command = _command_module()
    env = _valid_env(HALO_PAGE_NO=None)

    # Act
    config = command.build_config_from_env(env)

    # Assert
    assert config.page_no == 1


@pytest.mark.parametrize(
    ("raw_page_no", "expected_message"),
    [
        ("0", "strictly positive"),
        ("-1", "strictly positive"),
        ("not-an-integer", "must be an integer"),
    ],
)
def test_build_config_from_env_fails_closed_for_unsafe_page_no(
    raw_page_no: str,
    expected_message: str,
) -> None:
    # Arrange
    command = _command_module()
    env = _valid_env(HALO_PAGE_NO=raw_page_no)

    # Act
    with pytest.raises(command.ControlledExtractionError, match=expected_message):
        command.build_config_from_env(env)

    # Assert
    assert env["HALO_PAGE_NO"] == raw_page_no


@pytest.mark.parametrize(
    ("raw_page_size", "expected_message"),
    [
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


def test_build_config_from_env_caps_page_size_above_safe_limit_to_five() -> None:
    # Arrange
    command = _command_module()
    env = _valid_env(HALO_PAGE_SIZE="25")

    # Act
    config = command.build_config_from_env(env)

    # Assert
    assert config.page_size == command.MAX_PAGE_SIZE
    assert env["HALO_PAGE_SIZE"] == "25"


def test_run_controlled_halopsa_extract_blocks_when_transport_is_absent() -> None:
    # Arrange
    command = _command_module()
    env = _valid_env()

    # Act
    with pytest.raises(
        command.ControlledExtractionError,
        match="HaloPSA network transport is not explicitly configured",
    ):
        command.run_controlled_halopsa_extract(env=env)

    # Assert
    assert command._is_network_enabled(env) is False


@pytest.mark.parametrize("postgres_write_value", [None, "", "false", "0", "no", "unexpected"])
def test_run_controlled_halopsa_extract_blocks_network_enabled_without_postgres_write(
    monkeypatch: pytest.MonkeyPatch,
    postgres_write_value: str | None,
) -> None:
    # Arrange
    command = _command_module()
    fake_transport = object()
    transport_factory = MagicMock(return_value=fake_transport)
    client_factory = MagicMock(side_effect=AssertionError("HaloPSA client must not be created before repository approval"))
    ingestion_service_factory = MagicMock(side_effect=AssertionError("ingestion service must not be built before repository approval"))
    monkeypatch.setattr(command, "HaloPsaHttpTransport", transport_factory)
    monkeypatch.setattr(command, "HaloPsaTicketClient", client_factory)
    monkeypatch.setattr(command, "TicketIngestionService", ingestion_service_factory)
    env = _valid_env(HALOPSA_ENABLE_NETWORK="true", POSTGRES_ENABLE_WRITE=postgres_write_value)

    # Act
    with pytest.raises(command.ControlledExtractionError, match="PostgreSQL ticket writes are not explicitly enabled"):
        command.run_controlled_halopsa_extract(env=env)

    # Assert
    transport_factory.assert_called_once_with()
    client_factory.assert_not_called()
    ingestion_service_factory.assert_not_called()


@pytest.mark.parametrize("enabled_value", ["true", "TRUE", "1", "yes", "on"])
def test_explicit_network_transport_is_built_only_for_authorized_enable_values(
    monkeypatch: pytest.MonkeyPatch,
    enabled_value: str,
) -> None:
    # Arrange
    command = _command_module()
    transport_factory = MagicMock(return_value="synthetic-transport")
    monkeypatch.setattr(command, "HaloPsaHttpTransport", transport_factory)
    env = _valid_env(HALOPSA_ENABLE_NETWORK=enabled_value)

    # Act
    transport = command._build_explicit_network_transport(env)

    # Assert
    assert transport == "synthetic-transport"
    transport_factory.assert_called_once_with()


@pytest.mark.parametrize("disabled_value", [None, "", "false", "0", "no", "unexpected"])
def test_explicit_network_transport_is_not_built_without_authorized_enable_value(
    monkeypatch: pytest.MonkeyPatch,
    disabled_value: str | None,
) -> None:
    # Arrange
    command = _command_module()
    transport_factory = MagicMock(side_effect=AssertionError("real transport must not be built"))
    monkeypatch.setattr(command, "HaloPsaHttpTransport", transport_factory)
    env = _valid_env(HALOPSA_ENABLE_NETWORK=disabled_value)

    # Act
    transport = command._build_explicit_network_transport(env)

    # Assert
    assert transport is None
    transport_factory.assert_not_called()


def test_injected_real_transport_is_rejected_when_network_is_not_enabled() -> None:
    # Arrange
    command = _command_module()
    transport = command.HaloPsaHttpTransport()
    ingestion_service = MagicMock()
    env = _valid_env(HALOPSA_ENABLE_NETWORK="false")

    # Act
    with pytest.raises(command.ControlledExtractionError, match="not explicitly enabled"):
        command.run_controlled_halopsa_extract(env=env, transport=transport, ingestion_service=ingestion_service)

    # Assert
    ingestion_service.ingest_tickets.assert_not_called()


def test_main_with_valid_env_blocks_without_implicit_transport_or_repository(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    command = _command_module()
    dotenv_loader = MagicMock(return_value=True)
    dotenv_path = tmp_path / ".env"
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
    exit_code = command.main(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)

    # Assert
    assert exit_code == 2
    dotenv_loader.assert_called_once_with(dotenv_path, override=False)
    command.HaloPsaTicketClient.assert_not_called()


def test_main_calls_injected_dotenv_loader_before_mocked_extraction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    command = _command_module()
    dotenv_path = tmp_path / ".env"
    call_order: list[str] = []

    def dotenv_loader(path: str | Path, *, override: bool = False) -> bool:
        call_order.append("dotenv")
        assert path == dotenv_path
        assert override is False
        return True

    def run_controlled_halopsa_extract(**kwargs: object) -> command.ControlledExtractionResult:
        call_order.append("extract")
        assert kwargs["env"] is command.os.environ
        return command.ControlledExtractionResult(extracted_count=0, stored_count=0, status="mocked")

    monkeypatch.setattr(command, "run_controlled_halopsa_extract", run_controlled_halopsa_extract)

    # Act
    exit_code = command.main(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)

    # Assert
    assert exit_code == 0
    assert call_order == ["dotenv", "extract"]


def test_main_fails_closed_when_dotenv_not_loaded_and_required_env_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    command = _command_module()
    dotenv_path = tmp_path / "missing.env"
    dotenv_loader = MagicMock(return_value=False)
    for key in command.REQUIRED_ENV_KEYS + ("HALO_PAGE_SIZE",):
        monkeypatch.delenv(key, raising=False)

    # Act
    exit_code = command.main(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)

    # Assert
    assert exit_code == 2
    dotenv_loader.assert_called_once_with(dotenv_path, override=False)


def test_main_fails_closed_when_required_env_is_missing_after_mocked_dotenv_load(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Arrange
    command = _command_module()
    dotenv_path = tmp_path / ".env"
    dotenv_loader = MagicMock(return_value=True)
    missing_key = "HALOPSA_CLIENT_SECRET"
    for key in command.REQUIRED_ENV_KEYS + ("HALO_PAGE_SIZE",):
        monkeypatch.delenv(key, raising=False)
    for key, value in _valid_env(**{missing_key: None}).items():
        monkeypatch.setenv(key, value)

    # Act
    exit_code = command.main(dotenv_path=dotenv_path, dotenv_loader=dotenv_loader)

    # Assert
    assert exit_code == 2
    dotenv_loader.assert_called_once_with(dotenv_path, override=False)


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
