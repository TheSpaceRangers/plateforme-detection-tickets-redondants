# Sprint 1 — Rapport initial opérationnel

**Date** : 2026-05-22  
**Objectif** : sécuriser le socle projet et transformer le cadrage en backlog exécutable.  
**Jalon visé** : `2026-05-31 — Socle données exploitable pour ML`.

## 1. État des lieux observé

### Présent dans le dépôt

- `gestion-de-projet/STATUS.md` : roadmap, sprint courant, contraintes RNCP, risques initiaux.
- `.opencode/context/domain/halopsa.md` : audit API HaloPSA, endpoints, champs, sensibilités et points de vigilance.
- `.opencode/context/domain/rgpd.md` : qualification du traitement, base légale, champs sensibles, points de contrôle RGPD.
- `.opencode/context/technical/architecture.md` : architecture cible, tables PostgreSQL, variables d'environnement attendues.
- `.opencode/context/project/planning.md` : planning lots et contraintes RNCP Bloc 3.
- `.env.example` présents dans `ml/`, `backend/`, `frontend/`.
- `README.md` : installation, variables d'environnement, structure projet, commandes prévues.

### Manquant ou à confirmer

- `gestion-de-projet/backlog.md` était absent avant Sprint 1 ; créé dans ce sprint.
- Dossier `gestion-de-projet/sprints/` absent avant Sprint 1 ; créé pour le suivi.
- Livrables Lot 1 annoncés terminés mais non matérialisés dans `gestion-de-projet/` sous forme de note de cadrage, dictionnaire de données, registre RGPD ou veille dédiée.
- Lot 2 annoncé en cours, mais extraction API, nettoyage NLP, chargement PostgreSQL et EDA ne sont pas confirmés par des livrables opérationnels observés.
- Structure technique cible documentée, mais l'existence effective des modules `ml/src`, `backend/app`, `frontend/src`, `docker-compose.yml`, scripts d'extraction et schémas PostgreSQL reste à confirmer par le tech-lead.

## 2. Analyse opérationnelle

### Réalisé

- Cadrage produit synthétisé.
- Roadmap et contraintes RNCP explicites.
- Audit API HaloPSA documenté au niveau fonctionnel.
- Points RGPD majeurs identifiés : `user_id`, `details`, `summary`.
- Règle secrets via `.env` posée.
- Backlog Sprint 1 et backlog Lot 2 → Lot 3 structurés.

### Manquant critique

- Preuve d'un dataset ML exploitable.
- Preuve d'une extraction HaloPSA testée et conforme.
- Preuve du nettoyage/pseudonymisation avant stockage.
- Critères qualité dataset formellement validés par tech-lead et compliance-lead.
- Feu vert conformité avant extraction réelle.

### Risques

| Risque | Niveau | Impact | Réponse Sprint 1 |
| --- | --- | --- | --- |
| Lot 2 incomplet au 2026-05-22 | Élevé | Décalage Lot 3 ML | Prioriser US-DATA-001/002 |
| Données personnelles dans `details` ou `user_id` | Élevé | Non-conformité RGPD | Bloquer extraction réelle tant que US-GOV-001 non validée |
| Labels redondance absents | Élevé | Entraînement supervisé impossible | Exiger stratégie de labellisation avant Lot 3 |
| Secrets API HaloPSA exposés | Élevé | Incident sécurité | DevOps + Compliance vérifient `.gitignore`, exemples et workflow |
| Contraintes RNCP non intégrées tôt | Moyen | Rework ML | Critères Lot 3 imposent 4 modèles, split, métriques, Grid Search |

## 3. Sprint Backlog assignable

| US | Objectif | Lead(s) | Priorité | Statut |
| --- | --- | --- | --- | --- |
| US-PM-001 | Confirmer état réel Lot 1/Lot 2 | tech-lead, compliance-lead | P0 | À lancer |
| US-PM-002 | Structurer backlog par lots/priorités | scrum-master, devops-engineer | P0 | En cours |
| US-DATA-001 | Valider stratégie extraction HaloPSA | tech-lead, compliance-lead | P0 | À lancer |
| US-DATA-002 | Définir critères dataset ML | tech-lead, compliance-lead | P0 | À lancer |
| US-GOV-001 | Vérifier garde-fous RGPD/sécurité | compliance-lead, devops-engineer | P0 | À lancer |

## 4. Critères d'entrée Lot 3 ML

- Dataset local disponible et non versionné dans Git.
- Schéma documenté : ticket, client pseudonymisé, texte nettoyé/tronqué, catégories, dates, statut, priorité, label.
- Données personnelles supprimées, pseudonymisées ou minimisées selon validation conformité.
- Labels redondant / non-redondant disponibles ou protocole de labellisation validé.
- Rapport qualité : valeurs manquantes, doublons, distribution par client/catégorie/statut, déséquilibre de classes.
- Baseline ML définie avant optimisation.
- Protocole RNCP : KNN, Random Forest, Decision Tree, Logistic Regression ; split ≥ 70/30 ; Accuracy, F1, Recall ; Grid Search.
- Sortie attendue compatible application : score de confiance + explication technicien.

## 5. Décision Scrum Master

- Sprint 1 est lancé comme sprint de sécurisation, pas comme sprint d'implémentation lourde.
- Toute extraction réelle HaloPSA reste bloquée jusqu'au retour conformité US-GOV-001.
- Lot 3 ML ne doit pas démarrer tant que US-DATA-002 n'est pas validée.

## 6. Briefs leads

### Tech Lead — Turing

Contexte : sécuriser Lot 2 Données avant bascule ML.  
Critères d'acceptation : confirmer livrables techniques, stratégie extraction, schéma dataset, labels, critères qualité.  
Definition of Done : rapport technique synthétique avec écarts P0/P1/P2 et recommandations Lot 3.  
Dépendances : conformité US-GOV-001 avant extraction réelle.

### Compliance Lead — Montesquieu

Contexte : éviter exposition de données personnelles et secrets avant manipulation HaloPSA.  
Critères d'acceptation : valider minimisation, pseudonymisation, troncature, stockage local, absence de secrets/données dans Git.  
Definition of Done : feu vert conformité ou liste de blocages P0.  
Dépendances : stratégie extraction tech-lead.

### DevOps Engineer — Tesla

Contexte : rendre Sprint 1 pilotable et préparer GitHub Projects/workflow PR.  
Critères d'acceptation : issues Sprint 1 prêtes/créées, labels/milestone/board cohérents, vérification main protégée et secrets exclus.  
Definition of Done : structure GitHub Projects documentée et aucun secret exposé.  
Dépendances : backlog Sprint 1.

## 7. Recommandation PM

Valider Sprint 1 avec priorité absolue aux preuves opérationnelles Lot 2 et au feu vert conformité. Ne pas recadrer l'objectif produit ; recadrer seulement le calendrier si le dataset ou la labellisation ne sont pas confirmés sous 1 semaine.

---

## 8. Retours leads — consolidation Scrum Master

### Tech Lead — Turing

**Décision** : NO-GO technique pour démarrer Lot 3 ML opérationnel.

Observé :
- Roadmap, backlog, rapport Sprint 1, audit HaloPSA, contexte RGPD et architecture cible présents.
- Backend FastAPI opérationnel, extraction HaloPSA, schéma PostgreSQL, dataset ML, EDA et labels non prouvés dans le dépôt.
- Contraintes RNCP Lot 3 présentes documentairement.

Risques P0 :
- Aucun dataset local exploitable.
- Extraction HaloPSA non testée ou mockée.
- Schéma PostgreSQL local non observable.
- Pseudonymisation/nettoyage non prouvés.
- Labels redondance absents.
- Schéma ML pairwise non stabilisé.
- Feu vert conformité absent.

Actions recommandées :
- Formaliser extraction read-only avec pagination, token, retries et rate limiting.
- Matérialiser PostgreSQL local et schéma initial.
- Définir dataset ticket + dataset pairwise pour apprentissage supervisé.
- Préparer tests sans réseau et contrôles qualité dataset.

### Compliance Lead — Montesquieu

**Décision** : NO-GO conformité/sécurité pour extraction HaloPSA réelle et dataset ML.

Observé :
- Qualification du traitement, finalité, base légale et classification des champs sensibles documentées.
- Registre RGPD art. 30, cartographie formelle, procédure droits des personnes, purge post-soutenance et preuve de pseudonymisation absents ou non prouvés.
- Présence d'un secret réel dans un fichier local non destiné au versioning signalée par compliance ; aucun secret n'est recopié ici.

Risques P0 :
- Rotation/vérification des credentials à effectuer avant extraction réelle.
- Absence de preuve que les secrets et datasets réels sont exclus de Git et de l'historique.
- Registre de traitement RGPD absent.
- Pseudonymisation `user_id` et nettoyage/troncature `details` non prouvés.
- PostgreSQL local non vérifié.
- Purge post-soutenance non documentée.

Actions obligatoires avant extraction réelle :
- Rotater les credentials concernés.
- Vérifier absence de secrets/datasets dans Git et historique.
- Produire registre RGPD et cartographie des champs.
- Prouver pseudonymisation, nettoyage et troncature.
- Documenter PostgreSQL local et purge post-soutenance.

### DevOps Engineer — Tesla

**Décision** : Sprint 1 pilotable côté GitHub Projects.

Réalisé :
- Board GitHub Projects créé : https://github.com/users/TheSpaceRangers/projects/6
- Milestone créé : `Sprint 1 — Socle données & backlog`.
- Labels créés : `user-story`, `task`, `P0`, `P1`, `P2`, `lot-2`, `lot-3`, `compliance`, `data`, `ml`, `devops`.
- Issues créées :
  - US-PM-001 : https://github.com/TheSpaceRangers/plateforme-detection-tickets-redondants/issues/1
  - US-PM-002 : https://github.com/TheSpaceRangers/plateforme-detection-tickets-redondants/issues/2
  - US-DATA-001 : https://github.com/TheSpaceRangers/plateforme-detection-tickets-redondants/issues/3
  - US-DATA-002 : https://github.com/TheSpaceRangers/plateforme-detection-tickets-redondants/issues/4
  - US-GOV-001 : https://github.com/TheSpaceRangers/plateforme-detection-tickets-redondants/issues/5

Observé :
- `main` protégée : review obligatoire, admins inclus, historique linéaire, force-push et suppression interdits, conversations à résoudre.
- `.env.example` sans secret réel, mais vides.
- Aucun workflow CI GitHub Actions présent.

Point d'attention :
- Les tâches sont intégrées comme checklists dans les US, pas comme issues séparées.
- `.DS_Store` local non suivi observé ; à exclure via future PR si nécessaire.

## 9. Décision de sprint consolidée

- Sprint 1 reste valide et doit se concentrer sur sécurisation, preuves et documentation exécutable.
- Lot 3 ML ne doit pas démarrer opérationnellement.
- Extraction HaloPSA réelle bloquée jusqu'à levée des P0 conformité/sécurité.
- Le jalon `2026-05-31 — Socle données exploitable pour ML` est à risque élevé.

## 10. Recommandation PM actualisée

Valider Sprint 1 sans recadrage produit, mais avec arbitrage de priorité : traiter d'abord les P0 conformité/secrets et dataset avant toute expérimentation ML. Si les P0 ne sont pas levés avant le 2026-05-31, acter un décalage contrôlé du Lot 3 plutôt qu'un démarrage ML sur socle non conforme.

---

## 11. Correction de cadrage — planification globale complète

**Date** : 2026-05-22  
**Décision** : Sprint 1 ne couvre plus seulement le démarrage opérationnel ; il porte aussi la déclinaison complète de la planification projet Sprint 0 → Sprint 7.

### Livrables de planification produits

- `gestion-de-projet/backlog.md` mis à jour pour couvrir Lot 0 à Lot 6.
- `gestion-de-projet/sprints/sprint-0.md` créé.
- `gestion-de-projet/sprints/sprint-2.md` créé.
- `gestion-de-projet/sprints/sprint-3.md` créé.
- `gestion-de-projet/sprints/sprint-4.md` créé.
- `gestion-de-projet/sprints/sprint-5.md` créé.
- `gestion-de-projet/sprints/sprint-6.md` créé.
- `gestion-de-projet/sprints/sprint-7.md` créé.
- `gestion-de-projet/sprints/sprint-1.md` conservé et complété pour tracer la correction de cadrage.

### Validation Tech Lead — Turing

Décision : roadmap validée conditionnellement.

Points intégrés :
- Lot 3 ML strictement bloqué sans Go Lot 2.
- Sprint 2 limité à dataset, labels, pairwise et split ; aucun entraînement avant Go.
- CI recommandée dès les premiers modules testables, même si stabilisation formelle en Sprint 6.
- Preuves mémoire à collecter en continu, pas seulement en Sprint 7.

### Validation Compliance Lead — Montesquieu

Décision : No-Go extraction HaloPSA réelle, No-Go dataset ML réel et No-Go Lot 3 tant que Lot 2 conformité/sécurité n'est pas validé.

Gates intégrés :
- Registre RGPD Art. 30.
- Cartographie champ par champ HaloPSA.
- Autorisation client / DPA / rôles RGPD clarifiés.
- Secrets vérifiés ou rotatés si doute.
- Pseudonymisation des identifiants et nettoyage PII du texte libre prouvés.
- Procédure de purge post-soutenance.
- Mémoire, annexes et captures sans données personnelles ni secrets.

### Alignement GitHub Project — Tesla

Réalisé sans suppression du travail existant :
- Project GitHub conservé : https://github.com/users/TheSpaceRangers/projects/6
- Issues Sprint 1 conservées : #1 à #5.
- Milestones Sprint 0 et Sprint 2 à Sprint 7 créés.
- Issues globales créées :
  - Sprint 0 : #6
  - Sprint 2 : #7
  - Sprint 3 : #8
  - Sprint 4 : #9
  - Sprint 5 : #10
  - Sprint 6 : #11
  - Sprint 7 : #12

### Points Go/No-Go proposés

| Gate | Décision actuelle | Condition de Go |
| --- | --- | --- |
| Extraction HaloPSA réelle | No-Go | Registre, cartographie, secrets, autorisation/DPA, pseudonymisation, purge validés |
| Lot 3 ML | No-Go | Dataset nettoyé, EDA, labels, split ≥ 70/30, conformité Lot 2 validée |
| Lot 4 API/application | À venir | Modèle sérialisé validé, métriques documentées, contrat API stable |
| Lot 5 qualité/conformité | À venir | Application fonctionnelle, tests, CI, logs maîtrisés |
| Lot 6 mémoire/soutenance | À venir | Audits validés, preuves RNCP complètes, captures anonymisées |

### Recommandation Scrum Master

Piloter le projet par gates formels et non par simple pression calendaire. Le jalon `2026-05-31 — Socle données exploitable` reste à risque élevé : si les P0 conformité/données ne sont pas levés, acter un décalage contrôlé du Lot 3 plutôt qu'un ML non conforme ou non reproductible.
