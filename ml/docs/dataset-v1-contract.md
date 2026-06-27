# Contrat dataset ML v1 — dry-run conformité

## Scope validé

- Filtre officiel : `ticket_created_at >= 2025-01-01`.
- Référence attendue issue de l'EDA filtrée : 13 578 inclus, 2 historiques exclus, 9 sans date exclus.
- Le dry-run n'appelle pas HaloPSA, ne lit pas `.env`, n'exporte aucun dataset et n'affiche aucun ticket, ID, payload ou texte ligne par ligne.

## Allowlist stricte des colonnes dataset prévues

Entrées raw transitoires autorisées uniquement en mémoire pour transformation : `summary`, `details`, `ticket_created_at`. Elles ne sont jamais autorisées comme colonnes dataset ni comme champs du rapport dry-run.

- `cleaned_text_truncated`
- `created_day_of_week`
- `created_month`
- `created_week`
- `cleaned_text_length`
- `text_length_bucket`
- `has_email_placeholder`
- `has_phone_placeholder`
- `has_url_placeholder`

## Denylist stricte

Colonnes interdites en dataset/rapport : `external_ticket_id`, `agent_id`, `agent_id_pseudonym`, `payload`, IDs (`id`, `ticket_id`, `user_id`, `client_id`, `customer_id`, `account_id` et motifs `_id`/UUID/GUID), timestamps exacts (`created_at`, `updated_at`, `ticket_created_at`, `closed_at`, `resolved_at`, motifs `_at`/`timestamp`), `priority`, `category`, texte brut ou non tronqué (`summary`, `details`, `raw_text`, `cleaned_text`). Toute colonne source injectable hors `summary`, `details`, `ticket_created_at` est bloquée par défaut.

## Transformations

- Concaténation contrôlée de `summary` et `details` en mémoire uniquement.
- Nettoyage PII officiel via placeholders typés, normalisation whitespace/minuscules, puis troncature à 512 caractères.
- Granularisation date : mois, semaine ISO et jour de semaine uniquement ; aucun timestamp exact en sortie.
- Features placeholders : `has_email_placeholder`, `has_phone_placeholder`, `has_url_placeholder`.
- Scans post-transformation agrégés : `pii_official_residual_count` et `secret_scan_count`.

## Gates bloquants

- Colonne interdite détectée.
- PII résiduelle post-transformation > 0.
- Secret détecté post-transformation > 0.
- Timestamp exact dans les colonnes prévues.
- Colonne de texte brut ou texte nettoyé non tronqué.
- Tentative de chemin d'export dataset via CLI dry-run.

## Rapport dry-run autorisé

Le rapport est uniquement agrégé : compteurs de scope, colonnes prévues, compteurs de violations et statut des gates. Il ne contient ni contenu ticket, ni ID, ni payload, ni valeur source.

## Conservation, purge et génération réelle

- Conservation : aucun fichier data n'est créé par le dry-run ; seules les sorties console agrégées peuvent être conservées dans des logs de CI.
- Purge : aucun artefact dataset à purger pour ce dry-run. Toute future génération réelle devra définir une durée de conservation et une procédure de suppression explicites avant GO.
- Gate de mise en production : une génération réelle reste NO-GO tant que l'accès source, la destination, les contrôles RGPD/sécurité et la purge ne sont pas validés.
