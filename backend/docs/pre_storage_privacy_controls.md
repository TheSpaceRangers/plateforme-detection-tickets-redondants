# Contrôles pré-stockage tickets — Sprint 1

## État observé

Le backend ne contient actuellement aucun point d'entrée applicatif FastAPI, service métier, repository PostgreSQL, script d'ingestion ou stockage dataset.

## Décision Sprint 1

Aucun code de pseudonymisation ou de contrôle PII n'est ajouté côté backend tant qu'aucun flux de stockage ticket/dataset n'existe.

Pourquoi : dupliquer le preprocessing ML sans point d'intégration backend créerait une logique morte et un risque de divergence.

## Règles à appliquer au futur point d'intégration backend

- Refuser tout stockage si une PII résiduelle est détectée après nettoyage.
- Exclure `agent_id` par défaut des données stockées et des datasets.
- N'autoriser un pseudonyme `agent_id` que via décision explicite, avec HMAC-SHA-256 et secret obligatoire fourni par variable d'environnement.
- Échouer en mode fermé si le secret HMAC est absent ou vide.
- Isoler la logique métier dans `backend/app/services/` et les accès PostgreSQL dans `backend/app/db/repositories/`.
- Ne jamais stocker de payload HaloPSA brut durablement.
