# Domaine — RGPD & Conformité

## Qualification du traitement

| Champ                | Valeur                                                         |
| -------------------- | -------------------------------------------------------------- |
| Responsable          | SYNAPPSE — Tony BESSEAU                                        |
| Finalité             | Détection automatique de tickets redondants                    |
| Base légale          | Intérêt légitime (art. 6.1.f RGPD)                             |
| Données traitées     | Données professionnelles IT — pas de données de santé directes |
| Personnes concernées | Contacts IT des ESSMS clients                                  |
| Conservation         | Durée du projet + archivage 1 an post-soutenance               |
| Hébergement          | 100% local — aucune donnée vers le cloud                       |

## Champs sensibles identifiés

| Champ   | Sensibilité | Traitement prévu                 |
| ------- | ----------- | -------------------------------- |
| user_id | Élevée      | Pseudonymisation ou suppression  |
| details | Modérée     | Troncature 2000 car. + nettoyage |
| summary | Faible      | Nettoyage                        |

## Points de contrôle RGPD

| #     | Point                                              | Statut         |
| ----- | -------------------------------------------------- | -------------- |
| PC-01 | Base légale identifiée                             | ✓ Validé       |
| PC-02 | Dictionnaire de données classifié                  | ✓ Validé       |
| PC-03 | Credentials API en variables d'environnement       | ✓ Validé       |
| PC-04 | Troncature details à 2000 car.                     | ✓ Implémenté   |
| PC-05 | Pseudonymisation user_id                           | ⏳ À faire     |
| PC-06 | Nettoyage NLP du champ details                     | ⏳ À faire     |
| PC-07 | PostgreSQL accès localhost uniquement              | ⏳ À faire     |
| PC-08 | .gitignore excluant .env et credentials            | ⏳ À faire     |
| PC-09 | Absence de données personnelles dans dataset final | ⏳ À faire     |
| PC-10 | Mention RGPD dans l'application web                | ⏳ À faire     |
| PC-11 | Procédure de purge post-soutenance                 | ⏳ À planifier |

## Charte éthique — principes

| Principe           | Engagement                                                                 |
| ------------------ | -------------------------------------------------------------------------- |
| Transparence       | Algorithmes, features et métriques documentés. Score de confiance affiché. |
| Responsabilité     | Le modèle est un outil d'aide — la décision reste humaine                  |
| Intelligibilité    | Chaque prédiction expliquée simplement                                     |
| Fiabilité          | Évaluation sur jeu de test indépendant. Seuil minimal avant déploiement.   |
| Sécurité           | Architecture auto-hébergée. Accès restreint.                               |
| Non-discrimination | Distribution des prédictions analysée par client                           |
| Minimisation       | Seules les données nécessaires sont collectées (art. 5.1.c RGPD)           |
