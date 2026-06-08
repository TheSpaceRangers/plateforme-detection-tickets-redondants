# Checklist Sprint 1 — Branchement ML PII/HMAC

## Objectif

Formaliser les critères documentaires pour le futur branchement extraction → garde-fous PII/HMAC → export dataset, sans extraction réelle.

## État actuel observé

- Les garde-fous ML existent côté `ml/src/preprocessing/*`.
- `build_preprocessed_ticket_dataset()` applique la sanitation texte et le contrôle PII résiduelle.
- `agent_id` est exclu par défaut.
- La pseudonymisation HMAC requiert `SYNAPPSE_AGENT_ID_HMAC_SECRET` au runtime.
- Aucun flux extraction, stockage ou export n'existe encore.

## Exigences futures de branchement

- [ ] Aucun appel HaloPSA réel pendant la phase documentaire.
- [ ] Aucun stockage durable de JSON brut.
- [ ] Aucun export dataset avant appel à `build_preprocessed_ticket_dataset()`.
- [ ] Allowlist stricte des champs exportables définie avant implémentation.
- [ ] `assert_no_residual_pii()` exécuté et bloquant avant export, stockage et training.
- [ ] `agent_id` brut exclu par défaut.
- [ ] `agent_id_pseudonym` activé uniquement par opt-in documenté.
- [ ] Fail-closed si `SYNAPPSE_AGENT_ID_HMAC_SECRET` est absent quand `agent_id_pseudonym` est demandé.
- [ ] Logs limités à des métadonnées non sensibles.
- [ ] Export limité aux données nettoyées ou pseudonymisées.

## Go avant implémentation opérationnelle

- [ ] Validation tech-lead du contrat d'intégration.
- [ ] Validation sécurité/RGPD de l'allowlist dataset.
- [ ] Secret runtime disponible dans l'environnement cible si pseudonymisation requise.
- [ ] Tests d'intégration définis avant tout branchement réel.
- [ ] Stratégie de stockage/export confirmée sans raw durable.

## No-Go

- [ ] Extraction HaloPSA réelle sans validation explicite.
- [ ] Export complet du payload source.
- [ ] Absence de contrôle PII résiduelle bloquant.
- [ ] Logs contenant tickets, PII ou secret.
- [ ] `agent_id` brut présent dans un artefact exporté.
- [ ] Secret HMAC manquant alors que `agent_id_pseudonym` est attendu.

## Preuve attendue au futur branchement

- [ ] Test qui échoue si un export brut est produit.
- [ ] Test qui échoue si une PII résiduelle subsiste.
- [ ] Test qui échoue si `agent_id` brut est exporté.
- [ ] Test qui échoue si un champ hors allowlist est exporté.
- [ ] Test qui échoue si la pseudonymisation est demandée sans secret HMAC runtime.
