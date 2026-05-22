# STATUS — Plateforme Détection Tickets Redondants

**Dernière mise à jour** : 2026-05-22  
**Pilotage** : Projet complet — SYNAPPSE / RNCP 37137  
**Statut global** : 🔄 Planification globale initialisée, Lot 2 critique à sécuriser

## Vision produit

Plateforme IA privée et auto-hébergée permettant de détecter automatiquement les tickets HaloPSA redondants d'un même client, d'alerter les techniciens avant traitement, et de fournir un score de confiance avec explication.

## Objectifs stratégiques

| Objectif | Résultat attendu | Mesure de succès |
| -------- | ---------------- | ---------------- |
| Réduire les doublons de traitement support | Alerte proactive sur tickets similaires | Détection exploitable dans l'application web |
| Exploiter les historiques HaloPSA | Dataset structuré et traçable | Données importées, nettoyées, stockées PostgreSQL |
| Valider une démarche ML supervisée | Modèle comparé et sélectionné | Accuracy, F1, Recall + Grid Search |
| Respecter les contraintes académiques RNCP | Livrables techniques + mémoire | Dépôt mémoire 2026-09-01, soutenance octobre 2026 |
| Préserver confidentialité et conformité | Traitements locaux et documentés | Registre RGPD, pseudonymisation, secrets protégés |

## Roadmap globale

| Lot | Période cible | Objectif | Livrables attendus | Statut |
| --- | ------------- | -------- | ------------------ | ------ |
| 0 | Mai 2026 | Gouvernance projet et socle GitHub | Repo public, branche `main` protégée, backlog, sprints, workflow PR | ✅ Terminé |
| 1 | Mars — Avril 2026 | Cadrage fonctionnel, technique et réglementaire | Note de cadrage, audit API HaloPSA, dictionnaire données, analyse RGPD, veille | ✅ À confirmer |
| 2 | Mai 2026 | Socle données exploitable | Extraction contrôlée HaloPSA, PostgreSQL, nettoyage NLP, EDA, dataset ticket | 🔴 Critique |
| 3 | Juin 2026 | Pipeline ML supervisé | Labels, dataset pairwise, features TF-IDF, KNN/RF/DT/LR, Grid Search, métriques | ⏳ Bloqué par Lot 2 |
| 4 | Juillet 2026 | Application web locale | API FastAPI, UI React/Vite, dashboard, intégration modèle, logs prédictions | ⏳ À venir |
| 5 | Juillet — Août 2026 | Qualité, sécurité, conformité, CI/CD locale | Tests, audit sécurité, audit RGPD, CI GitHub, documentation déploiement local | ⏳ À venir |
| 6 | Août — Septembre 2026 | Mémoire et soutenance | Mémoire PDF, annexes, support oral, répétitions, preuves projet | ⏳ À venir |

## Jalons directeurs

| Date | Jalon | Critère de validation | Statut |
| ---- | ----- | --------------------- | ------ |
| 2026-05-22 | Gouvernance GitHub active | Repo créé, `main` protégée, PR obligatoire | ✅ Atteint |
| 2026-05-31 | Socle données exploitable | Extraction contrôlée + PostgreSQL + dataset nettoyé + EDA | 🔴 À risque |
| 2026-06-15 | Dataset ML labellisé | Paires tickets, labels, split ≥ 70/30 validés | ⏳ À venir |
| 2026-06-30 | Modèle ML sélectionné | 4 algorithmes comparés, Grid Search, métriques documentées | ⏳ À venir |
| 2026-07-15 | API + modèle intégrés | Endpoint prédiction opérationnel et traçable | ⏳ À venir |
| 2026-07-31 | Application web locale prête | Dashboard utilisable, score + explication visibles | ⏳ À venir |
| 2026-08-15 | Qualité et conformité validées | Tests, audits sécurité/RGPD, documentation exploitation | ⏳ À venir |
| 2026-09-01 | Mémoire déposé | PDF final déposé | ⏳ À venir |
| Octobre 2026 | Soutenance | Démonstration + argumentaire RNCP | ⏳ À venir |

## Macro-planning par phases

### Phase A — Gouvernance et cadrage projet

- Objectif : sécuriser la vision, le périmètre, les règles GitHub et l'organisation agentique.
- Dépendances : aucune.
- Sortie attendue : projet pilotable avec roadmap, backlog, règles PR.
- Statut : ✅ Terminé pour GitHub ; livrables Lot 1 à confirmer.

### Phase B — Données HaloPSA et conformité

- Objectif : extraire, nettoyer et stocker les tickets exploitables sans risque RGPD.
- Dépendances : accès HaloPSA, secrets valides, registre de traitement, stratégie de pseudonymisation.
- Sortie attendue : dataset ticket en PostgreSQL + EDA + critères qualité.
- Statut : 🔴 Priorité immédiate.

### Phase C — Machine Learning supervisé

- Objectif : construire et comparer les modèles de détection de redondance.
- Dépendances : dataset nettoyé, labels, features, protocole d'évaluation.
- Sortie attendue : modèle sérialisé, métriques, rapport d'évaluation.
- Statut : ⏳ Interdit tant que Phase B non validée.

### Phase D — Application web locale

- Objectif : exposer la détection via API et interface technicien.
- Dépendances : modèle sélectionné, schéma prédiction, base PostgreSQL.
- Sortie attendue : FastAPI + React/Vite + dashboard + logs prédictions.
- Statut : ⏳ À venir.

### Phase E — Industrialisation locale et conformité finale

- Objectif : fiabiliser tests, sécurité, RGPD, documentation et exploitation locale.
- Dépendances : application fonctionnelle.
- Sortie attendue : CI, tests, audits, documentation installation/démo.
- Statut : ⏳ À venir.

### Phase F — Mémoire et soutenance

- Objectif : consolider les preuves, rédiger le mémoire et préparer la démonstration.
- Dépendances : résultats techniques et conformité documentés.
- Sortie attendue : mémoire, annexes, support oral, scénario démo.
- Statut : ⏳ À venir.

## Sprints directeurs proposés

| Sprint | Fenêtre cible | Objectif | Lots couverts | Validation attendue |
| ------ | ------------- | -------- | ------------ | ------------------- |
| Sprint 0 | 2026-05-22 | Gouvernance GitHub et planification globale | Lot 0 | Repo, règles `main`, roadmap, backlog |
| Sprint 1 | 2026-05-23 → 2026-05-31 | Sécuriser conformité + socle données | Lots 1-2 | Go/No-Go extraction réelle et dataset ML |
| Sprint 2 | 2026-06-01 → 2026-06-14 | Finaliser dataset ML et labellisation | Lot 2-3 | Dataset pairwise + labels + split validés |
| Sprint 3 | 2026-06-15 → 2026-06-30 | Entraîner, comparer et sélectionner modèle | Lot 3 | 4 modèles + Grid Search + métriques |
| Sprint 4 | 2026-07-01 → 2026-07-15 | Construire API prédiction et intégration modèle | Lot 4 | Endpoint prédiction + logs PostgreSQL |
| Sprint 5 | 2026-07-16 → 2026-07-31 | Construire dashboard technicien | Lot 4 | UI affichant alertes, scores, explications |
| Sprint 6 | 2026-08-01 → 2026-08-15 | Qualité, sécurité, RGPD, CI | Lot 5 | Tests + audits + documentation exploitation |
| Sprint 7 | 2026-08-16 → 2026-08-31 | Mémoire, annexes et démo finale | Lot 6 | Mémoire prêt dépôt + scénario soutenance |

## Dépendances critiques

| Dépendance | Bloque | Décision PM |
| ---------- | ------ | ----------- |
| Accès API HaloPSA + secrets valides | Lot 2 | Priorité P0 avant extraction |
| Registre RGPD + pseudonymisation | Lots 2-3 | Pas de données réelles sans validation conformité |
| PostgreSQL local opérationnel | Lots 2-4 | Obligatoire, pas de SQLite |
| Dataset nettoyé + EDA | Lot 3 | Critère d'entrée ML |
| Labels de redondance | Lot 3 | Critère d'entrée entraînement supervisé |
| Modèle sérialisé | Lot 4 | Critère d'entrée API prédiction |
| Tests et CI | Lot 5 | Critère de stabilisation avant mémoire |

## Critères d'entrée / sortie par lot

| Lot | Entrée | Sortie |
| --- | ------ | ------ |
| Lot 1 | Problématique et périmètre validés | Cadrage, risques, contraintes, données cibles |
| Lot 2 | Accès API + conformité validée | Dataset ticket nettoyé, stocké, documenté |
| Lot 3 | Dataset + labels + split | Modèle sélectionné et métriques reproductibles |
| Lot 4 | Modèle sérialisé + schémas API | Application web locale intégrant la prédiction |
| Lot 5 | Application fonctionnelle | Tests, audits, CI, documentation stable |
| Lot 6 | Résultats projet consolidés | Mémoire, annexes, support soutenance |

## Contraintes non négociables

- Hébergement 100% local, pas de cloud externe pour les traitements applicatifs.
- Secrets uniquement via variables d'environnement ou GitHub Secrets.
- PostgreSQL obligatoire, pas de SQLite.
- Frontend JavaScript, pas de TypeScript.
- Workflow GitHub : `main` protégée, changements via PR.
- RNCP Bloc 3 : KNN, Random Forest, Decision Tree, Logistic Regression.
- Train/test split ≥ 70/30.
- Métriques minimales : Accuracy, F1, Recall.
- Grid Search obligatoire.
- Application web intégrant le modèle.

## Risques majeurs

| Risque | Probabilité | Impact | Mitigation |
| ------ | ----------- | ------ | ---------- |
| Retard Lot 2 données | Élevée | Élevé | Prioriser extraction, PostgreSQL, EDA, labels avant ML |
| Non-conformité RGPD | Moyenne | Élevé | Registre, minimisation, pseudonymisation, audit avant données réelles |
| Qualité insuffisante des labels | Moyenne | Élevé | Définir protocole de labellisation et revue d'échantillons |
| Modèle peu performant | Moyenne | Moyen | Comparer 4 modèles, baseline, features explicables, seuils ajustables |
| Dérive mémoire/soutenance | Moyenne | Élevé | Documenter preuves à chaque sprint, annexes en continu |
| Absence de CI | Moyenne | Moyen | Introduire CI avant Sprint 6 et status checks ensuite |

## Décisions PM actées

| Date | Décision | Impact |
| ---- | -------- | ------ |
| 2026-05-22 | Dépôt GitHub public créé et `main` protégée après bootstrap. | Workflow PR obligatoire. |
| 2026-05-22 | Planification globale structurée en 7 sprints directeurs. | Vision projet complète jusqu'à soutenance. |
| 2026-05-22 | Lot 3 ML interdit tant que Lot 2 données/conformité non validé. | Évite de produire un ML non reproductible ou non conforme. |
| 2026-05-22 | Extraction HaloPSA réelle interdite sans garde-fous RGPD. | Réduit le risque légal et sécurité. |

## Prochaine action de pilotage

Mandater Eisenhower pour décliner cette planification globale en backlog complet, sprints détaillés, issues GitHub et dépendances opérationnelles, sans démarrer le Lot 3 tant que le Go Lot 2 n'est pas obtenu.
