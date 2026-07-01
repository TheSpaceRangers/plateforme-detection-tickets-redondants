"""Synthetic dry-run ingestion command with no network and no durable storage."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict

from backend.app.data.extractors.synthetic_ticket_extractor import SyntheticTicketExtractor
from backend.app.db.repositories.ticket_repository import InMemoryTicketRepository
from backend.app.schemas.tickets import IngestionResult
from backend.app.services.ticket_ingestion_service import TicketIngestionService


class SyntheticDryRunCommandError(RuntimeError):
    """Raised when the synthetic dry-run cannot complete safely."""


def run_synthetic_dry_run_ingestion() -> IngestionResult:
    """Run the backend ingestion pipeline on synthetic tickets without writes."""

    repository = InMemoryTicketRepository()
    service = TicketIngestionService(
        extractor=SyntheticTicketExtractor(),
        repository=repository,
    )
    result = service.ingest_synthetic_tickets(include_agent_pseudonym=False)
    if result.stored_count != len(repository.tickets):
        raise SyntheticDryRunCommandError("Synthetic dry-run counts are inconsistent")
    return result


def main() -> int:
    """Write a non-sensitive JSON dry-run summary to stdout."""

    try:
        result = run_synthetic_dry_run_ingestion()
    except (SyntheticDryRunCommandError, ValueError) as exc:
        print(json.dumps({"error": "synthetic_dry_run_blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
