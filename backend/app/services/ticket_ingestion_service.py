"""Service orchestrating ticket extraction, privacy guardrails, and storage."""

from __future__ import annotations

from ml.src.preprocessing import AgentIdPolicy, assert_no_residual_pii, build_preprocessed_ticket_dataset

from backend.app.data.extractors.ticket_extractor import TicketExtractor
from backend.app.db.repositories.ticket_repository import TicketRepository
from backend.app.schemas.tickets import IngestionResult, StoredCleanTicket


class TicketIngestionService:
    """Service layer for ticket ingestion with pre-repository privacy controls."""

    def __init__(self, extractor: TicketExtractor, repository: TicketRepository) -> None:
        self._extractor = extractor
        self._repository = repository

    def ingest_synthetic_tickets(self, include_agent_pseudonym: bool = False) -> IngestionResult:
        """Run extraction, ML privacy guardrails, and sanitized storage in that order."""

        return self.ingest_tickets(include_agent_pseudonym=include_agent_pseudonym)

    def ingest_tickets(self, include_agent_pseudonym: bool = False) -> IngestionResult:
        """Run source-agnostic extraction, ML privacy guardrails, and sanitized storage."""

        incoming_tickets = tuple(self._extractor.extract())
        guarded_records = build_preprocessed_ticket_dataset(
            (ticket.to_guardrail_mapping() for ticket in incoming_tickets),
            agent_id_policy=AgentIdPolicy(include_pseudonymized=include_agent_pseudonym),
        )
        assert_no_residual_pii(
            guarded_records,
            fields=(
                "external_ticket_id",
                "summary",
                "details",
                "status",
                "priority",
                "category",
                "agent_id_pseudonym",
            ),
        )
        clean_tickets = tuple(StoredCleanTicket.from_guarded_mapping(record) for record in guarded_records)
        stored_count = self._repository.save_many(clean_tickets)
        return IngestionResult(
            extracted_count=len(incoming_tickets),
            stored_count=stored_count,
            status="completed",
        )
