# Durée de conservation et procédure de purge

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date** : 2026-05-23  
**Conformité** : Art. 5.1.e RGPD — limitation de la conservation

---

## 1. Durées de conservation

| Catégorie de données                                        | Durée de conservation                                             | Point de départ    | Justification                                                                  |
| ----------------------------------------------------------- | ----------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------ |
| **Tickets pseudonymisés en PostgreSQL**                     | **J+7 post-soutenance maximum**                                   | Date de soutenance | Usage limité à l'évaluation académique et purge rapide après démonstration     |
| **Logs de prédiction** (scores, ids pseudonymes, timestamp) | **J+7 post-soutenance maximum**                                   | Date de soutenance | Traçabilité sans texte brut, secret, email, nom, téléphone ni détail de ticket |
| **Données brutes HaloPSA** (avant transformation)           | **Non persistées** ; 24h maximum uniquement en incident documenté | Date d'extraction  | Transformation immédiate ; purge obligatoire de tout résidu temporaire         |
| **Modèle ML sérialisé** (joblib)                            | **J+7 post-soutenance maximum si entraîné sur données réelles**   | Date de soutenance | Artefact dérivé des tickets, donc inclus dans la purge                         |
| **Jeux de données ML** (train/test/val)                     | **J+7 post-soutenance maximum**                                   | Date de soutenance | Datasets pseudonymisés mais non anonymes                                       |
| **Backups, dumps, volumes Docker, exports, caches**         | **J+7 post-soutenance maximum**                                   | Date de soutenance | Toute copie ou dérivé des données est inclus dans la purge                     |
| **Mémoire PDF et annexes**                                  | **Permanent** (anonymisé)                                         | Dépôt mémoire      | Engagement académique — vérifier absence totale de PII avant dépôt             |
| **Journal des purges**                                      | **2 ans post-soutenance**                                         | Date de purge      | Preuve de conformité pour tout audit ultérieur (Art. 5.2 — Responsabilité)     |

---

## 2. Procédure de purge — post-soutenance (octobre 2026)

### 2.1 Calendrier

| Étape                | Date butoir   | Action                                                          |
| -------------------- | ------------- | --------------------------------------------------------------- |
| Jalon mémoire        | 2026-09-01    | Vérification qu'aucune PII n'est dans le mémoire ou les annexes |
| Soutenance           | Octobre 2026  | Dernière utilisation des données de production                  |
| J+7 post-soutenance  | Octobre 2026  | Exécution de la purge complète                                  |
| J+30 post-soutenance | Novembre 2026 | Attestation de purge signée                                     |

### 2.2 Périmètre de la purge

Toutes les données suivantes sont définitivement supprimées :

- [ ] Base PostgreSQL `halopsa_tickets` : `DROP DATABASE` ou `TRUNCATE` toutes les tables
- [ ] Fichiers de cache/computed : `ml/data/raw/`, `ml/data/processed/`, `ml/models/`
- [ ] Logs d'extraction : tout fichier contenant des données HaloPSA brutes
- [ ] Logs de prédiction : `predictions_logs` table
- [ ] Artefacts ML : modèles joblib, vectorizers, encoders
- [ ] Backups, dumps SQL, exports CSV/JSON, volumes Docker, caches applicatifs et fichiers temporaires
- [ ] Jeux de données train/test/validation et tout dérivé contenant des identifiants pseudonymes

### 2.3 Ce qui est conservé après purge

- Le code source (backend, frontend, ml) — sous réserve de contrôle d'absence de PII, secrets et données réelles
- Les fichiers de documentation (registre, stratégie, etc.) — sous réserve qu'ils ne contiennent aucune PII ni secret
- Les métriques et rapports d'évaluation — valeurs agrégées
- Les captures d'écran du dashboard — vérifiées sans PII
- Le journal de purge — preuve documentaire

### 2.4 Modalités de purge — sans code applicatif

La purge doit être exécutée selon une procédure opératoire validée, sans intégrer de code applicatif dans ce document. Elle doit couvrir : base PostgreSQL, datasets, modèles, logs, backups, dumps, volumes Docker, exports, caches et fichiers temporaires. Le journal de purge ne doit contenir aucune donnée sensible : uniquement date, périmètre purgé, responsable, résultat, anomalies éventuelles et référence de preuve.

---

## 3. Engagement de suppression — mention mémoire

Le mémoire devra contenir un engagement écrit similaire à :

> **Engagement de suppression des données**
>
> Conformément à l'article 5.1.e du RGPD, l'ensemble des données extraites de l'API HaloPSA dans le cadre du projet SYNAPPSE sont conservées au maximum jusqu'à J+7 post-soutenance.
>
> Une purge complète est exécutée dans les 7 jours suivant la soutenance :
>
> - Suppression de la base PostgreSQL contenant les tickets pseudonymisés
> - Suppression des artefacts modèles et jeux de données
> - Suppression de tous les logs contenant des données de production
>
> Seul le code source et la documentation technique (exempts de PII) sont conservés à titre de preuve académique.
>
> Le journal de purge est conservé comme preuve documentaire uniquement s'il ne contient aucune donnée sensible, aucun secret et aucun identifiant réel ou pseudonyme exploitable.

---

## 4. Surveillance et application

| Mécanisme                                         | Responsable     | Fréquence                          |
| ------------------------------------------------- | --------------- | ---------------------------------- |
| Vérification des durées de conservation           | Compliance Lead | Mensuelle                          |
| Alerte de purge post-soutenance                   | Scrum Master    | Jalon dédié dans le backlog        |
| Mise à jour du registre de traitement             | Compliance Lead | Après chaque modification de durée |
| Vérification d'absence de données brutes dans Git | DevOps Engineer | À chaque PR                        |

---

## 5. Références

- Registre de traitement : `registre-traitement.md` (section 7)
- Art. 5.1.e RGPD — Limitation de la conservation
- Art. 17 RGPD — Droit à l'effacement
- Art. 5.2 RGPD — Responsabilité (comptes rendus de purge)
