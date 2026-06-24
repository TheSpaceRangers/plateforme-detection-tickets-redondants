"""Typed ticket structures for ingestion and clean storage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IncomingTicket:
    """Allowlisted incoming ticket fields before privacy guardrails."""

    external_ticket_id: str
    summary: str
    details: str
    status: str
    priority: str | None = None
    category: str | None = None
    agent_id: str | None = None

    def to_guardrail_mapping(self) -> dict[str, object]:
        """Return only fields expected by existing ML privacy guardrails."""

        mapping: dict[str, object] = {
            "external_ticket_id": self.external_ticket_id,
            "summary": self.summary,
            "details": self.details,
            "status": self.status,
            "priority": self.priority,
            "category": self.category,
        }
        if self.agent_id is not None:
            mapping["agent_id"] = self.agent_id
        return mapping


IncomingSyntheticTicket = IncomingTicket


@dataclass(frozen=True, slots=True)
class StoredCleanTicket:
    """Sanitized ticket shape accepted by repositories; raw JSON and agent_id are absent."""

    external_ticket_id: str
    summary: str
    details: str
    status: str
    priority: str | None = None
    category: str | None = None
    agent_id_pseudonym: str | None = None

    @classmethod
    def from_guarded_mapping(cls, record: dict[str, object]) -> "StoredCleanTicket":
        """Create a storage record from guardrail output while rejecting forbidden fields."""

        forbidden_fields = {"agent_id", "raw_json", "raw_payload", "payload", "halopsa_payload"}
        present_forbidden_fields = forbidden_fields.intersection(record)
        if present_forbidden_fields:
            raise ValueError("Forbidden storage fields detected before repository call")

        return cls(
            external_ticket_id=str(record["external_ticket_id"]),
            summary=str(record["summary"]),
            details=str(record["details"]),
            status=str(record["status"]),
            priority=str(record["priority"]) if record.get("priority") is not None else None,
            category=str(record["category"]) if record.get("category") is not None else None,
            agent_id_pseudonym=str(record["agent_id_pseudonym"])
            if record.get("agent_id_pseudonym") is not None
            else None,
        )


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Aggregated non-sensitive ingestion result."""

    extracted_count: int
    stored_count: int
    status: str
    ignored_count: int = 0
