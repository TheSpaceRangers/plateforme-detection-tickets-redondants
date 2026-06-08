# Contrôles pré-stockage tickets — Sprint 1

## État observé

Le backend ne contient actuellement aucun point d'entrée applicatif FastAPI, service métier, repository PostgreSQL, script d'ingestion ou stockage dataset.

Les garde-fous HMAC/PII existent côté ML, mais aucun branchement backend `extraction → contrôles → stockage` n'existe encore.

## Décision Sprint 1

Aucun code de pseudonymisation ou de contrôle PII n'est ajouté côté backend tant qu'aucun flux de stockage ticket/dataset n'existe.

Pourquoi : dupliquer le preprocessing ML sans point d'intégration backend créerait une logique morte et un risque de divergence.

## Règles à appliquer au futur point d'intégration backend

- Appliquer une allowlist stricte avant tout stockage ; tout champ hors allowlist doit être rejeté ou ignoré avant repository.
- Exécuter les garde-fous de minimisation, pseudonymisation éventuelle et contrôle PII dans le Service Layer avant appel au repository.
- Refuser tout stockage si une PII résiduelle est détectée après nettoyage.
- Exclure `agent_id` par défaut des données stockées et des datasets.
- N'autoriser un pseudonyme `agent_id` que via décision explicite, avec HMAC-SHA-256 et secret obligatoire fourni par `SYNAPPSE_AGENT_ID_HMAC_SECRET`.
- Échouer en mode fermé si `SYNAPPSE_AGENT_ID_HMAC_SECRET` est absent ou vide alors qu'une pseudonymisation est requise.
- Isoler la logique métier dans `backend/app/services/` et les accès PostgreSQL dans `backend/app/db/repositories/`.
- Ne jamais stocker de payload HaloPSA brut durablement.
- Ne jamais logger contenu ticket, PII, `agent_id` brut, secret HMAC, token, header HTTP ou payload brut.
- Persister uniquement des données nettoyées et, si décision explicite, pseudonymisées.

## Conditions Go/No-Go

- **Go** : allowlist validée, contrôle PII bloquant, fail-closed HMAC spécifié, Service Layer avant Repository Pattern, logs minimisés et absence de stockage JSON brut.
- **No-Go** : extraction HaloPSA réelle requise, secret HMAC absent lors d'une pseudonymisation, PII résiduelle détectée, champ hors allowlist à persister ou risque de log sensible.
