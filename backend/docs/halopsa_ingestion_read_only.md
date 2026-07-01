# Contrat backend d'ingestion HaloPSA contrôlée — Sprint 2

## État actuel observé

- Un contrat d'extraction source-agnostique existe côté `backend/app/data/extractors/ticket_extractor.py`.
- Un adaptateur HaloPSA préparatoire existe, mais son transport par défaut bloque toute exécution réseau.
- Aucun endpoint, service, repository ou script backend ne déclenche d'appel HaloPSA.
- Aucun stockage applicatif de payload brut HaloPSA n'est implémenté côté backend.
- Le secret runtime attendu pour une pseudonymisation HMAC d'`agent_id` est `SYNAPPSE_AGENT_ID_HMAC_SECRET`; il n'est pas requis tant qu'aucune pseudonymisation opérationnelle n'est exécutée.

## Décision Sprint 2

Cette étape formalise uniquement le contrat d'intégration futur `extraction → garde-fous PII/HMAC → stockage`.

Extraction HaloPSA réelle par défaut : **NO-GO**.

Le comportement attendu sans Go conformité explicite est le mode dry-run/synthétique :

- `python -m backend.app.data.commands.synthetic_dry_run_ingestion` exécute le pipeline sur tickets synthétiques uniquement ;
- `python -m backend.app.data.commands.controlled_halopsa_extract` valide la configuration puis échoue fermé tant que `SYNAPPSE_COMPLIANCE_GO_REAL_EXTRACTION=true` n'est pas positionné en plus de `HALOPSA_ENABLE_NETWORK=true`, `POSTGRES_ENABLE_WRITE=true`, un transport explicite et PostgreSQL approuvés ;
- aucune commande ne doit être lancée avec données réelles HaloPSA avant Go sécurité/conformité.

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
- `HaloPsaExtractorConfig` est injecté par l'appelant et valide en fail-closed `base_url`, `client_id`, `client_secret`, `tenant`, `page_size` et `max_total_tickets`, sans charger de `.env`.
- Le transport tickets construit une query paginée documentée avec `pageinate=true`, `page_size` issu de `HALO_PAGE_SIZE` et `page_no` issu de `HALO_PAGE_NO` ou `1` par défaut. `HALO_PAGE_SIZE` est plafonné par `HALOPSA_MAX_PAGE_SIZE` et par le hard cap backend `50`; `HALOPSA_MAX_TOTAL_TICKETS` est plafonné à `50` et le transport tronque toute réponse au-delà de ce volume.
- Le transport réel, désactivé par défaut, utilise OAuth client credentials sur `HALOPSA_TOKEN_PATH`, puis lit `HALOPSA_TICKETS_PATH`; ces endpoints sont fournis par variables d'environnement et ne contiennent aucun secret dans Git.
- Les appels HTTP ont un timeout (`HALOPSA_REQUEST_TIMEOUT_SECONDS`), des retries bornés (`HALOPSA_MAX_RETRIES`) et un throttling local (`HALOPSA_RATE_LIMIT_PER_MINUTE`).
- `HaloPsaTicketClient` ne connaît qu'un `HaloPsaTransport` injecté ; sans transport explicite, `NoopHaloPsaTransport` lève une erreur et ne fait aucun réseau.
- `HaloPsaTicketExtractor` transforme uniquement les champs allowlistés vers `IncomingTicket` : `external_ticket_id`, `summary`, `details`, `status`, `priority`, `category`, `agent_id`.
- Le contenu `details` accepte les variantes provider minimisées `details`, `description`, `detail`, `body`, `note`, `symptom` et `problem`; en absence totale de détail exploitable, le champ interne devient une chaîne vide afin de continuer vers les garde-fous PII sans persister de payload brut.
- Le statut accepte les variantes provider minimisées `status`, `status_id`, `statusid`, `ticketstatus` et l'objet `status` via `name` puis `id`; si aucune valeur exploitable n'est présente, le statut interne devient `unknown` sans stockage de payload brut.
- Les champs bruts hors allowlist ne sont pas transmis au service d'ingestion ni aux repositories.

## Variables d'environnement sans secret

Les variables attendues sont documentées dans `backend/.env.example` avec valeurs vides pour les secrets :

- Compliance : `SYNAPPSE_COMPLIANCE_GO_REAL_EXTRACTION` doit rester `false` tant qu'aucun Go conformité formel n'est donné. `HALOPSA_BASE_URL` reste vide ou utilise `https://<tenant>.halopsa.example` sans URL tenant réelle avant Go.
- HaloPSA : `HALOPSA_ENABLE_NETWORK`, `HALOPSA_BASE_URL`, `HALOPSA_CLIENT_ID`, `HALOPSA_CLIENT_SECRET`, `HALOPSA_TENANT`, `HALO_SCOPE`, `HALO_PAGE_SIZE`, `HALOPSA_MAX_PAGE_SIZE`, `HALOPSA_MAX_TOTAL_TICKETS`, `HALO_PAGE_NO`, `HALOPSA_REQUEST_TIMEOUT_SECONDS`, `HALOPSA_MAX_RETRIES`, `HALOPSA_RATE_LIMIT_PER_MINUTE`, `HALOPSA_TOKEN_PATH`, `HALOPSA_TICKETS_PATH`.
- HMAC éventuel : `SYNAPPSE_INCLUDE_AGENT_PSEUDONYM=false` par défaut et `SYNAPPSE_AGENT_ID_HMAC_SECRET` uniquement si l'opt-in est approuvé.
- PostgreSQL : `POSTGRES_ENABLE_WRITE`, `POSTGRES_DSN` ou `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

## PostgreSQL et dataset backend

PostgreSQL est la seule cible de stockage backend. SQLite n'est pas une cible de stockage.

Le schéma local est `backend/app/db/schema.sql`, table `clean_tickets`. Il contient uniquement les colonnes dataset nettoyées :

- identifiant technique provider minimisé : `external_ticket_id` côté backend uniquement, interdit dans les exports ML ;
- textes nettoyés : `summary`, `details` ;
- dimensions minimisées : `status`, `priority`, `category` ;
- pseudonyme optionnel : `agent_id_pseudonym` au format `hmac_sha256:%` ;
- dates métier : `ticket_created_at`, `ticket_updated_at`, `ticket_closed_at` ;
- date technique d'ingestion : `ingested_at`.

Aucune colonne `raw_json`, `payload` ou dump provider brut n'est autorisée.

## EDA agrégée

`python -m backend.app.data.commands.aggregate_ticket_eda` lit PostgreSQL en mode agrégé et retourne uniquement des compteurs, distributions anonymes, métriques temporelles et métriques PII agrégées. La commande n'écrit aucun fichier et ne retourne ni texte brut de ticket, ni identifiant, ni pseudonyme.

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
