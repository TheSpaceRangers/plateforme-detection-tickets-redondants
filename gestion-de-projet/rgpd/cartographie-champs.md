# Cartographie des champs HaloPSA → PII

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date** : 2026-05-23  
**Source** : `domain/halopsa.md` (audit API) + `domain/rgpd.md` (qualification RGPD)  
**Référence** : Registre de traitement Art. 30 — section 4

---

## 1. Périmètre audité

Endpoint HaloPSA concerné : **GET /api/Tickets** et **GET /api/Tickets/{id}**

Seuls ces deux endpoints sont nécessaires à la détection de redondance.

> Les endpoints `/api/Users`, `/api/Client/{id}` (détail), `/api/Site` sont exclus — non pertinents et/ou porteurs de PII superflues.

---

## 2. Cartographie champ par champ

| #   | Champ           | Type          | Description                       | Contient des PII ? | Type de PII                                                                  | Mesure de protection                                                         |
| --- | --------------- | ------------- | --------------------------------- | ------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 1   | `id`            | Integer       | Identifiant unique du ticket      | **Non**            | —                                                                            | Aucune — identifiant technique                                               |
| 2   | `summary`       | String        | Titre / objet du ticket           | **Partiel**        | Nom, prénom, email possibles dans le libellé                                 | Nettoyage regex PII avant stockage                                           |
| 3   | `details`       | String (long) | Description longue de l'incident  | **Oui**            | Noms, emails, téléphones, adresses IP, noms de machines, identifiants locaux | Troncature 2000 car. + nettoyage regex PII                                   |
| 4   | `client_id`     | Integer       | Identifiant du client ESSMS       | **Non**            | —                                                                            | Aucune — donnée agrégée                                                      |
| 5   | `site_id`       | Integer       | Identifiant du site client        | **Non**            | —                                                                            | Aucune — donnée agrégée                                                      |
| 6   | `user_id`       | Integer       | Identifiant du contact demandeur  | **Oui**            | Identifiant interne → lien possible avec personne physique                   | Pseudonymisation HMAC-SHA-256 avant stockage                                 |
| 7   | `agent_id`      | Integer       | Identifiant du technicien assigné | **Oui**            | Identifiant interne d'un professionnel identifiable                          | Exclu par défaut ; pseudonymisation HMAC-SHA-256 si nécessité métier validée |
| 8   | `tickettype_id` | Integer       | Type de ticket                    | **Non**            | —                                                                            | Aucune                                                                       |
| 9   | `category_1`    | String        | Catégorie niveau 1                | **Non**            | —                                                                            | Aucune                                                                       |
| 10  | `category_2`    | String        | Catégorie niveau 2                | **Non**            | —                                                                            | Aucune                                                                       |
| 11  | `category_3`    | String        | Catégorie niveau 3                | **Non**            | —                                                                            | Aucune                                                                       |
| 12  | `dateoccurred`  | DateTime      | Date d'occurrence                 | **Non**            | —                                                                            | Aucune                                                                       |
| 13  | `dateentered`   | DateTime      | Date de saisie                    | **Non**            | —                                                                            | Aucune                                                                       |
| 14  | `dateclosed`    | DateTime      | Date de clôture                   | **Non**            | —                                                                            | Aucune                                                                       |
| 15  | `status_id`     | Integer       | Statut du ticket                  | **Non**            | —                                                                            | Aucune                                                                       |
| 16  | `priority_id`   | Integer       | Priorité                          | **Non**            | —                                                                            | Aucune                                                                       |

---

## 3. Légende des sensibilités

| Sensibilité | Définition                                     | Action requise                  |
| ----------- | ---------------------------------------------- | ------------------------------- |
| **Nulle**   | Aucune donnée personnelle                      | Stockage direct                 |
| **Faible**  | Donnée contextuelle non nominative             | Stockage sans transformation    |
| **Partiel** | Peut occasionnellement contenir des PII        | Nettoyage conditionnel          |
| **Élevée**  | PII avérées ou lien possible avec une personne | Pseudonymisation ou suppression |

---

## 4. Champs à pseudonymiser / nettoyer / tronquer

### 4.1 Pseudonymisation obligatoire

| Champ      | Méthode                        | Détail                                                                                     |
| ---------- | ------------------------------ | ------------------------------------------------------------------------------------------ |
| `user_id`  | HMAC-SHA-256 avec secret local | Déterministe, pseudonyme, non réversible sans secret. Voir `strategie-pseudonymisation.md` |
| `agent_id` | Exclusion ou HMAC-SHA-256      | Exclu par défaut ; même protection que `user_id` si conservation indispensable             |

### 4.2 Nettoyage obligatoire

| Champ     | Méthode                                         | Détail                                                                 |
| --------- | ----------------------------------------------- | ---------------------------------------------------------------------- |
| `summary` | Regex de suppression PII                        | Noms, prénoms, emails, téléphones remplacés par token `[PII_REDACTED]` |
| `details` | Regex de suppression PII + troncature 2000 car. | Mêmes règles + limite de taille                                        |

### 4.3 Exclusion (non collectés)

| Champ          | Raison                                                                                 |
| -------------- | -------------------------------------------------------------------------------------- |
| `user_name`    | Non fourni par l'endpoint Tickets — serait PII directe                                 |
| `user_email`   | Non fourni par l'endpoint — PII directe                                                |
| `client_name`  | Non nécessaire à la détection de redondance                                            |
| `site_name`    | Non nécessaire                                                                         |
| `agent_name`   | Non nécessaire                                                                         |
| `agent_id`     | Exclu par défaut si aucune fonctionnalité validée ne requiert l'affectation technicien |
| Notes internes | Non exposées par l'endpoint Tickets                                                    |

---

## 5. Flux de transformation des données

```
HaloPSA API                        PostgreSQL (pseudonymisé)
    │                                      │
    │ GET /api/Tickets                     │
    │ GET /api/Tickets/{id}                │
    ▼                                      │
[Extraction brute]                         │
    │                                      │
    ▼                                      │
[Troncature details → 2000 car.]           │
    │                                      │
    ▼                                      │
[Nettoyage summary + details]              │
    │  regex PII                           │
    ▼                                      │
[Pseudonymisation user_id / agent_id si retenu]
    │  HMAC-SHA-256(secret, identifiant)   │
    ▼                                      │
[Stockage PostgreSQL] ──────────────────────┘
    │
    ▼
[Pipeline ML / API / UI]
    │  Données pseudonymisées, non anonymisées
    ▼
[Utilisation exploitation]
```

## 5.1 Contrôle résiduel avant stockage

- Le nettoyage PII de `summary` et `details` est appliqué avant toute persistance.
- Une passe de contrôle résiduel doit vérifier l'absence d'emails, téléphones, adresses, IP et noms évidents après nettoyage.
- Tout échec de contrôle bloque le stockage du ticket concerné (`fail-closed`).
- La pseudonymisation réduit le risque d'identification mais ne constitue pas une anonymisation RGPD : les données restent personnelles tant qu'une ré-identification indirecte est possible.

---

## 6. Références croisées

| Document                      | Référence                             |
| ----------------------------- | ------------------------------------- |
| Stratégie de pseudonymisation | `strategie-pseudonymisation.md`       |
| Minimisation des données      | `minimisation-donnees.md`             |
| Registre de traitement        | `registre-traitement.md`              |
| Conservation et purge         | `conservation-purge.md`               |
| Audit API HaloPSA             | `.opencode/context/domain/halopsa.md` |
| Qualification RGPD            | `.opencode/context/domain/rgpd.md`    |
