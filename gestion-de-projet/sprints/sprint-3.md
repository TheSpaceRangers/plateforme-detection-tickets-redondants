# Sprint 3 — Entraîner, comparer et sélectionner le modèle

**Fenêtre cible** : 2026-06-15 → 2026-06-30  
**Lots couverts** : Lot 3  
**Statut** : ⏳ À venir — interdit sans Go Lot 3  
**Objectif** : respecter le RNCP Bloc 3 par un pipeline ML supervisé reproductible, comparant quatre modèles et sélectionnant un modèle intégrable.

## Livrables attendus

- Protocole d'évaluation supervisée.
- Baseline documentée.
- KNN, Random Forest, Decision Tree, Logistic Regression entraînés.
- Grid Search réalisé.
- Accuracy, F1, Recall comparés.
- Modèle sélectionné et sérialisé localement.
- Rapport limites, seuil de confiance, explicabilité.

## Dépendances

- Go Lot 3 validé en sortie Sprint 2.
- Dataset nettoyé, labellisé, pairwise et conforme.
- Split ≥ 70/30 validé.
- Politique artefacts ML : pas de `.pkl/.joblib` sensible dans Git.

## Critères de validation

- [ ] Les 4 algorithmes RNCP sont comparés.
- [ ] Grid Search et métriques obligatoires documentés.
- [ ] Modèle sérialisé prêt pour API.
- [ ] Logs ML sans texte ticket ni données personnelles.
- [ ] Rapport d'évaluation exploitable en mémoire.

## Go/No-Go

**No-Go ML** si Lot 2 n'est pas validé.  
**Go Lot 4** si modèle + métriques + artefact local sont validés techniquement et conformité.

## Issues GitHub

- Issue globale Sprint 3 : #8.
- US détaillées dans `gestion-de-projet/backlog.md` : US-ML-001, US-ML-002, US-ML-003.

## Points de vigilance

- Ne pas optimiser avant baseline.
- Conserver les preuves RNCP dès ce sprint pour éviter la dette mémoire.
