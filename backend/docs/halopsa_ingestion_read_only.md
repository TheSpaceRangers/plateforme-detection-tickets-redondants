# Contrat backend d'ingestion HaloPSA en lecture seule — Sprint 1

## État actuel observé

- Un contrat d'extraction source-agnostique existe côté `backend/app/data/extractors/ticket_extractor.py`.
- Un adaptateur HaloPSA préparatoire existe, mais son transport par défaut bloque toute exécution réseau.
- Aucun endpoint, service, repository ou script backend ne déclenche d'appel HaloPSA.
- Aucun stockage applicatif de payload brut HaloPSA n'est implémenté côté backend.
- Le secret runtime attendu pour une pseudonymisation HMAC d'`agent_id` est `SYNAPPSE_AGENT_ID_HMAC_SECRET`; il n'est pas requis tant qu'aucune pseudonymisation opérationnelle n'est exécutée.

## Décision Sprint 1

Cette étape formalise uniquement le contrat d'intégration futur `extraction → garde-fous PII/HMAC → stockage`.

Extraction HaloPSA réelle : **NO-GO**.

Pourquoi : sans service d'intégration, repository et validation Go sécurité, une extraction réelle créerait un risque de fuite ou de stockage non maîtrisé.

## Périmètre explicitement interdit à ce stade

- Aucun appel API HaloPSA.
- Aucune donnée réelle.
- Aucun payload JSON brut conservé durablement.
- Aucun export CSV, JSONL, Parquet, XLSX ou dump SQL.
- Aucun log contenant contenu de ticket, PII, identifiant personnel brut, secret, header HTTP ou token.

## Contrat cible d'intégration backend

Le futur flux backend devra respecter strictement l'ordre suivant :

1. **Boundary d'extraction contrôlée** : récupérer uniquement les champs autorisés par allowlist explicite, sans persistance de payload brut.
2. **Service Layer** : orchestrer normalisation, minimisation, contrôles PII et décision éventuelle de pseudonymisation.
3. **Garde-fous pré-repository** : bloquer toute donnée non nettoyée avant appel au repository.
4. **Repository Pattern** : persister uniquement des champs nettoyés et/ou pseudonymisés dans PostgreSQL.

La logique métier restera dans `backend/app/services/` et l'accès PostgreSQL dans `backend/app/db/repositories/`.

## Préparation technique implémentée

- `TicketExtractor` définit le protocole découplé attendu par `TicketIngestionService`.
- `HaloPsaExtractorConfig` est injecté par l'appelant et valide en fail-closed `base_url`, `client_id`, `client_secret`, `tenant` et `page_size`, sans charger de `.env`.
- `HaloPsaTicketClient` ne connaît qu'un `HaloPsaTransport` injecté ; sans transport explicite, `NoopHaloPsaTransport` lève une erreur et ne fait aucun réseau.
- `HaloPsaTicketExtractor` transforme uniquement les champs allowlistés vers `IncomingTicket` : `external_ticket_id`, `summary`, `details`, `status`, `priority`, `category`, `agent_id`.
- Le statut accepte les variantes provider minimisées `status`, `status_id`, `statusid`, `ticketstatus` et l'objet `status` via `name` puis `id`; si aucune valeur exploitable n'est présente, le statut interne devient `unknown` sans stockage de payload brut.
- Les champs bruts hors allowlist ne sont pas transmis au service d'ingestion ni aux repositories.

Intégration future prévue : instancier `TicketIngestionService(extractor=HaloPsaTicketExtractor(client), repository=...)` puis appeler `ingest_tickets()`. Le transport réel devra être fourni par composition et validé séparément par sécurité/conformité.

## Allowlist pré-stockage

Le backend devra définir une allowlist stricte avant stockage.

- Tout champ absent de l'allowlist est rejeté ou ignoré avant repository.
- Les champs de contenu ticket ne sont stockables qu'après nettoyage et contrôle PII bloquant.
- `agent_id` est exclu par défaut des données stockées et des datasets.
- `agent_id` ne peut être pseudonymisé que sur décision explicite documentée.

## Garde-fous PII/HMAC avant repository

- Le contrôle PII résiduel est bloquant : toute PII détectée après nettoyage empêche la persistance.
- Si une pseudonymisation HMAC est requise, le backend doit échouer en mode fermé lorsque `SYNAPPSE_AGENT_ID_HMAC_SECRET` est absent ou vide.
- Le secret HMAC ne doit jamais être journalisé, retourné par API, stocké en base ou inclus dans un export.
- Le stockage est autorisé uniquement pour des données nettoyées et, si nécessaire, pseudonymisées.

## Journalisation attendue

Les logs futurs doivent rester techniques et minimisés :

- identifiant interne de traitement ;
- statut de validation ;
- compteurs agrégés ;
- durée d'exécution ;
- code d'erreur non sensible.

Les logs ne doivent jamais contenir contenu de ticket, payload HaloPSA, PII, `agent_id` brut, secret, token ou headers HTTP.

## Conditions Go/No-Go avant implémentation opérationnelle

### Go uniquement si

- le contrat d'allowlist est validé ;
- les garde-fous PII sont branchés avant tout repository ;
- le comportement fail-closed sur `SYNAPPSE_AGENT_ID_HMAC_SECRET` est spécifié et testé lorsque la pseudonymisation est activée ;
- les repositories ne reçoivent que des données nettoyées/pseudonymisées ;
- la politique de logs est validée ;
- aucun stockage durable de JSON brut n'est possible ;
- une revue sécurité/conformité autorise explicitement le passage hors documentation.

### No-Go si

- une extraction réelle HaloPSA est nécessaire pour tester le flux ;
- le secret HMAC manque alors qu'une pseudonymisation est requise ;
- un contrôle PII résiduel détecte une donnée personnelle après nettoyage ;
- un champ hors allowlist doit être persisté ;
- un log ou export risque de contenir ticket, PII ou secret.
