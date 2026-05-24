# Registre de traitement — Art. 30 RGPD

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date de création** : 2026-05-23  
**Version** : 1.1  
**Responsable de traitement** : Tony BESSEAU (SYNAPPSE — RNCP 37137)

---

## 1. Identité du responsable de traitement

| Champ               | Valeur                                                       |
| ------------------- | ------------------------------------------------------------ |
| Nom du responsable  | SYNAPPSE / Tony BESSEAU                                      |
| Statut              | Personne physique dans le cadre d'un projet RNCP 37137       |
| Finalité principale | Détection automatique de tickets HaloPSA redondants          |
| Contexte            | Projet académique — auto-hébergé, aucun transfert commercial |

## 1.1 Rôles RGPD, autorisation client et sous-traitance HaloPSA

| Acteur                          | Qualification RGPD                                         | Statut / exigence                                                                                                 |
| ------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| SYNAPPSE / Tony BESSEAU         | Responsable de traitement du traitement académique local   | Détermine les finalités et moyens du prototype de détection de tickets redondants                                 |
| Client ESSMS source des tickets | Responsable de traitement initial dans HaloPSA             | Autorisation écrite requise avant toute extraction réelle de tickets                                              |
| HaloPSA                         | Sous-traitant du client ESSMS pour la plateforme ticketing | DPA HaloPSA à obtenir ou référencer avant extraction réelle ; aucune conformité présumée sans preuve documentaire |

> Condition préalable : aucune extraction réelle HaloPSA ne doit être réalisée tant que l'autorisation client et la référence au DPA HaloPSA ne sont pas documentées.

## 2. Finalité et base légale

| Champ                               | Valeur                                                                                                                                                                                                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Finalité détaillée                  | Détection et alerte des techniciens IT sur les tickets support redondants au sein d'un même client ESSMS                                                                                                                                                          |
| Base légale                         | Intérêt légitime (Art. 6.1.f RGPD) — optimisation du traitement des tickets support IT, réduction des doublons, amélioration de la qualité de service                                                                                                             |
| Justification de l'intérêt légitime | Les données visées sont limitées aux informations professionnelles IT nécessaires. Les personnes concernées sont des contacts techniques professionnels. L'impact doit rester limité par la minimisation, la pseudonymisation et le nettoyage PII avant stockage. |

### 2.1 Test d'intérêt légitime — Art. 6.1.f RGPD

| Étape             | Analyse                                                                                                                                          | Conclusion                                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| Finalité légitime | Réduire les doublons de tickets et améliorer la qualité du support IT pour un périmètre ESSMS déterminé                                          | Finalité légitime documentée                                                                                  |
| Nécessité         | Seuls les champs nécessaires à la détection de redondance sont retenus ; les données directement nominatives sont exclues                        | Nécessité conditionnée au respect de la minimisation                                                          |
| Mise en balance   | Les personnes concernées sont des professionnels ; les risques principaux portent sur les identifiants et textes libres pouvant contenir des PII | Acceptable uniquement avec pseudonymisation, nettoyage PII, contrôle résiduel et absence de diffusion externe |
| Garanties         | Pseudonymisation `user_id`, exclusion ou pseudonymisation `agent_id`, nettoyage `summary/details`, conservation limitée, contrôle Git/secrets    | Garanties à vérifier avant extraction réelle                                                                  |

## 3. Catégories de personnes concernées

| Catégorie                     | Description                                                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Contacts IT des ESSMS clients | Techniciens, administrateurs systèmes, utilisateurs déclarant des incidents via HaloPSA                            |
| Techniciens support SYNAPPSE  | Agents traitant les tickets (`agent_id` exclu par défaut ; pseudonymisé uniquement si nécessité métier documentée) |

## 4. Catégories de données traitées

| Catégorie                          | Données concernées                                                                                   | Sensibilité      |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------- |
| Données d'identification technique | user_id pseudonymisé, agent_id exclu par défaut ou pseudonymisé si indispensable, client_id, site_id | Faible à modérée |
| Données de ticket                  | id, summary (nettoyé), details (tronqué + nettoyé)                                                   | Modérée          |
| Données contextuelles              | category_1/2/3, status_id, priority_id                                                               | Nulle            |
| Données temporelles                | dateoccurred, dateentered, dateclosed                                                                | Nulle            |
| Données de liaison                 | tickettype_id                                                                                        | Nulle            |

## 5. Destinataires des données

| Destinataire                      | Rôle                               | Justification                      |
| --------------------------------- | ---------------------------------- | ---------------------------------- |
| Base de données PostgreSQL locale | Stockage des tickets pseudonymisés | Traitement ML et API               |
| Développeur / responsable projet  | Accès à la base locale uniquement  | Maintenance, extraction, debugging |
| Modèle ML (local)                 | Analyse automatique de similarité  | Détection de redondance            |
| Interface web (localhost)         | Affichage des alertes              | Technicien — décision finale       |

> Aucun destinataire externe du traitement local (société tierce, cloud, nouveau sous-traitant). HaloPSA reste le sous-traitant de la plateforme source du client et son DPA doit être référencé avant extraction.

## 6. Transferts hors UE

| Point             | Valeur                                                 |
| ----------------- | ------------------------------------------------------ |
| Transfert hors UE | Aucun                                                  |
| Hébergement       | 100 % local — machine de développement / serveur local |
| Cloud externe     | Aucun — ni stockage, ni traitement, ni sauvegarde      |

## 7. Durées de conservation

| Donnée                                                  | Durée de conservation                                                                       | Justification                                                             |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Tickets pseudonymisés                                   | Jusqu'à J+7 post-soutenance maximum                                                         | Analyse ML, démonstration soutenance, purge rapide après usage académique |
| Logs de prédiction                                      | Jusqu'à J+7 post-soutenance maximum                                                         | Traçabilité des alertes sans texte brut ni PII                            |
| Données brutes HaloPSA                                  | Non persistées ; mémoire temporaire uniquement, 24h maximum si incident technique documenté | Fenêtre de transformation exceptionnelle                                  |
| Datasets / modèles / exports / caches / volumes / dumps | Jusqu'à J+7 post-soutenance maximum                                                         | Purge coordonnée de tous les artefacts contenant ou dérivant des tickets  |
| Mémoire et annexes                                      | Permanent (anonymisé)                                                                       | Engagement académique — aucune PII dans le mémoire                        |
| Journal de suppression                                  | 2 ans post-soutenance                                                                       | Preuve de purge                                                           |

→ Voir fichier dédié : `conservation-purge.md`

## 8. Mesures techniques et organisationnelles (MTO)

| #      | Mesure                                       | Type              | Détail                                                                                                        |
| ------ | -------------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------- |
| MTO-01 | Pseudonymisation user_id                     | Technique         | HMAC-SHA-256 avec secret local obligatoire, non réversible sans secret                                        |
| MTO-02 | Nettoyage summary/details                    | Technique         | Regex suppression PII (noms, emails, téléphones, adresses)                                                    |
| MTO-03 | Troncature details                           | Technique         | Limité à 2000 caractères                                                                                      |
| MTO-04 | Chiffrement PostgreSQL                       | Technique         | Chiffrement au repos (file system)                                                                            |
| MTO-05 | Accès PostgreSQL localhost                   | Technique         | Pas d'exposition réseau — écoute locale uniquement                                                            |
| MTO-06 | Variables d'environnement                    | Technique         | Credentials HaloPSA, base et secret HMAC via `.env` ; aucun secret dans le code ou la documentation           |
| MTO-07 | Exclusion Git                                | Organisationnelle | `.gitignore` doit bloquer `.env`, artefacts ML, datasets bruts, dumps, exports, caches et volumes locaux      |
| MTO-08 | Minimisation dès l'extraction                | Organisationnelle | Seuls les champs nécessaires sont collectés (voir `minimisation-donnees.md`)                                  |
| MTO-09 | Registre de traitement                       | Organisationnelle | Présent document — tenu à jour                                                                                |
| MTO-10 | Procédure de purge                           | Organisationnelle | Procédure opératoire de purge exécutée à J+7 post-soutenance maximum, sans données sensibles dans le journal  |
| MTO-11 | Séparation des environnements                | Organisationnelle | Développement local vs démonstration ; jamais de données réelles dans un dépôt public                         |
| MTO-12 | Contrôle préalable secrets / données réelles | Organisationnelle | Absence de secrets et de données réelles HaloPSA à prouver avant extraction, avant commit et avant soutenance |

## 9. Registre des violations (Art. 33)

| Date | Description                | Causes | Mesures prises | Notifié CNIL ? |
| ---- | -------------------------- | ------ | -------------- | -------------- |
| N/A  | Aucune violation à ce jour | —      | —              | Non            |

> Engagement : toute violation sera notifiée à la CNIL sous 72h et documentée dans ce registre.

## 10. Validation

| Rôle        | Nom                           | Date       |
| ----------- | ----------------------------- | ---------- |
| Rédacteur   | Compliance Lead (Montesquieu) | 2026-05-23 |
| Validateur  | Scrum Master (Eisenhower)     | À valider  |
| Approbateur | PM (Napoleon)                 | À valider  |

---

**Prochain examen** : 2026-06-15 (post-extraction réelle, pré-ML)
