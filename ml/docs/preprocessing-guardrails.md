# Contrat ML — extraction vers dataset prétraité

## Périmètre Sprint 1

Cette note formalise l'architecture d'intégration ML entre une future extraction de tickets, les garde-fous PII/HMAC et l'export dataset.

- **Aucune extraction HaloPSA réelle** n'est réalisée à cette étape.
- **Aucune donnée réelle** n'est utilisée ou attendue.
- **Aucun flux opérationnel** extraction, stockage, export ou entraînement n'est encore branché côté ML.
- Le document décrit le contrat obligatoire pour le futur branchement.

## État actuel observé

- `ml/src/preprocessing/tickets.py` expose `build_preprocessed_ticket_dataset()`.
- `build_preprocessed_ticket_dataset()` sanitise les champs texte via `sanitize_ticket_text_fields()` puis applique `assert_no_residual_pii()` avant de retourner le dataset.
- `agent_id` est supprimé par défaut des enregistrements prétraités.
- Si `AgentIdPolicy(include_pseudonymized=True)` est demandé, `agent_id` devient `agent_id_pseudonym` via HMAC-SHA-256 uniquement dans un flux technique explicitement validé ; ce champ reste interdit par défaut dans tout dataset ML et tout rapport ML.
- Le secret runtime attendu pour la pseudonymisation est `SYNAPPSE_AGENT_ID_HMAC_SECRET`.
- En absence de secret, la pseudonymisation échoue en fail-closed via `MissingPseudonymizationSecretError`.

## Contrat d'intégration futur

Tout futur flux ML doit respecter l'ordre suivant :

1. Recevoir des tickets en mémoire depuis un extracteur autorisé.
2. Ne jamais persister le JSON brut durablement.
3. Appeler obligatoirement `build_preprocessed_ticket_dataset()` avant tout export dataset, stockage ou entraînement.
4. Exporter uniquement le résultat nettoyé ou pseudonymisé.
5. Bloquer le flux si `assert_no_residual_pii()` détecte une PII résiduelle.
6. Bloquer le flux si `agent_id` doit être pseudonymisé et que `SYNAPPSE_AGENT_ID_HMAC_SECRET` est absent.

Pourquoi : ce point d'entrée unique limite le risque de contournement des garde-fous PII/HMAC.

## Allowlist dataset stricte

Le futur export dataset doit être piloté par une allowlist explicite, jamais par sérialisation complète des tickets source.

Champs autorisés par défaut après preprocessing :

- `summary` nettoyé ;
- `details` nettoyé ;
- champs métier non sensibles explicitement validés lors de l'exploration de données.

Champs exclus par défaut :

- `agent_id` brut ;
- `agent_id_pseudonym` en dataset/rapport ML par défaut ;
- `external_ticket_id`, considéré comme identifiant indirect non exportable ML ;
- contenu ticket brut ;
- payloads source, dumps JSON et raw IDs ;
- identifiants client, utilisateur, compte, login ou tout champ non validé ;
- tout champ source absent de l'allowlist.

## Règles PII/HMAC obligatoires

- `agent_id` reste exclu par défaut.
- `agent_id_pseudonym` n'est autorisé que par opt-in explicite pour un flux technique validé ; il reste interdit par défaut dans les datasets et rapports ML.
- La pseudonymisation HMAC doit utiliser `SYNAPPSE_AGENT_ID_HMAC_SECRET` lu à l'exécution.
- Le secret ne doit jamais être loggé, exporté, affiché ou documenté avec sa valeur.
- Les logs ne doivent contenir ni texte de ticket, ni PII, ni secret ; seules des métadonnées non sensibles sont admises, par exemple nombre de lignes traitées ou statut d'échec.
- Le contrôle PII résiduelle est bloquant avant export, stockage et training.

## Limites du nettoyage PII en texte libre

Le détecteur couvre des catégories fréquentes et raisonnables pour des tickets libres : emails, téléphones français, IPv4/IPv6, URLs, MAC addresses, identifiants explicites (`login`, `user_id`, `external_ticket_id`, etc.), IBAN/cartes de paiement au format apparent, NIR français et SIRET/SIREN précédés d'un libellé. Il fonctionne en fail-closed sur ces catégories : une détection résiduelle bloque le flux.

Limites assumées sans sur-promesse :

- les noms/prénoms en texte libre ne sont pas garantis, car les faux positifs seraient élevés sans référentiel validé ;
- les contextes métier locaux, surnoms, noms d'équipes, sites, contrats ou applications peuvent indirectement identifier une personne ou une organisation sans correspondre à un motif fiable ;
- les formats obfusqués, incomplets, avec fautes ou très spécifiques au client peuvent échapper aux regex ;
- le nettoyage automatique ne remplace pas une revue conformité/sécurité avant toute donnée réelle.

Conclusion opérationnelle : aucun branchement sur données réelles, extraction HaloPSA, entraînement, export durable ou partage de dataset n'est autorisé sans GO conformité explicite, revue du schéma réel et validation des colonnes.

## Dataset synthétique préparatoire

Le dataset synthétique ML est limité à des tickets fictifs construits dans le code pour exercer les garde-fous : PII fictive, doublons, valeurs manquantes, dates hors scope et volumétrie minimale de split. Il ne doit jamais être remplacé par des données HaloPSA réelles sans GO conformité explicite.

## Périmètre temporel EDA/ML

- Les métriques EDA/ML filtrées doivent exclure par défaut les tickets dont `ticket_created_at` est antérieur au `2025-01-01`.
- Ce filtre est appliqué uniquement au calcul des métriques et aux datasets ML filtrés en mémoire ; il ne supprime, ne met à jour et ne masque jamais les lignes source en base.
- Les sorties EDA doivent exposer uniquement des compteurs agrégés non identifiants : `total_source_count`, `included_count`, `excluded_historical_outlier_count`, `excluded_missing_ticket_created_at_count` et `applied_min_ticket_created_at`.
- Les champs texte, IDs, payloads, PII et secrets restent interdits dans toute sortie EDA.

Pourquoi : les tickets pré-2025 sont acceptés comme outliers historiques probables et ne doivent pas biaiser les métriques de démonstration.

## No raw durable

Interdictions pour le futur branchement :

- écrire des payloads HaloPSA bruts dans `ml/data`, logs, artefacts CI ou stockage applicatif ;
- conserver des dumps JSON bruts pour debug ;
- exporter un dataset avant passage par `build_preprocessed_ticket_dataset()` ;
- entraîner un modèle sur des tickets non nettoyés.

## Préparation labels/pairwise/split Lot 3 synthétique

- Les labels synthétiques ne servent qu'à préparer les garde-fous et la forme du futur pipeline ; ils ne doivent pas déclencher d'entraînement avant GO conformité.
- La future génération pairwise devra éviter la fuite : un groupe de redondance ou un ticket source et toutes ses paires dérivées restent dans un seul split.
- Les paires inverses `(A, B)` / `(B, A)` ne doivent jamais être réparties entre train et test.
- Le split prévu après GO est groupé et stratifié 70/30 avec `random_state=42`, après validation des labels et exploration du schéma réel.

## Conditions Go avant implémentation opérationnelle

- Source d'extraction validée par le tech-lead et alignée sécurité.
- Schéma source exploré sans donnée réelle exposée dans les logs.
- Allowlist dataset approuvée et documentée.
- Secret `SYNAPPSE_AGENT_ID_HMAC_SECRET` disponible uniquement dans le runtime cible si `agent_id_pseudonym` est requis.
- Tests de non-régression PII/HMAC ajoutés avant branchement réel.
- Stratégie de stockage/export confirmée comme nettoyée ou pseudonymisée uniquement.

## Conditions No-Go

- Extraction HaloPSA réelle demandée sans validation explicite.
- Besoin de `agent_id_pseudonym` sans secret runtime disponible.
- Export brut ou stockage durable de JSON source.
- Absence de test bloquant sur PII résiduelle.
- Logs contenant du contenu ticket, PII ou secret.
- Allowlist absente ou remplacée par une exportation complète du payload.

## Preuve attendue lors du futur branchement

Le futur branchement devra fournir au minimum un test d'intégration qui échoue si :

- un export dataset contourne `build_preprocessed_ticket_dataset()` ;
- une PII résiduelle reste présente après preprocessing ;
- `agent_id` brut apparaît dans le dataset exporté ;
- `agent_id_pseudonym` est demandé sans `SYNAPPSE_AGENT_ID_HMAC_SECRET` ;
- un champ non allowlisté est exporté.
