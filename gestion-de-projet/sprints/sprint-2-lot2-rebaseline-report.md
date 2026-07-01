# Sprint 2 renforcé — Rapport Lot 2 Socle données exploitable

**Date** : 2026-07-01  
**Mandat PM** : terminer le Lot 2 avant Lot 3/4 réels.  
**Décision Scrum Master** : **Lot 2 terminé conditionnel synthétique** ; extraction réelle toujours interdite sans Go conformité complet.

## Synthèse exécutive

Le socle technique Lot 2 est majoritairement préparé : extraction HaloPSA contrôlée en fail-closed, PostgreSQL cible, schéma dataset documenté, dry-run synthétique, nettoyage PII, EDA agrégée, contrat dataset ML v1 et cadrage Lot 3.

La conformité a statué :

- **No-Go données réelles HaloPSA** : absence de preuve d'autorisation client, DPA HaloPSA, Go conformité complet et vérification historique Git.
- **Go synthétique préparatoire conditionnel** : autorisable uniquement sans appel HaloPSA réel, sans ID réel, sans export sensible, avec logs agrégés.

Tesla a corrigé deux écarts racine précédemment bloquants :

1. `docker-compose.yml` impose désormais `POSTGRES_PASSWORD` via variable obligatoire sans valeur par défaut.
2. `README.md` utilise désormais un placeholder HaloPSA non sensible.

Le dernier indice tenant HaloPSA réel précédemment présent dans `.opencode/context/domain/halopsa.md` a été remplacé par des placeholders. La recherche working tree ne retourne plus les anciennes chaînes sensibles PostgreSQL/HaloPSA ciblées.

## Livrables techniques validés ou produits par Tech Lead

- `backend/app/data/commands/synthetic_dry_run_ingestion.py`
- `backend/app/data/commands/controlled_halopsa_extract.py`
- `backend/app/data/extractors/halopsa_config.py`
- `backend/app/data/extractors/halopsa_http_transport.py`
- `backend/.env.example`
- `backend/README.md`
- `backend/docs/halopsa_ingestion_read_only.md`
- `backend/app/data/commands/README.md`
- `ml/src/ml_contract/synthetic_source.py`
- `ml/src/eda/quality.py`
- `ml/src/ml_contract/lot3_readiness.py`
- `ml/src/ml_contract/dry_run_report.py`
- `ml/src/ml_contract/ticket_dataset_v1_dry_run.py`
- `ml/src/ml_contract/contract.py`
- `ml/src/ml_contract/ticket_v1_export.py`
- `ml/src/preprocessing/pii.py`
- `ml/docs/dataset-v1-contract.md`
- `ml/docs/preprocessing-guardrails.md`
- `ml/tests/test_synthetic_dry_run_pipeline.py`
- `ml/tests/test_preprocessing_guardrails.py`

## Livrables conformité validés ou partiellement validés

- `gestion-de-projet/rgpd/registre-traitement.md`
- `gestion-de-projet/rgpd/cartographie-champs.md`
- `gestion-de-projet/rgpd/minimisation-donnees.md`
- `gestion-de-projet/rgpd/conservation-purge.md`
- `gestion-de-projet/rgpd/strategie-pseudonymisation.md`
- `gestion-de-projet/security/halopsa_secrets_and_logging_policy.md`
- `gestion-de-projet/checklists/lot2_pre_extraction_go_no_go.md`
- `backend/docs/pre_storage_privacy_controls.md`
- `backend/docs/halopsa_ingestion_read_only.md`
- `ml/docs/dataset-v1-contract.md`
- `ml/docs/preprocessing-guardrails.md`

## Preuves rapportées par les leads

### Technique

- Extraction réelle désactivée par défaut et fail-closed.
- Gate conformité explicite ajouté côté flux contrôlé : `SYNAPPSE_COMPLIANCE_GO_REAL_EXTRACTION=true` requis avant extraction réelle.
- Plafonds d'extraction ajoutés : page size et volume total bornés.
- `agent_id_pseudonym` désactivé par défaut ; opt-in soumis à Go conformité et secret HMAC.
- `external_ticket_id` aligné comme identifiant indirect autorisé backend mais interdit export ML.
- Nettoyage PII renforcé : IPv6, MAC, IBAN, carte apparente, NIR, SIRET/SIREN, identifiants explicites.
- EDA agrégée : valeurs manquantes, doublons/signatures, distributions minimales, volumétrie.
- Lot 3 cadré : labels, pairwise et split anti-fuite sans entraînement réel.

### Tests

- Suite ML exécutée par Tech Lead : `.venv/bin/python -m pytest ml/tests` → **18 passed**.
- QA complète non validée localement : environnement Python 3.9.6 incompatible avec le projet Python 3.11+ ; erreurs `datetime.UTC`, `dataclass(slots=...)`, dépendance `dotenv` manquante.

### Conformité / sécurité

- Contrôles read-only réalisés : recherche fichiers sensibles, secrets, exports, dumps, logs, modèles, archives, datasets, PII évidente.
- Limite : historique Git complet non confirmé ; contrôle obligatoire avant tout Go réel.

## Écarts bloquants

### Bloquants Lot 2 synthétique

| Écart | Statut | Impact |
| --- | --- | --- |
| Anciennes chaînes sensibles PostgreSQL/HaloPSA ciblées | Corrigé | Plus bloquant pour Lot 2 synthétique |
| QA complète non rejouée sous Python 3.11+ | Résiduel | Restriction Lot 3 : relancer avant entraînement ou industrialisation |

### Bloquants données réelles uniquement

- Autorisation client non prouvée.
- DPA HaloPSA absent ou non référencé.
- Checklist Go/No-Go extraction réelle non validée en Go.
- Historique Git non vérifié intégralement pour secrets/données.
- Labels réels, pairwise réel et split réel non validés.

## Décision Go/No-Go

| Gate | Décision | Justification |
| --- | --- | --- |
| Extraction HaloPSA réelle | **No-Go** | Go conformité absent et obligations RGPD/sécurité non prouvées |
| Dataset synthétique préparatoire | **Go conditionnel** | Autorisé sans appel HaloPSA réel, sans données réelles, sans export sensible |
| Lot 2 terminé | **Terminé conditionnel synthétique** | Socle exploitable pour préparation Lot 3 sur dataset synthétique conforme |
| Entrée Lot 3 | **Go conditionnel préparatoire** | Labels/pairwise/split synthétiques cadrés ; aucun entraînement réel sur données HaloPSA |

## Actions immédiates recommandées

1. Démarrer Lot 3 uniquement en mode préparatoire synthétique, sans entraînement réel ni données HaloPSA.
2. Exécuter les tests avec Python 3.11+ : `python3.11 -m pytest tests/unit/backend tests/unit/ml ml/tests`.
3. Produire labels/pairwise/split synthétiques avec anti-fuite groupée.
4. Maintenir le No-Go extraction réelle tant que DPA, autorisation client, audit historique Git et Go conformité ne sont pas prouvés.
5. Faire valider ou corriger le changement de gouvernance `.opencode/agents/scrum-master.md` (`mode: primary` attendu par `AGENTS.md`, `mode: subagent` observé) hors gate données Lot 2.
