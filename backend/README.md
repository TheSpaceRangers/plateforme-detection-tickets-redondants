# Backend — socle données exploitable

Ce dossier matérialise le socle backend/données de Sprint 2.
Aucune extraction HaloPSA réelle, aucun credential et aucune donnée métier ne sont inclus.

## Structure cible

```text
backend/app/
├── routers/          # Future FastAPI API boundaries
├── services/         # Business rules and orchestration
├── data/             # Controlled extractors and dry-run commands
└── db/               # PostgreSQL schema, config and repositories
```

## Décisions de cadrage

- FastAPI reste la cible backend, mais aucun serveur applicatif n'est démarré à ce stade.
- PostgreSQL est la seule base cible backend; SQLite n'est pas une cible de stockage.
- Le schéma local est `backend/app/db/schema.sql` et stocke uniquement `clean_tickets`, sans JSON brut ni payload provider.
- L'ingestion HaloPSA contrôlée est cadrée dans `backend/docs/halopsa_ingestion_read_only.md`.
- Les contrôles pré-stockage tickets sont cadrés dans `backend/docs/pre_storage_privacy_controls.md` et appliqués par `TicketIngestionService` avant repository.
- `HALOPSA_BASE_URL` doit rester vide ou utiliser un placeholder non sensible (`https://<tenant>.halopsa.example`) tant qu'un Go conformité n'est pas accordé.
- Aucune extraction réelle, aucun appel réseau HaloPSA et aucune écriture PostgreSQL de tickets réels ne sont autorisés sans `SYNAPPSE_COMPLIANCE_GO_REAL_EXTRACTION=true` en plus des flags techniques `HALOPSA_ENABLE_NETWORK=true` et `POSTGRES_ENABLE_WRITE=true`.
- Le flux contrôlé borne strictement l'extraction à `HALOPSA_MAX_PAGE_SIZE<=50` et `HALOPSA_MAX_TOTAL_TICKETS<=50`; `HALO_PAGE_SIZE` ne peut jamais dépasser ces plafonds.
- `SYNAPPSE_INCLUDE_AGENT_PSEUDONYM=false` par défaut; l'agent pseudonymisé reste exclu sauf opt-in explicite après Go conformité.
- `external_ticket_id` est conservé uniquement comme identifiant provider indirect minimisé côté backend; il est interdit dans tout export ML.
- Les futurs scripts Python devront utiliser Python 3.11+, `uv`, des type hints et des variables d'environnement.

## Commandes locales sûres

- Dry-run synthétique, sans réseau et sans écriture durable : `python -m backend.app.data.commands.synthetic_dry_run_ingestion`
- Extraction HaloPSA contrôlée : `python -m backend.app.data.commands.controlled_halopsa_extract` échoue fermé par défaut sans Go explicite.
- EDA agrégée PostgreSQL, sans texte brut en sortie : `python -m backend.app.data.commands.aggregate_ticket_eda`

## Données interdites dans Git

- credentials, tokens, `.env` réels;
- dumps SQL, exports CSV/JSONL/Parquet/XLSX;
- tickets réels, noms de clients réels, descriptions identifiables.
