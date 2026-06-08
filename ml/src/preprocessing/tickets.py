"""Dataset guardrails for synthetic pre-extraction ticket preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .pii import assert_no_residual_pii, sanitize_ticket_text_fields
from .pseudonymization import DEFAULT_SECRET_ENV_VAR, pseudonymize_with_hmac_sha256


@dataclass(frozen=True)
class AgentIdPolicy:
    """Controls whether agent_id is excluded or explicitly pseudonymized."""

    include_pseudonymized: bool = False
    secret_env_var: str = DEFAULT_SECRET_ENV_VAR


def build_preprocessed_ticket_dataset(
    tickets: Iterable[Mapping[str, object]],
    agent_id_policy: AgentIdPolicy | None = None,
) -> list[dict[str, object]]:
    """Build a guarded synthetic dataset from ticket-like mappings."""

    policy = agent_id_policy or AgentIdPolicy()
    preprocessed_records: list[dict[str, object]] = []

    for ticket in tickets:
        sanitized_ticket = sanitize_ticket_text_fields(ticket)
        sanitized_ticket.pop("agent_id", None)

        if policy.include_pseudonymized and ticket.get("agent_id") is not None:
            sanitized_ticket["agent_id_pseudonym"] = pseudonymize_with_hmac_sha256(
                str(ticket["agent_id"]),
                secret_env_var=policy.secret_env_var,
            )

        preprocessed_records.append(sanitized_ticket)

    assert_no_residual_pii(preprocessed_records)
    return preprocessed_records
