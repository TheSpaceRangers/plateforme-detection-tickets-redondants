# Pipeline backend de données — Lot 2

## Objectif

Définir la stratégie conceptuelle de préparation des données HaloPSA pour le Lot 2, sans extraction réelle, sans payload réel et sans code applicatif.

## Périmètre et interdits

- Aucune extraction HaloPSA n'est réalisée dans le Lot 2.
- Aucun payload HaloPSA réel n'est conservé dans ce document.
- Aucun secret, jeton, en-tête d'authentification ou identifiant technique sensible n'est documenté.
- Aucun stockage durable de JSON brut n'est autorisé.
- Le Lot 3 ML reste en **NO-GO** tant qu'un dataset réel conforme n'a pas été validé.

## Stratégie d'extraction HaloPSA sans extraction réelle

Le Lot 2 prépare uniquement les règles de collecte et de contrôle. L'extraction future sera déclenchée après validation conformité, sécurité et périmètre métier.

Principes retenus :

1. définir les champs autorisés avant toute connexion ;
2. exécuter un dry-run sans persistance pour contrôler volumes et structure ;
3. refuser toute donnée hors allowlist ;
4. nettoyer les données personnelles avant stockage ;
5. stocker uniquement des champs normalisés en staging nettoyé puis en curated ;
6. documenter les preuves de purge et la date limite de conservation.

Pourquoi : cette approche réduit le risque de collecte excessive avant d'engager l'exploitation réelle des données.

## Pré-validation conformité

Avant toute extraction réelle, les contrôles suivants doivent être validés :

- base légale et finalité de traitement confirmées ;
- minimisation des champs validée par le responsable conformité ;
- politique de conservation acceptée ;
- politique de journalisation sans contenu ticket validée ;
- méthode de pseudonymisation validée si une exception est demandée ;
- dry-run exécuté sans persistance durable ;
- échantillon de structure contrôlé sans contenu réel exposé dans les traces.

## Allowlist stricte des champs

### Champs autorisés par défaut

| Champ conceptuel | Usage | Justification |
| --- | --- | --- |
| `ticket_id_source` | Déduplication et traçabilité source | Nécessaire pour relier un ticket à sa source sans stocker le payload brut. |
| `created_at` | Analyse temporelle | Utile pour filtrer les périodes et mesurer la fraîcheur des données. |
| `updated_at` | Contrôle de synchronisation | Permet d'éviter les reprises inutiles. |
| `category` | Similarité métier | Signal utile pour comparer des tickets proches. |
| `subcategory` | Similarité métier fine | Améliore la précision sans identifier directement une personne. |
| `status` | Qualité et filtrage | Permet d'exclure des tickets non pertinents. |
| `priority` | Contexte de traitement | Signal métier non directement identifiant. |
| `cleaned_title` | Similarité textuelle après nettoyage | Utilisé uniquement après suppression ou masquage des PII. |
| `cleaned_description` | Similarité textuelle après nettoyage | Champ principal pour la détection, strictement nettoyé avant stockage. |
| `data_retention_until` | Conservation limitée | Nécessaire pour piloter la purge J+7 post-soutenance. |

### Champs conditionnels

| Champ conceptuel | Condition | Justification |
| --- | --- | --- |
| `agent_id_pseudo` | Uniquement si exception conformité validée | Permet des analyses opérationnelles sans conserver l'identifiant agent brut. |
| `requester_domain_hash` | Uniquement si besoin métier validé | Agrégation possible sans stocker d'adresse complète. |
| `site_or_customer_pseudo` | Uniquement si pseudonymisation validée | Peut aider à détecter des doublons locaux sans exposer le client. |

### Champs exclus

| Champ exclu | Raison d'exclusion |
| --- | --- |
| `agent_id` | Exclu par défaut : identifiant personnel ou assimilable. |
| nom, prénom, e-mail, téléphone | Données directement identifiantes non nécessaires au modèle. |
| titre complet brut | Peut contenir des données personnelles ou confidentielles. |
| description complète brute | Peut contenir des données personnelles, secrets, logs ou informations clients. |
| pièces jointes | Risque élevé de données sensibles et hors périmètre Lot 2. |
| commentaires internes bruts | Risque de données personnelles, secrets et informations confidentielles. |
| en-têtes HTTP, tokens, cookies | Secrets ou éléments techniques sensibles. |
| payload JSON brut | Interdit en stockage durable. |

## Dry-run sans persistance

Le dry-run futur devra :

- appeler uniquement un périmètre limité et pré-validé ;
- ne pas écrire en base durable ;
- ne pas enregistrer de payload ;
- produire seulement des métriques agrégées : nombre de tickets candidats, champs présents, champs rejetés, erreurs de mapping ;
- vérifier que tous les champs hors allowlist sont ignorés.

## Extraction future contrôlée

Une extraction réelle ne sera autorisée qu'après validation explicite des contrôles préalables. Elle devra être limitée par période, volume et finalité.

Le flux conceptuel cible est :

1. connexion sécurisée via variables d'environnement ou secret manager ;
2. récupération contrôlée des champs allowlistés ;
3. rejet immédiat des champs exclus ;
4. nettoyage PII en mémoire avant toute persistance ;
5. écriture dans `ticket_staging` uniquement avec données nettoyées ;
6. validation qualité ;
7. promotion vers `tickets_curated` ;
8. purge du staging selon politique de conservation.

## Nettoyage PII avant stockage

Le nettoyage doit intervenir avant toute écriture durable. Les traitements attendus sont conceptuels :

- suppression ou masquage des e-mails, téléphones, noms détectables et identifiants directs ;
- suppression des secrets potentiels, chemins sensibles et extraits de logs confidentiels ;
- normalisation du texte utile à la similarité ;
- conservation uniquement de champs nettoyés explicitement autorisés.

## No raw JSON durable

Aucun JSON brut HaloPSA ne doit être stocké durablement. Les données doivent être transformées en colonnes conceptuelles minimisées, nettoyées et documentées.

## Staging nettoyé puis curated

- `ticket_staging` reçoit uniquement des données déjà nettoyées, avec statut de validation.
- `tickets_curated` reçoit uniquement les enregistrements validés pour usage analytique ou ML futur.
- Les rejets sont comptabilisés sans contenu ticket dans les logs.

## Conservation et purge J+7 post-soutenance

Chaque lot de données doit porter une date `data_retention_until`. La purge doit être planifiée au plus tard à J+7 après soutenance, avec preuve de purge inscrite dans les journaux dédiés.

## Anticipation Service Layer / Repository Pattern

Lors d'une implémentation future, la logique métier d'import, de nettoyage et de validation devra être portée par une couche de services. Les accès PostgreSQL devront être isolés dans des repositories dédiés. Ce document ne définit aucun code applicatif.

Pourquoi : cette séparation facilite les contrôles de sécurité, les tests et l'audit des responsabilités.

## Décision Lot 3 ML

Le Lot 3 ML est en **NO-GO** tant qu'un dataset réel conforme, nettoyé, minimisé, validé et purgeable n'a pas été approuvé.
