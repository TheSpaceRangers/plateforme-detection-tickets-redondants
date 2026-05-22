# Projet — Planning et jalons

## Planning prévisionnel

| Période             | Lot                 | Contenu                                                          |
| ------------------- | ------------------- | ---------------------------------------------------------------- |
| Mars — Avril 2026   | Lot 1 — Cadrage     | Note de cadrage, audit API, dictionnaire données, RGPD, veille ✓ |
| Avril — Mai 2026    | Lot 2 — Données     | Extraction API, nettoyage NLP, chargement PostgreSQL, EDA        |
| Mai — Juin 2026     | Lot 3 — Modèle ML   | Feature engineering, labellisation, entraînement, Grid Search    |
| Juin — Juillet 2026 | Lot 4 — Application | FastAPI + Vite/React, dashboard, déploiement local, tests        |
| Juillet — Août 2026 | Lot 5 — Mémoire     | Rédaction, intégration livrables, relecture finale               |

## Jalons clés

| Date               | Jalon                          |
| ------------------ | ------------------------------ |
| 1er septembre 2026 | 🚩 Dépôt du mémoire PDF        |
| Octobre 2026       | 🎓 Soutenance orale RNCP 37137 |

## Contrainte RNCP Bloc 3 — non négociable

Les exigences suivantes guident tous les choix techniques :

- 4 algorithmes supervisés : KNN, Random Forest, Decision Tree, Logistic Regression
- Train/test split ≥ 70/30
- Métriques : Accuracy (obligatoire), F1, Recall
- Grid Search obligatoire
- Application web intégrant le modèle
