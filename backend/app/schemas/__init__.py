"""Schemas and typed structures used by backend services."""

from .tickets import IncomingSyntheticTicket, IngestionResult, StoredCleanTicket

__all__ = ["IncomingSyntheticTicket", "IngestionResult", "StoredCleanTicket"]
