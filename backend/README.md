# Backend — socle minimal données

Ce dossier matérialise uniquement le socle backend/données de Sprint 1.
Aucune extraction HaloPSA réelle, aucun credential et aucune donnée métier ne sont inclus.

## Structure cible

```text
backend/app/
├── routers/          # Future FastAPI API boundaries
├── services/         # Business rules and orchestration
├── repositories/     # PostgreSQL access layer
└── db/               # Database schema and connection boundary
```

## Décisions de cadrage

- FastAPI reste la cible backend, mais aucun serveur applicatif n'est démarré à ce stade.
- PostgreSQL est la base cible et peut être vérifié localement; aucun schéma backend applicatif n'est encore présent dans `backend/app/db/schema.sql`.
- L'ingestion HaloPSA est cadrée en lecture seule dans `backend/docs/halopsa_ingestion_read_only.md`.
- Les contrôles pré-stockage tickets sont cadrés dans `backend/docs/pre_storage_privacy_controls.md` tant qu'aucun point d'intégration backend n'existe.
- Les futurs scripts Python devront utiliser Python 3.11+, `uv`, des type hints et des variables d'environnement.

## Données interdites dans Git

- credentials, tokens, `.env` réels;
- dumps SQL, exports CSV/JSONL/Parquet/XLSX;
- tickets réels, noms de clients réels, descriptions identifiables.
