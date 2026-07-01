"""Non-sensitive synthetic ticket-like records for dry-run preparation only."""

from __future__ import annotations


def synthetic_ticket_source_records() -> list[dict[str, object]]:
    """Return synthetic records that exercise scope, PII, duplicates, and missingness checks."""

    return [
        {
            "summary": "Connexion applicative impossible depuis le portail interne",
            "details": "Message d erreur generique apres authentification standard",
            "ticket_created_at": "2025-01-15T09:30:00+00:00",
        },
        {
            "summary": "Connexion applicative impossible depuis le portail interne",
            "details": "Message d erreur generique apres authentification standard",
            "ticket_created_at": "2025-01-15T09:30:00+00:00",
        },
        {
            "summary": "Lenteur lors de la synchronisation documentaire",
            "details": "Plusieurs utilisateurs signalent un delai sur une operation recurrente",
            "ticket_created_at": "2025-02-03",
        },
        {
            "summary": "Notification synthetique envoyee a synthetic.user@example.test",
            "details": "Scenario fictif avec rappel 06 00 00 00 00 et page https://example.test/help",
            "ticket_created_at": "2025-03-18",
        },
        {
            "summary": "",
            "details": "Cas synthetique exploitable avec resume volontairement absent",
            "ticket_created_at": "2025-04-22",
        },
        {
            "summary": "Archive historique hors scope",
            "details": "Cas synthetique exclu par date de cadrage",
            "ticket_created_at": "2024-12-31",
        },
        {
            "summary": "Date absente exclue",
            "details": "Cas synthetique sans date de creation exploitable",
            "ticket_created_at": None,
        },
    ]
