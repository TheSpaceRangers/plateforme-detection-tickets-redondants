# Backlog projet — Plateforme Détection Tickets Redondants

**Dernière mise à jour** : 2026-05-22  
**Périmètre** : planification complète Lot 0 → Lot 6, Sprint 0 → Sprint 7, jusqu'au dépôt mémoire et soutenance.  
**Source PM** : `gestion-de-projet/STATUS.md`  
**Décision structurante** : Lot 3 ML reste bloqué tant que Lot 2 données + conformité n'a pas reçu un Go formel.

## Légende

| Priorité | Sens |
| --- | --- |
| P0 | Bloquant immédiat ou gate Go/No-Go |
| P1 | Nécessaire au lot suivant ou à la conformité RNCP |
| P2 | Amélioration, stabilisation ou preuve de soutenance |

| Lead | Périmètre |
| --- | --- |
| `tech-lead` | Architecture, backend, frontend, ML, QA via coordination interne |
| `compliance-lead` | RGPD, sécurité, conformité, audits via coordination interne |
| `devops-engineer` | GitHub Projects, milestones, CI/CD, workflow Git |
| `scrum-master` | Pilotage, consolidation, gates, reporting PM |

## Gates Go/No-Go globaux

| Gate | Condition de Go | No-Go si | Sprint cible |
| --- | --- | --- | --- |
| Go Lot 2 — extraction réelle | Registre RGPD, cartographie champs, secrets vérifiés, PostgreSQL local, pseudonymisation/nettoyage prouvés | Secret/dataset réel dans Git, autorisation/DPA non clarifiée, absence de purge | Sprint 1 |
| Go Lot 3 — ML supervisé | Dataset nettoyé, EDA, labels, dataset pairwise, split ≥ 70/30, validation conformité | Lot 2 non validé, labels absents, PII dans features/logs | Sprint 2 |
| Go Lot 4 — API/application | Modèle sélectionné/sérialisé, métriques documentées, contrat API défini | Artefact modèle non validé, schéma prédiction instable | Sprint 4 |
| Go Lot 5 — stabilisation | Application fonctionnelle, tests démarrés, CI active, logs maîtrisés | Audits sécurité/RGPD impossibles, CI absente | Sprint 6 |
| Go Lot 6 — dépôt mémoire | Preuves consolidées, captures anonymisées, annexes sans secrets/données | Mémoire ou démo expose données personnelles/secrets | Sprint 7 |

---

## Sprint 0 — Gouvernance GitHub et planification globale

### US-GOV-000 : Installer la gouvernance projet et le workflow GitHub

En tant que PM, je veux un socle de gouvernance clair afin de piloter le projet par PR, backlog et jalons.

**Priorité** : P0  
**Lot** : Lot 0  
**Assigné à** : devops-engineer + scrum-master  
**Estimation** : M  
**Dépendances** : aucune

Critères d'acceptation :
- [x] Dépôt GitHub créé et `main` protégée.
- [x] Workflow PR obligatoire établi.
- [x] Roadmap globale validée dans `STATUS.md`.
- [x] GitHub Project initialisé sans suppression du travail existant.

Tâches :
- [x] TASK-GOV-000-A : Confirmer protection `main` et règles PR → devops-engineer
- [x] TASK-GOV-000-B : Créer board/milestones initiales → devops-engineer
- [x] TASK-GOV-000-C : Formaliser sprints directeurs → scrum-master

Definition of Done :
- [x] Gouvernance documentée.
- [x] Project GitHub utilisable.
- [x] Sprint 0 représenté dans `gestion-de-projet/sprints/`.

---

## Sprint 1 — Sécuriser conformité + socle données

### US-PM-001 : Confirmer l'état réel des livrables Lot 1 et Lot 2

En tant que PM, je veux disposer d'un état des lieux vérifié afin de distinguer les livrables réellement disponibles des livrables seulement planifiés.

**Priorité** : P0  
**Lot** : Lot 1 → Lot 2  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : M  
**Dépendances** : aucune

Critères d'acceptation :
- [x] Les livrables Lot 1/Lot 2 sont classés `présent`, `partiel`, `absent` ou `à confirmer`.
- [x] Les écarts entre planning et dépôt sont listés avec impact sur Lot 3.
- [x] Aucun secret ni donnée personnelle n'est exposé dans le rapport.

Tâches :
- [x] TASK-PM-001-A : Inventorier livrables techniques existants/manquants → tech-lead
- [x] TASK-PM-001-B : Inventorier livrables RGPD/sécurité existants/manquants → compliance-lead
- [x] TASK-PM-001-C : Consolider écarts et risques → scrum-master

Definition of Done :
- [x] Rapport Sprint 1 disponible.
- [x] Écarts priorisés P0/P1/P2.
- [x] Décision No-Go Lot 3 documentée.

### US-PM-002 : Structurer le backlog projet complet

En tant que PM, je veux un backlog complet par lots, sprints et dépendances afin de piloter le projet jusqu'à la soutenance.

**Priorité** : P0  
**Lot** : transversal  
**Assigné à** : scrum-master + devops-engineer  
**Estimation** : M  
**Dépendances** : `STATUS.md`

Critères d'acceptation :
- [x] Le backlog couvre Lot 0 à Lot 6.
- [x] Les sprints 0 à 7 sont décrits avec objectifs, livrables, dépendances et validations.
- [x] Les tâches sont assignées uniquement aux leads autorisés.
- [x] Les issues/milestones GitHub sont alignées sans suppression du travail existant.

Tâches :
- [x] TASK-PM-002-A : Produire backlog projet actionnable → scrum-master
- [x] TASK-PM-002-B : Aligner GitHub Project/issues globales → devops-engineer
- [x] TASK-PM-002-C : Intégrer retours Tech Lead et Compliance Lead → scrum-master

Definition of Done :
- [x] `gestion-de-projet/backlog.md` couvre Sprint 0 à Sprint 7.
- [x] `gestion-de-projet/sprints/` contient la vue Sprint 0 à Sprint 7.
- [x] Dépendances critiques visibles.

### US-GOV-001 : Vérifier les garde-fous RGPD et sécurité avant données réelles

En tant que responsable projet, je veux vérifier les garde-fous RGPD et sécurité afin d'éviter toute exposition de données personnelles ou de secrets.

**Priorité** : P0  
**Lot** : Lot 1 → Lot 2  
**Assigné à** : compliance-lead + devops-engineer  
**Estimation** : L  
**Dépendances** : aucune ; bloque extraction réelle

Critères d'acceptation :
- [ ] Registre RGPD Art. 30 initial formalisé.
- [ ] Cartographie champ par champ HaloPSA disponible.
- [ ] Autorisation client / DPA / rôles RGPD clarifiés.
- [ ] Secrets vérifiés ou rotatés si doute.
- [ ] Scan Git/historique/secrets réalisé.
- [ ] Procédure purge post-soutenance définie.

Tâches :
- [ ] TASK-GOV-001-A : Auditer garde-fous RGPD/sécurité → compliance-lead
- [ ] TASK-GOV-001-B : Vérifier Git/GitHub contre secrets et datasets versionnés → devops-engineer
- [ ] TASK-GOV-001-C : Produire checklist Go/No-Go extraction réelle → compliance-lead

Definition of Done :
- [ ] Feu vert conformité documenté ou blocages P0 explicités.
- [ ] Aucun secret/donnée réelle dans Git.
- [ ] Extraction réelle autorisée uniquement après Go formel.

### US-DATA-001 : Valider la stratégie d'extraction HaloPSA contrôlée

En tant que responsable produit, je veux valider la stratégie d'extraction HaloPSA afin de collecter uniquement les champs nécessaires à la détection de redondance.

**Priorité** : P0  
**Lot** : Lot 2  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : US-GOV-001 avant extraction réelle

Critères d'acceptation :
- [ ] Endpoints HaloPSA nécessaires confirmés.
- [ ] Champs minimisés et classifiés par sensibilité.
- [ ] Pagination, expiration token, retries et rate limiting pris en compte.
- [ ] Stratégie de pseudonymisation/nettoyage validée avant stockage exploitable.

Tâches :
- [ ] TASK-DATA-001-A : Définir flux d'extraction API et erreurs à gérer → tech-lead
- [ ] TASK-DATA-001-B : Valider périmètre champs au regard RGPD/sécurité → compliance-lead
- [ ] TASK-DATA-001-C : Confirmer variables d'environnement attendues sans secret hardcodé → tech-lead

Definition of Done :
- [ ] Stratégie d'extraction documentée.
- [ ] Liste de champs validée conformité.
- [ ] Aucun appel réel tant que gate conformité non validé.

### US-DATA-002 : Définir les critères d'acceptation du dataset exploitable ML

En tant que futur utilisateur du pipeline ML, je veux des critères de qualité dataset afin de démarrer Lot 3 sur une base mesurable.

**Priorité** : P0  
**Lot** : Lot 2 → Lot 3  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : US-DATA-001, US-GOV-001

Critères d'acceptation :
- [ ] Dataset stocké localement, sans secret, sans export cloud.
- [ ] Colonnes minimales documentées : ticket, client pseudonymisé, résumé nettoyé, détails nettoyés/tronqués, catégories, dates utiles, statut, priorité, label ou stratégie de labellisation.
- [ ] Qualité mesurée : valeurs manquantes, doublons, distributions, déséquilibre de classes.
- [ ] Protocole RNCP intégré : KNN, Random Forest, Decision Tree, Logistic Regression, split ≥ 70/30, Accuracy/F1/Recall, Grid Search.

Tâches :
- [ ] TASK-DATA-002-A : Définir schéma dataset ML et contrôles qualité → tech-lead
- [ ] TASK-DATA-002-B : Définir stratégie de labellisation tickets redondants → tech-lead
- [ ] TASK-DATA-002-C : Valider anonymisation/pseudonymisation avant usage ML → compliance-lead
- [ ] TASK-DATA-002-D : Formaliser critères d'entrée Lot 3 ML → scrum-master

Definition of Done :
- [ ] Critères d'entrée Lot 3 documentés.
- [ ] Risques dataset connus et priorisés.
- [ ] Lot 3 reste bloqué sans Go Lot 2.

---

## Sprint 2 — Finaliser dataset ML et labellisation

### US-DATA-003 : Matérialiser PostgreSQL local et le schéma tickets

En tant que tech lead, je veux un stockage PostgreSQL local afin de respecter l'architecture cible et préparer les données ML.

**Priorité** : P0  
**Lot** : Lot 2  
**Assigné à** : tech-lead  
**Estimation** : L  
**Dépendances** : US-GOV-001, US-DATA-001

Critères d'acceptation :
- [ ] PostgreSQL local opérationnel, pas de SQLite.
- [ ] Schéma tickets documenté.
- [ ] Données fictives/synthétiques utilisables tant que Go extraction réelle absent.
- [ ] Aucun dump réel versionné.

Tâches :
- [ ] TASK-DATA-003-A : Définir schéma PostgreSQL tickets → tech-lead
- [ ] TASK-DATA-003-B : Préparer données fictives de validation → tech-lead
- [ ] TASK-DATA-003-C : Vérifier exclusion dumps/datasets de Git → devops-engineer

Definition of Done :
- [ ] Schéma local validé.
- [ ] Conformité de stockage confirmée.
- [ ] Dépendance Lot 4 API anticipée.

### US-DATA-004 : Produire dataset nettoyé, EDA et rapport qualité

En tant que PM, je veux un dataset documenté et mesuré afin de décider le passage vers le ML supervisé.

**Priorité** : P0  
**Lot** : Lot 2  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : US-DATA-003, Go extraction réelle ou données synthétiques pour test

Critères d'acceptation :
- [ ] Pipeline de nettoyage/troncature défini.
- [ ] EDA disponible : volumes, valeurs manquantes, doublons, distributions.
- [ ] Contrôle absence PII dans dataset exploitable.
- [ ] Rapport qualité dataset produit.

Tâches :
- [ ] TASK-DATA-004-A : Produire contrôles qualité dataset → tech-lead
- [ ] TASK-DATA-004-B : Valider absence PII dans dataset ML → compliance-lead
- [ ] TASK-DATA-004-C : Documenter limites et biais du dataset → tech-lead

Definition of Done :
- [ ] Rapport qualité disponible.
- [ ] Go/No-Go Lot 3 préparé.
- [ ] Données réelles toujours exclues de Git.

### US-ML-000 : Préparer labellisation et dataset pairwise sans entraîner de modèle

En tant que ML lead coordonné par le tech lead, je veux préparer les labels et paires afin de rendre l'entraînement supervisé possible après Go Lot 2.

**Priorité** : P0  
**Lot** : Lot 2 → Lot 3  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : US-DATA-004 ; aucun entraînement avant Go Lot 2

Critères d'acceptation :
- [ ] Règles de redondance documentées.
- [ ] Protocole de labellisation validé.
- [ ] Dataset pairwise défini.
- [ ] Split train/test ≥ 70/30 préparé et reproductible.

Tâches :
- [ ] TASK-ML-000-A : Définir logique pairwise et labels → tech-lead
- [ ] TASK-ML-000-B : Vérifier labels sans révélation client/personne → compliance-lead
- [ ] TASK-ML-000-C : Préparer gate Go Lot 3 → scrum-master

Definition of Done :
- [ ] Go/No-Go Lot 3 formel disponible.
- [ ] Aucune expérimentation ML réelle avant Go.
- [ ] Contraintes RNCP intégrées.

---

## Sprint 3 — Entraîner, comparer et sélectionner le modèle

### US-ML-001 : Définir baseline supervisée et protocole RNCP

En tant que responsable ML, je veux un protocole d'évaluation reproductible afin de comparer les modèles conformément au RNCP Bloc 3.

**Priorité** : P1  
**Lot** : Lot 3  
**Assigné à** : tech-lead  
**Estimation** : M  
**Dépendances** : Go Lot 3

Critères d'acceptation :
- [ ] Baseline définie avant optimisation.
- [ ] Split ≥ 70/30 documenté.
- [ ] Métriques Accuracy, F1, Recall calculables.
- [ ] Explicabilité score + justification prise en compte.

Tâches :
- [ ] TASK-ML-001-A : Définir protocole d'évaluation → tech-lead
- [ ] TASK-ML-001-B : Valider reproductibilité et absence données en Git → tech-lead
- [ ] TASK-ML-001-C : Documenter preuves RNCP → scrum-master

Definition of Done :
- [ ] Protocole validé.
- [ ] Métriques prêtes.
- [ ] Preuves mémoire collectées.

### US-ML-002 : Entraîner les quatre algorithmes RNCP obligatoires

En tant que candidat RNCP, je veux entraîner KNN, Random Forest, Decision Tree et Logistic Regression afin de démontrer la comparaison supervisée exigée.

**Priorité** : P1  
**Lot** : Lot 3  
**Assigné à** : tech-lead  
**Estimation** : L  
**Dépendances** : US-ML-001

Critères d'acceptation :
- [ ] KNN entraîné.
- [ ] Random Forest entraîné.
- [ ] Decision Tree entraîné.
- [ ] Logistic Regression entraînée.
- [ ] Résultats reproductibles localement.

Tâches :
- [ ] TASK-ML-002-A : Coordonner implémentation pipeline ML → tech-lead
- [ ] TASK-ML-002-B : Vérifier métriques par modèle → tech-lead
- [ ] TASK-ML-002-C : Contrôler logs ML sans texte ticket → compliance-lead

Definition of Done :
- [ ] Quatre modèles comparables.
- [ ] Logs et artefacts non sensibles.
- [ ] Résultats documentés.

### US-ML-003 : Réaliser Grid Search, sélectionner et sérialiser le modèle

En tant que responsable produit, je veux sélectionner un modèle traçable afin de l'intégrer à l'application web locale.

**Priorité** : P1  
**Lot** : Lot 3  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : US-ML-002

Critères d'acceptation :
- [ ] Grid Search réalisé.
- [ ] Accuracy, F1, Recall comparés.
- [ ] Modèle sélectionné et sérialisé localement.
- [ ] Risques de mémorisation/données dans artefact contrôlés.
- [ ] Limites et seuil de confiance documentés.

Tâches :
- [ ] TASK-ML-003-A : Coordonner Grid Search et sélection → tech-lead
- [ ] TASK-ML-003-B : Contrôler artefact modèle et stockage local → compliance-lead
- [ ] TASK-ML-003-C : Produire synthèse décision modèle → scrum-master

Definition of Done :
- [ ] Modèle prêt pour API.
- [ ] Rapport d'évaluation disponible.
- [ ] Gate Go Lot 4 préparé.

---

## Sprint 4 — Construire API prédiction et intégration modèle

### US-APP-001 : Définir contrat API et endpoint de prédiction

En tant que technicien support, je veux interroger une API locale afin d'obtenir les tickets similaires avec score de confiance.

**Priorité** : P1  
**Lot** : Lot 4  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : Go Lot 4, modèle sérialisé

Critères d'acceptation :
- [ ] Contrat entrée/sortie prédiction documenté.
- [ ] Endpoint local prévu avec validation stricte.
- [ ] Logs prédictions minimisés : identifiant pseudonymisé, score, version modèle, timestamp.
- [ ] Erreurs sans donnée sensible ni stack trace exposée.

Tâches :
- [ ] TASK-APP-001-A : Coordonner architecture FastAPI service/repository → tech-lead
- [ ] TASK-APP-001-B : Valider politique logs prédictions → compliance-lead
- [ ] TASK-APP-001-C : Préparer tests API → tech-lead

Definition of Done :
- [ ] API prédiction exploitable localement.
- [ ] Contrat stable pour frontend.
- [ ] Sécurité locale documentée.

### US-APP-002 : Journaliser les prédictions dans PostgreSQL

En tant que PM, je veux conserver des logs prédictions maîtrisés afin de démontrer la traçabilité sans exposer de données personnelles.

**Priorité** : P1  
**Lot** : Lot 4  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : M  
**Dépendances** : US-APP-001

Critères d'acceptation :
- [ ] Table logs prédictions définie.
- [ ] Pas de texte brut ticket dans les logs.
- [ ] Conservation et purge définies.
- [ ] Preuve intégrable au mémoire.

Tâches :
- [ ] TASK-APP-002-A : Définir schéma logs prédictions → tech-lead
- [ ] TASK-APP-002-B : Valider minimisation/conservation logs → compliance-lead
- [ ] TASK-APP-002-C : Documenter preuve de traçabilité → scrum-master

Definition of Done :
- [ ] Logs utiles et conformes.
- [ ] PostgreSQL reste le stockage cible.
- [ ] Gate UI prêt.

---

## Sprint 5 — Construire dashboard technicien

### US-UI-001 : Afficher alertes de redondance, scores et explications

En tant que technicien support, je veux visualiser les tickets similaires et leur score afin de prioriser le traitement sans doublon.

**Priorité** : P1  
**Lot** : Lot 4  
**Assigné à** : tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : US-APP-001, US-APP-002

Critères d'acceptation :
- [ ] UI React/Vite JavaScript, pas TypeScript.
- [ ] Dashboard affiche ticket courant, tickets similaires, score de confiance, explication.
- [ ] États chargement/erreur présents.
- [ ] Données personnelles non nécessaires masquées.
- [ ] Captures futures anonymisables pour mémoire/soutenance.

Tâches :
- [ ] TASK-UI-001-A : Coordonner composants et hooks frontend → tech-lead
- [ ] TASK-UI-001-B : Valider minimisation affichage UI → compliance-lead
- [ ] TASK-UI-001-C : Préparer scénario démo utilisateur → scrum-master

Definition of Done :
- [ ] Dashboard utilisable localement.
- [ ] Score + explication visibles.
- [ ] Données de démo conformes.

### US-UI-002 : Stabiliser le parcours de démonstration applicative

En tant que candidat, je veux une démonstration reproductible afin de soutenir le projet sans dépendre de données réelles sensibles.

**Priorité** : P2  
**Lot** : Lot 4 → Lot 6  
**Assigné à** : tech-lead + compliance-lead + scrum-master  
**Estimation** : M  
**Dépendances** : US-UI-001

Critères d'acceptation :
- [ ] Scénario démo local documenté.
- [ ] Données fictives ou anonymisées disponibles.
- [ ] Plan B démo préparé.
- [ ] Preuves visuelles sans PII collectées.

Tâches :
- [ ] TASK-UI-002-A : Valider parcours technique démo → tech-lead
- [ ] TASK-UI-002-B : Valider données/captures anonymisées → compliance-lead
- [ ] TASK-UI-002-C : Intégrer preuves dans suivi mémoire → scrum-master

Definition of Done :
- [ ] Démo stable.
- [ ] Captures conformes.
- [ ] Risque soutenance réduit.

---

## Sprint 6 — Qualité, sécurité, RGPD, CI

### US-QA-001 : Compléter tests et CI locale/GitHub

En tant que PM, je veux une chaîne qualité minimale afin de sécuriser les livrables avant mémoire.

**Priorité** : P1  
**Lot** : Lot 5  
**Assigné à** : tech-lead + devops-engineer  
**Estimation** : L  
**Dépendances** : application fonctionnelle

Critères d'acceptation :
- [ ] Tests backend/frontend/ML pertinents présents.
- [ ] CI GitHub active.
- [ ] Secret scan ou contrôle fichiers interdits intégré.
- [ ] Documentation commandes de test disponible.

Tâches :
- [ ] TASK-QA-001-A : Coordonner stratégie tests → tech-lead
- [ ] TASK-QA-001-B : Mettre en place CI GitHub → devops-engineer
- [ ] TASK-QA-001-C : Documenter critères de fermeture → scrum-master

Definition of Done :
- [ ] CI verte ou écarts documentés.
- [ ] Tests exécutables localement.
- [ ] Main protégée compatible checks.

### US-COMP-001 : Réaliser audits sécurité et RGPD finaux

En tant que responsable projet, je veux valider sécurité et conformité afin de déposer un mémoire sans risque d'exposition.

**Priorité** : P0  
**Lot** : Lot 5  
**Assigné à** : compliance-lead + devops-engineer  
**Estimation** : L  
**Dépendances** : application fonctionnelle, CI minimale

Critères d'acceptation :
- [ ] Audit sécurité final réalisé.
- [ ] Audit RGPD final réalisé.
- [ ] Inventaire/classification des actifs sensibles disponible.
- [ ] Blocage `.env`, datasets, dumps, logs, modèles réels vérifié.
- [ ] Documentation exploitation locale validée.

Tâches :
- [ ] TASK-COMP-001-A : Coordonner audit sécurité/RGPD → compliance-lead
- [ ] TASK-COMP-001-B : Vérifier règles CI/fichiers interdits → devops-engineer
- [ ] TASK-COMP-001-C : Consolider No-Go restants → scrum-master

Definition of Done :
- [ ] Go Lot 6 ou blocages documentés.
- [ ] Audits exploitables en annexe mémoire.
- [ ] Démo et repo sans secrets/données réelles.

---

## Sprint 7 — Mémoire, annexes et soutenance

### US-MEM-001 : Finaliser mémoire, annexes et preuves RNCP

En tant que candidat, je veux déposer un mémoire complet afin de démontrer la maîtrise du Bloc 3 et du projet de bout en bout.

**Priorité** : P0  
**Lot** : Lot 6  
**Assigné à** : scrum-master + tech-lead + compliance-lead  
**Estimation** : L  
**Dépendances** : Go Lot 6

Critères d'acceptation :
- [ ] Mémoire PDF prêt dépôt 2026-09-01.
- [ ] Annexes techniques : architecture, dataset, EDA, modèles, Grid Search, métriques.
- [ ] Annexes conformité : registre, cartographie, audits, purge.
- [ ] Captures sans données personnelles ni secrets.
- [ ] Preuves RNCP : 4 modèles, split ≥ 70/30, Accuracy/F1/Recall, app web intégrant modèle.

Tâches :
- [ ] TASK-MEM-001-A : Consolider preuves techniques → tech-lead
- [ ] TASK-MEM-001-B : Valider absence secrets/PII dans mémoire et annexes → compliance-lead
- [ ] TASK-MEM-001-C : Suivre dépôt mémoire et checklist finale → scrum-master

Definition of Done :
- [ ] Mémoire déposé.
- [ ] Annexes cohérentes et conformes.
- [ ] Traçabilité projet complète.

### US-SOUT-001 : Préparer et répéter la soutenance

En tant que candidat, je veux une soutenance structurée afin de présenter la valeur produit, les choix techniques et les limites en conditions maîtrisées.

**Priorité** : P1  
**Lot** : Lot 6  
**Assigné à** : scrum-master + tech-lead + compliance-lead  
**Estimation** : M  
**Dépendances** : US-MEM-001, scénario démo stable

Critères d'acceptation :
- [ ] Support oral finalisé.
- [ ] Démo locale répétée.
- [ ] Plan B disponible.
- [ ] Questions risques/RGPD/ML préparées.
- [ ] Purge post-soutenance planifiée.

Tâches :
- [ ] TASK-SOUT-001-A : Valider argumentaire technique → tech-lead
- [ ] TASK-SOUT-001-B : Valider argumentaire conformité → compliance-lead
- [ ] TASK-SOUT-001-C : Organiser répétitions et points d'amélioration → scrum-master

Definition of Done :
- [ ] Soutenance prête.
- [ ] Démo robuste.
- [ ] Engagement purge post-soutenance documenté.

## Synthèse dépendances opérationnelles

| Dépendance | Bloque | Responsable suivi |
| --- | --- | --- |
| Accès API HaloPSA + secrets valides | extraction réelle Lot 2 | compliance-lead + devops-engineer |
| Registre RGPD + cartographie champs | extraction réelle, dataset ML | compliance-lead |
| PostgreSQL local | Lot 2, Lot 4 | tech-lead |
| Dataset nettoyé + EDA | Lot 3 | tech-lead |
| Labels + pairwise dataset | entraînement supervisé | tech-lead |
| Go conformité Lot 2 | tout ML réel | compliance-lead + scrum-master |
| Modèle sérialisé validé | API prédiction | tech-lead + compliance-lead |
| CI/tests | stabilisation Lot 5 | devops-engineer + tech-lead |
| Captures anonymisées + preuves | mémoire/soutenance | scrum-master + compliance-lead |

## Alignement GitHub Project/issues

Observé via DevOps le 2026-05-22 :
- Project GitHub : <https://github.com/users/TheSpaceRangers/projects/6>
- Issues Sprint 1 conservées : #1 à #5.
- Milestones Sprint 0 et Sprint 2 à Sprint 7 créés.
- Issues globales Sprint 0 et Sprint 2 à Sprint 7 créées : #6 à #12.
- Aucun push Git ni suppression réalisés.

## Recommandation Scrum Master

Piloter par gates plutôt que par dates seules : préserver l'objectif de soutenance, mais refuser tout démarrage ML réel tant que Lot 2 données/conformité n'est pas validé. Introduire CI, preuves mémoire et anonymisation dès les sprints techniques pour éviter une dette finale impossible à absorber.
