# Stratégie de pseudonymisation

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date** : 2026-05-23  
**Version** : 1.1  
**Conformité** : Art. 4.5, Art. 5.1.c, Art. 32 RGPD — Recommandation CNIL pseudonymisation

---

## 1. Principes généraux

La pseudonymisation est appliquée **avant stockage en PostgreSQL** comme couche de protection immédiate.

| Principe       | Application                                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Déterministe   | Un même identifiant donne toujours le même pseudonyme avec le même secret → cardinalité préservée pour l'apprentissage ML |
| Non réversible | HMAC-SHA-256 avec secret local obligatoire — pas de fonction de déchiffrement possible                                    |
| Précoce        | Appliquée dès l'extraction, avant toute persistance                                                                       |
| Systématique   | Tous les `user_id` sont pseudonymisés ; `agent_id` est exclu ou pseudonymisé si conservation justifiée                    |
| Fail-closed    | Absence de secret, secret vide ou contrôle résiduel KO → pas de stockage                                                  |

---

## 2. Pseudonymisation de `user_id` et `agent_id` si retenu

### 2.1 Algorithme

Spécification documentaire, sans code applicatif :

| Élément    | Exigence                                                                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------------- |
| Algorithme | HMAC-SHA-256                                                                                                |
| Secret     | Secret local obligatoire, stocké hors dépôt, non vide, distinct des credentials API                         |
| Entrée     | Identifiant source normalisé en chaîne (`user_id` ; `agent_id` seulement si retenu)                         |
| Sortie     | Hexadécimal complet de 64 caractères recommandé ; troncature interdite sans analyse de collision documentée |
| Échec      | Si le secret est absent ou invalide, le traitement s'arrête avant stockage (`fail-closed`)                  |

### 2.3 Gestion du sel

| Propriété       | Valeur                                                                                                            |
| --------------- | ----------------------------------------------------------------------------------------------------------------- |
| Génération      | Secret aléatoire fort — une seule fois en local pour un jeu de données donné                                      |
| Stockage        | Variable d'environnement dédiée dans `.env` local ou secret manager équivalent                                    |
| Exclusion Git   | `.env` et tout fichier de secret doivent être couverts par `.gitignore`                                           |
| Rotation        | Obligatoire en cas de compromission suspectée ; recommandée à chaque ré-extraction complète                       |
| Compromission   | Purger les pseudonymes dérivés, générer un nouveau secret, recalculer les pseudonymes depuis une source autorisée |
| Perte du secret | Les pseudonymes deviennent non raccordables → ré-extraction ou recalcul nécessaire selon autorisation client      |

### 2.4 Impact ML

Le pseudonyme déterministe préserve les relations entre tickets d'un même `user_id`, ce qui est suffisant pour la détection de redondance sans connaître l'identité réelle. Cette protection reste une pseudonymisation, pas une anonymisation.

---

## 3. Nettoyage de `summary` et `details`

### 3.1 Règles de suppression

Les motifs suivants sont détectés par regex et remplacés par le token `[PII_REDACTED]` :

| #   | Motif                             | Regex                                            | Exemple                                     |
| --- | --------------------------------- | ------------------------------------------------ | ------------------------------------------- | --------------------------------------------------------------------- | ------------------------------ | ----- | ------ | ----- | ----- | ------------------- | ----------------------------------- |
| 1   | Adresse email                     | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | `jean.dupont@societe.fr` → `[PII_REDACTED]` |
| 2   | Numéro de téléphone FR            | `(?:0                                            | \+33)[1-9](?:[\s.-]?\d{2}){4}`              | `06 12 34 56 78` → `[PII_REDACTED]`                                   |
| 3   | Numéro de téléphone international | `\+\d{1,3}[\s.-]?\d{4,}`                         | `+33123456789` → `[PII_REDACTED]`           |
| 4   | Civilité + Nom                    | `(?:M\.                                          | Mme                                         | Mlle)\s+[A-Z][a-zéêèëàâäûüôöîïç]+(?:\s+[A-Z][a-zéêèëàâäûüôöîïç-]+)\*` | `M. Dupont` → `[PII_REDACTED]` |
| 5   | Adresse postale (mots-clés)       | `(?:rue                                          | avenue                                      | boulevard                                                             | impasse                        | allée | chemin | place | route | lotissement)\s+\S+` | `rue de la Paix` → `[PII_REDACTED]` |
| 6   | Code postal + ville               | `\d{5}\s*[A-Z][a-zéêèëàâäûüôöîïç]+`              | `75001 Paris` → `[PII_REDACTED]`            |
| 7   | IP locale ou publique             | `\b(?:\d{1,3}\.){3}\d{1,3}\b`                    | `192.168.1.1` → `[PII_REDACTED]`            |

### 3.2 Application

Le code applicatif n'est pas défini dans ce document. L'implémentation devra respecter les motifs ci-dessus, remplacer chaque occurrence par `[PII_REDACTED]`, puis exécuter un contrôle résiduel bloquant avant stockage.

### 3.3 Nettoyage NLP complémentaire

En complément des regex, une étape NER (Named Entity Recognition) avec spaCy peut être introduite pour détecter les noms de personnes non couverts par les motifs de civilité.

| Option            | Quand                       | Bénéfice                                  |
| ----------------- | --------------------------- | ----------------------------------------- |
| Regex seules      | Version initiale (Sprint 1) | Rapide, déterministe, sans dépendance NLP |
| Regex + spaCy NER | Sprint 2 (avant ML)         | Couverture plus large des entités nommées |

---

## 4. Troncature de `details`

Le champ `details` peut contenir de très longs textes (plusieurs pages HTML). Pour limiter l'exposition :

- Longueur maximale après extraction : **2000 caractères** (UTF-8)
- La troncature est appliquée **avant** le nettoyage regex

La troncature et le nettoyage doivent être réalisés avant persistance ; aucun extrait brut ne doit être écrit dans des logs, dumps ou fichiers temporaires persistants.

---

## 5. Pipeline complet de pseudonymisation

```
[Données brutes HaloPSA]
    │
    ├─── user_id  →  HMAC-SHA-256(secret, user_id)  →  [user_id_pseudo]
    ├─── agent_id →  exclu OU HMAC-SHA-256(secret, agent_id) si justifié
    │
    ├─── summary  →  troncature? (déjà court)  →  nettoyage regex  →  [summary_propre]
    │
    ├─── details  →  troncature 2000 car.  →  nettoyage regex  →  [details_propre]
    │
    ├─── autres champs  →  inchangés (non sensibles)
    │
    ▼
[Stockage PostgreSQL]
```

## 5.1 Contrôle résiduel et échec sécurisé

| Contrôle                                              | Exigence                                                       |
| ----------------------------------------------------- | -------------------------------------------------------------- |
| Secret absent ou vide                                 | Arrêt du traitement avant toute persistance                    |
| PII résiduelle détectée après nettoyage               | Ticket non stocké et événement journalisé sans valeur sensible |
| Donnée brute détectée dans cache, export, dump ou log | Purge immédiate et incident documenté                          |
| Longueur de hash non conforme                         | Rejet du lot jusqu'à correction                                |

---

## 6. Tests de validation

| Test                                     | Attendu                     | Méthode                                             |
| ---------------------------------------- | --------------------------- | --------------------------------------------------- |
| Même user_id → même pseudonyme           | Vrai                        | Contrôle déterministe avec même secret              |
| user_id différent → pseudonyme différent | Vrai                        | Contrôle sur deux identifiants distincts            |
| Longueur HMAC conforme                   | 64 caractères hexadécimaux  | Troncature interdite sans analyse documentée        |
| Nettoyage email dans summary             | `[PII_REDACTED]`            | Regex sur `"Contacter jean@test.fr"`                |
| Nettoyage téléphone dans details         | `[PII_REDACTED]`            | Regex sur `"Tél : 06 12 34 56 78"`                  |
| Troncature details > 2000 car.           | Max 2000 car.               | Chaîne artificielle de 5000 car. → doit être coupée |
| Token PII non présent après nettoyage    | Pas de pattern PII résiduel | Nouvelle passe de regex sur le résultat             |

---

## 7. Références

- Registre de traitement : `registre-traitement.md`
- Cartographie des champs : `cartographie-champs.md`
- Minimisation des données : `minimisation-donnees.md`
- CNIL — Guide de la pseudonymisation : https://www.cnil.fr/fr/pseudonymisation
