# Domaine — HaloPSA

## Instance

| Champ          | Valeur                                  |
| -------------- | --------------------------------------- |
| Instance       | <tenant>.halopsa.com             |
| URL base API   | https://<tenant>.halopsa.com/api |
| Auth           | OAuth2 — grant_type: client_credentials |
| Token endpoint | POST /auth/token (scope: all)           |
| Format         | JSON                                    |
| Pagination     | pageinate=true, page_size, page_no      |

## Endpoints disponibles

| Endpoint              | Description                            | Pertinence         |
| --------------------- | -------------------------------------- | ------------------ |
| GET /api/Tickets      | Liste paginée des tickets              | ★★★ Critique       |
| GET /api/Tickets/{id} | Détail complet d'un ticket             | ★★★ Critique       |
| GET /api/Client       | Référentiel des clients ESSMS          | ★★☆ Important      |
| GET /api/Client/{id}  | Détail d'un client                     | ★☆☆ Secondaire     |
| GET /api/Category     | Référentiel des catégories (3 niveaux) | ★★★ Critique       |
| GET /api/Site         | Sites rattachés à un client            | ★☆☆ Secondaire     |
| GET /api/Users        | Utilisateurs / contacts clients        | Non utilisé — RGPD |

## Champs disponibles dans GET /api/Tickets/{id}

| Champ         | Type          | Description                       | Sensibilité RGPD |
| ------------- | ------------- | --------------------------------- | ---------------- |
| id            | Integer       | Identifiant unique du ticket      | Nulle            |
| summary       | String        | Titre court du ticket             | Faible           |
| details       | String (long) | Description longue de l'incident  | Modérée          |
| client_id     | Integer       | Identifiant du client             | Faible           |
| site_id       | Integer       | Identifiant du site client        | Faible           |
| user_id       | Integer       | Identifiant du contact demandeur  | Élevée           |
| agent_id      | Integer       | Identifiant du technicien assigné | Faible           |
| tickettype_id | Integer       | Type de ticket                    | Nulle            |
| category_1    | String        | Catégorie niveau 1                | Nulle            |
| category_2    | String        | Catégorie niveau 2                | Nulle            |
| category_3    | String        | Catégorie niveau 3                | Nulle            |
| dateoccurred  | DateTime      | Date d'occurrence                 | Nulle            |
| dateentered   | DateTime      | Date de saisie                    | Nulle            |
| dateclosed    | DateTime      | Date de clôture (null si ouvert)  | Nulle            |
| status_id     | Integer       | Statut du ticket                  | Nulle            |
| priority_id   | Integer       | Priorité                          | Nulle            |

## Points de vigilance

| Point                   | Description                                                             |
| ----------------------- | ----------------------------------------------------------------------- |
| Expiration token        | Bearer token expire après ~3600s                                        |
| Rate limiting           | L'API peut limiter le nombre de requêtes par seconde                    |
| Champs manquants        | Certains tickets anciens ont summary ou category vides                  |
| Données personnelles    | Le champ details peut contenir des noms, emails, informations sensibles |
| Pagination              | Arrêter quand une page vide est retournée                               |
| Déséquilibre de classes | Les tickets redondants sont minoritaires dans l'historique              |
