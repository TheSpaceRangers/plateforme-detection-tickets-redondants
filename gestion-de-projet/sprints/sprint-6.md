# Sprint 6 — Qualité, sécurité, RGPD, CI

**Fenêtre cible** : 2026-08-01 → 2026-08-15  
**Lots couverts** : Lot 5  
**Statut** : ⏳ À venir  
**Objectif** : stabiliser l'application, valider les audits sécurité/RGPD et préparer les preuves finales.

## Livrables attendus

- Tests backend/frontend/ML pertinents.
- CI GitHub active.
- Contrôles secrets/datasets/fichiers interdits.
- Audit sécurité final.
- Audit RGPD final.
- Documentation installation/exploitation locale.
- Inventaire des actifs sensibles.

## Dépendances

- Application fonctionnelle Sprint 5.
- Scénario démo stable.
- Données de démonstration conformes.
- Main protégée compatible avec checks CI.

## Critères de validation

- [ ] CI verte ou écarts documentés.
- [ ] Tests exécutables localement.
- [ ] Audits sécurité/RGPD terminés.
- [ ] Aucun secret, dataset réel, dump, log sensible ou modèle sensible versionné.
- [ ] Documentation exploitation locale prête.

## Go/No-Go

**Go Lot 6** si application, CI, audits et documentation sont validés.  
**No-Go mémoire** si secrets/données personnelles apparaissent dans repo, captures, logs ou annexes.

## Issues GitHub

- Issue globale Sprint 6 : #11.
- US détaillées dans `gestion-de-projet/backlog.md` : US-QA-001, US-COMP-001.

## Points de vigilance

- CI minimale recommandée avant ce sprint dès que les premiers modules testables existent.
- Audits à conserver comme annexes mémoire.
