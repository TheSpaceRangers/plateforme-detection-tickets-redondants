"""Schemas and typed structures used by backend services."""

from .tickets import IncomingSyntheticTicket, IncomingTicket, IngestionResult, StoredCleanTicket

__all__ = ["IncomingSyntheticTicket", "IncomingTicket", "IngestionResult", "StoredCleanTicket"]
