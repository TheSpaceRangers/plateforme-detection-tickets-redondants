# Schéma PostgreSQL conceptuel — Lot 2

## Objectif

Décrire un modèle PostgreSQL conceptuel pour les données HaloPSA préparées au Lot 2, sans SQL, sans code applicatif et sans stockage durable de JSON brut.

## Principes de conception

- Les noms de tables et colonnes sont en `snake_case`.
- Les données stockées sont minimisées et nettoyées avant persistance.
- Aucun payload JSON brut HaloPSA n'est conservé durablement.
- `agent_id` est exclu par défaut.
- `agent_id_pseudo` et les pseudonymes ne sont autorisés que sur exception validée avec HMAC-SHA-256.
- Chaque enregistrement exploitable porte une date `data_retention_until`.
- Les preuves de purge sont conservées dans une table dédiée sans contenu ticket.

## Tables conceptuelles

### `import_batches`

Représente un lot d'import ou de dry-run contrôlé.

Colonnes conceptuelles :

- `import_batch_id` : identifiant interne du lot ;
- `source_system` : système source attendu, par exemple HaloPSA sans détail secret ;
- `run_mode` : `dry_run` ou `controlled_import` ;
- `status` : statut du lot ;
- `requested_at` : date de demande ;
- `started_at` : date de début ;
- `completed_at` : date de fin ;
- `records_seen_count` : volume agrégé observé ;
- `records_accepted_count` : volume agrégé accepté ;
- `records_rejected_count` : volume agrégé rejeté ;
- `fields_rejected_count` : nombre agrégé de champs hors allowlist ;
- `data_retention_until` : date limite de conservation ;
- `purge_required` : indicateur de purge à effectuer ;
- `created_by_process` : nom logique du processus, sans identifiant personnel ;
- `compliance_validation_ref` : référence documentaire interne de validation.

Contraintes logiques :

- un lot ne peut pas passer en import contrôlé sans validation conformité ;
- un dry-run ne doit pas créer d'enregistrements persistants dans `ticket_staging` ou `tickets_curated` ;
- les compteurs sont agrégés et ne contiennent aucun contenu ticket.

### `ticket_staging`

Zone transitoire contenant uniquement des données déjà nettoyées.

Colonnes conceptuelles :

- `ticket_staging_id` : identifiant interne staging ;
- `import_batch_id` : référence au lot d'import ;
- `ticket_id_source` : identifiant source du ticket ;
- `created_at` : date de création source ;
- `updated_at` : date de mise à jour source ;
- `category` : catégorie normalisée ;
- `subcategory` : sous-catégorie normalisée ;
- `status` : statut normalisé ;
- `priority` : priorité normalisée ;
- `cleaned_title` : titre nettoyé et minimisé ;
- `cleaned_description` : description nettoyée et minimisée ;
- `agent_id_pseudo` : pseudonyme conditionnel, absent par défaut ;
- `pii_cleaning_status` : statut du nettoyage PII ;
- `validation_status` : statut de validation qualité ;
- `rejection_reason_code` : code de rejet sans contenu ticket ;
- `data_retention_until` : date limite de conservation ;
- `created_at_internal` : date de création interne.

Contraintes logiques :

- `import_batch_id` référence `import_batches` ;
- `ticket_id_source` est unique dans un lot ;
- `cleaned_title` et `cleaned_description` ne doivent contenir aucun titre ou description brute ;
- les lignes rejetées ne doivent pas être promues vers `tickets_curated` ;
- aucun champ `raw_json` ou équivalent n'est autorisé.

### `tickets_curated`

Table cible pour les données validées et minimisées.

Colonnes conceptuelles :

- `ticket_curated_id` : identifiant interne curated ;
- `source_ticket_staging_id` : référence à la ligne staging validée ;
- `ticket_id_source` : identifiant source du ticket ;
- `created_at` : date de création source ;
- `updated_at` : date de mise à jour source ;
- `category` : catégorie validée ;
- `subcategory` : sous-catégorie validée ;
- `status` : statut validé ;
- `priority` : priorité validée ;
- `cleaned_title` : titre nettoyé validé ;
- `cleaned_description` : description nettoyée validée ;
- `agent_id_pseudo` : pseudonyme conditionnel si exception validée ;
- `curation_status` : statut de curation ;
- `data_quality_score` : score conceptuel de qualité ;
- `data_retention_until` : date limite de conservation ;
- `curated_at` : date de promotion en curated.

Contraintes logiques :

- `source_ticket_staging_id` référence `ticket_staging` ;
- seules les lignes validées peuvent être promues ;
- `data_retention_until` est obligatoire ;
- aucune donnée brute, aucun payload, aucun secret et aucun header ne sont autorisés.

### `ticket_pseudonyms` optionnelle

Table optionnelle, activable uniquement si une exception conformité est validée.

Colonnes conceptuelles :

- `ticket_pseudonym_id` : identifiant interne ;
- `pseudonym_type` : type de pseudonyme, par exemple agent ou organisation ;
- `pseudonym_value` : valeur pseudonymisée par HMAC-SHA-256 ;
- `hmac_key_version` : version de clé HMAC utilisée ;
- `validation_ref` : référence de validation de l'exception ;
- `created_at_internal` : date de création interne ;
- `data_retention_until` : date limite de conservation.

Contraintes logiques :

- aucun identifiant brut ne doit être stocké dans cette table ;
- la clé HMAC n'est jamais stockée en base ;
- l'usage est interdit sans validation d'exception ;
- les pseudonymes sont purgés avec les données associées.

### `data_purge_logs`

Journal conceptuel des purges et preuves associées, sans contenu ticket.

Colonnes conceptuelles :

- `data_purge_log_id` : identifiant interne du journal ;
- `purge_scope` : périmètre logique purgé ;
- `purge_reason` : raison de purge ;
- `scheduled_for` : date prévue ;
- `executed_at` : date d'exécution ;
- `records_deleted_count` : nombre agrégé d'enregistrements supprimés ;
- `import_batch_id` : lot concerné si applicable ;
- `retention_deadline` : échéance de conservation liée ;
- `purge_evidence_ref` : référence interne de preuve de purge ;
- `executed_by_process` : processus ayant exécuté la purge ;
- `status` : statut de la purge.

Contraintes logiques :

- le journal ne contient aucun titre, description, payload, secret ou identifiant personnel brut ;
- chaque purge J+7 post-soutenance doit produire une preuve ;
- les échecs de purge doivent être visibles via un statut et une référence de suivi.

## Relations conceptuelles

- `import_batches` possède zéro ou plusieurs lignes `ticket_staging`.
- `ticket_staging` peut produire zéro ou une ligne `tickets_curated`.
- `tickets_curated` peut référencer un pseudonyme uniquement si l'exception HMAC-SHA-256 est validée.
- `data_purge_logs` peut référencer un `import_batch_id` pour prouver la purge d'un lot.

## Exclusions explicites

- Aucun champ `raw_json`, `payload`, `headers`, `authorization_header` ou équivalent.
- Aucun `agent_id` brut.
- Aucun nom, prénom, e-mail, téléphone, pièce jointe ou commentaire brut.
- Aucun contenu complet de titre ou description non nettoyé.

## Conservation

`data_retention_until` doit être présent sur les tables contenant des données tickets ou pseudonymisées. La purge doit être documentée dans `data_purge_logs`, notamment pour l'échéance J+7 post-soutenance.
