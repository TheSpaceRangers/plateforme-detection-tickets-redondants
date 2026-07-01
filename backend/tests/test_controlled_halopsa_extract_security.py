"""Security regression tests for controlled HaloPSA extraction wiring."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.app.data.commands import controlled_halopsa_extract as command
from backend.app.schemas.tickets import IngestionResult


def _valid_env(**overrides: str | None) -> dict[str, str]:
    """Return a synthetic environment mapping without real endpoints or secrets."""

    env = {
        "SYNAPPSE_AGENT_ID_HMAC_SECRET": "synthetic-hmac-value",
        "HALOPSA_BASE_URL": "https://halopsa.invalid.test",
        "HALOPSA_CLIENT_ID": "synthetic-client-id",
        "HALOPSA_CLIENT_SECRET": "synthetic-client-secret",
        "HALOPSA_TENANT": "synthetic-tenant",
        "HALO_SCOPE": "synthetic-scope",
        "HALO_PAGE_SIZE": "1",
    }
    for key, value in overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def test_real_network_wiring_requires_compliance_go_before_transport_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Block real extraction even when network/write flags are set without compliance GO."""

    transport_factory = MagicMock(side_effect=AssertionError("transport must not be created"))
    monkeypatch.setattr(command, "HaloPsaHttpTransport", transport_factory)

    with pytest.raises(command.ControlledExtractionError, match="Compliance GO"):
        command.run_controlled_halopsa_extract(
            env=_valid_env(HALOPSA_ENABLE_NETWORK="true", POSTGRES_ENABLE_WRITE="true")
        )

    transport_factory.assert_not_called()


def test_page_size_and_total_ticket_caps_fail_closed() -> None:
    """Reject arbitrary extraction sizes above documented backend safety caps."""

    with pytest.raises(command.ControlledExtractionError, match="HALO_PAGE_SIZE"):
        command.build_config_from_env(_valid_env(HALO_PAGE_SIZE="51"))

    with pytest.raises(command.ControlledExtractionError, match="HALOPSA_MAX_TOTAL_TICKETS"):
        command.build_config_from_env(_valid_env(HALOPSA_MAX_TOTAL_TICKETS="51"))


def test_agent_pseudonym_is_disabled_by_default() -> None:
    """Do not include agent pseudonym unless explicitly opted in after compliance GO."""

    ingestion_service = MagicMock()
    ingestion_service.ingest_tickets.return_value = IngestionResult(
        extracted_count=1,
        stored_count=1,
        ignored_count=0,
        status="completed",
    )

    command.run_controlled_halopsa_extract(
        env=_valid_env(SYNAPPSE_AGENT_ID_HMAC_SECRET=None),
        ingestion_service=ingestion_service,
    )

    ingestion_service.ingest_tickets.assert_called_once_with(include_agent_pseudonym=False)
