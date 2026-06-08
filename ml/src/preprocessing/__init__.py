"""Preprocessing utilities for synthetic ticket datasets."""

from .pii import (
    PiiResidualError,
    PiiSanitizationResult,
    assert_no_residual_pii,
    detect_pii,
    sanitize_ticket_text_fields,
)
from .tickets import AgentIdPolicy, build_preprocessed_ticket_dataset

__all__ = [
    "AgentIdPolicy",
    "PiiResidualError",
    "PiiSanitizationResult",
    "assert_no_residual_pii",
    "build_preprocessed_ticket_dataset",
    "detect_pii",
    "sanitize_ticket_text_fields",
]
