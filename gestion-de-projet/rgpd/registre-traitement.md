# Registre de traitement — Art. 30 RGPD

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date de création** : 2026-05-23  
**Version** : 1.0  
**Responsable de traitement** : Tony BESSEAU (SYNAPPSE — RNCP 37137)

---

## 1. Identité du responsable de traitement

| Champ | Valeur |
|---|---|
| Nom du responsable | SYNAPPSE / Tony BESSEAU |
| Statut | Personne physique dans le cadre d'un projet RNCP 37137 |
| Finalité principale | Détection automatique de tickets HaloPSA redondants |
| Contexte | Projet académique — auto-hébergé, aucun transfert commercial |

## 2. Finalité et base légale

| Champ | Valeur |
|---|---|
| Finalité détaillée | Détection et alerte des techniciens IT sur les tickets support redondants au sein d'un même client ESSMS |
| Base légale | Intérêt légitime (Art. 6.1.f RGPD) — optimisation du traitement des tickets support IT, réduction des doublons, amélioration de la qualité de service |
| Justification de l'intérêt légitime | Les données traitées sont limitées aux informations professionnelles IT. Les personnes concernées sont des contacts techniques professionnels. L'impact sur leurs droits et libertés est minimal grâce aux mesures de pseudonymisation et minimisation mises en œuvre. |

## 3. Catégories de personnes concernées

| Catégorie | Description |
|---|---|
| Contacts IT des ESSMS clients | Techniciens, administrateurs systèmes, utilisateurs déclarant des incidents via HaloPSA |
| Techniciens support SYNAPPSE | Agents traitant les tickets (agent_id — pseudonymisé) |

## 4. Catégories de données traitées

| Catégorie | Données concernées | Sensibilité |
|---|---|---|
| Données d'identification technique | user_id (hashé), agent_id, client_id, site_id | Faible à modérée |
| Données de ticket | id, summary (nettoyé), details (tronqué + nettoyé) | Modérée |
| Données contextuelles | category_1/2/3, status_id, priority_id | Nulle |
| Données temporelles | dateoccurred, dateentered, dateclosed | Nulle |
| Données de liaison | tickettype_id | Nulle |

## 5. Destinataires des données

| Destinataire | Rôle | Justification |
|---|---|---|
| Base de données PostgreSQL locale | Stockage des tickets pseudonymisés | Traitement ML et API |
| Développeur / responsable projet | Accès à la base locale uniquement | Maintenance, extraction, debugging |
| Modèle ML (local) | Analyse automatique de similarité | Détection de redondance |
| Interface web (localhost) | Affichage des alertes | Technicien — décision finale |

> Aucun destinataire externe (société tierce, cloud, sous-traitant).

## 6. Transferts hors UE

| Point | Valeur |
|---|---|
| Transfert hors UE | Aucun |
| Hébergement | 100 % local — machine de développement / serveur local |
| Cloud externe | Aucun — ni stockage, ni traitement, ni sauvegarde |

## 7. Durées de conservation

| Donnée | Durée de conservation | Justification |
|---|---|---|
| Tickets pseudonymisés | 12 mois après extraction | Analyse ML, réentraînement, démonstration soutenance |
| Logs de prédiction | Durée du projet + archivage 6 mois | Traçabilité des alertes et audit conformité |
| Données brutes HaloPSA | 24h max avant pseudonymisation | Fenêtre de transformation imposée |
| Mémoire et annexes | Permanent (anonymisé) | Engagement académique — aucune PII dans le mémoire |
| Journal de suppression | 2 ans post-soutenance | Preuve de purge |

→ Voir fichier dédié : `conservation-purge.md`

## 8. Mesures techniques et organisationnelles (MTO)

| # | Mesure | Type | Détail |
|---|---|---|---|
| MTO-01 | Pseudonymisation user_id | Technique | SHA-256 avec sel local, non réversible |
| MTO-02 | Nettoyage summary/details | Technique | Regex suppression PII (noms, emails, téléphones, adresses) |
| MTO-03 | Troncature details | Technique | Limité à 2000 caractères |
| MTO-04 | Chiffrement PostgreSQL | Technique | Chiffrement au repos (file system) |
| MTO-05 | Accès PostgreSQL localhost | Technique | Pas d'exposition réseau — écoute locale uniquement |
| MTO-06 | Variables d'environnement | Technique | Credentials HaloPSA et base via `.env` jamais dans le code |
| MTO-07 | Exclusion Git | Organisationnelle | `.gitignore` bloque `.env`, `*.pkl`, `__pycache__/`, datasets bruts |
| MTO-08 | Minimisation dès l'extraction | Organisationnelle | Seuls les champs nécessaires sont collectés (voir `minimisation-donnees.md`) |
| MTO-09 | Registre de traitement | Organisationnelle | Présent document — tenu à jour |
| MTO-10 | Procédure de purge | Organisationnelle | Script `purge.py` exécuté post-soutenance |
| MTO-11 | Séparation des environnements | Organisationnelle | Développement local vs démonstration ; jamais de données réelles dans un dépôt public |

## 9. Registre des violations (Art. 33)

| Date | Description | Causes | Mesures prises | Notifié CNIL ? |
|---|---|---|---|---|
| N/A | Aucune violation à ce jour | — | — | Non |

> Engagement : toute violation sera notifiée à la CNIL sous 72h et documentée dans ce registre.

## 10. Validation

| Rôle | Nom | Date |
|---|---|---|
| Rédacteur | Compliance Lead (Montesquieu) | 2026-05-23 |
| Validateur | Scrum Master (Eisenhower) | À valider |
| Approbateur | PM (Napoleon) | À valider |

---

**Prochain examen** : 2026-06-15 (post-extraction réelle, pré-ML)
