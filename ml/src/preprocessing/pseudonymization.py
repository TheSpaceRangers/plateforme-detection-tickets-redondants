"""Fail-closed HMAC-SHA-256 pseudonymization helpers."""

from __future__ import annotations

import hashlib
import hmac
import os


DEFAULT_SECRET_ENV_VAR = "SYNAPPSE_AGENT_ID_HMAC_SECRET"


class MissingPseudonymizationSecretError(RuntimeError):
    """Raised when pseudonymization is requested without a usable secret."""


def pseudonymize_with_hmac_sha256(value: str, secret_env_var: str = DEFAULT_SECRET_ENV_VAR) -> str:
    """Pseudonymize a value with HMAC-SHA-256 using a mandatory environment secret."""

    secret = os.environ.get(secret_env_var)
    if not secret:
        raise MissingPseudonymizationSecretError(
            f"Missing required environment variable for HMAC-SHA-256 pseudonymization: {secret_env_var}"
        )
    digest = hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"hmac_sha256:{digest}"
