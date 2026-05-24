# Rapport de conformité RGPD — Synthèse Go/No-Go

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Mission** : US-GOV-001 — Corrections RGPD — Sprint 1  
**Date** : 2026-05-24  
**Rédacteur** : RGPD Engineer (Voltaire)  
**Destinataire** : Scrum Master (Eisenhower)

---

## 1. Synthèse exécutive

Le retest US-GOV-001 a permis de corriger la documentation RGPD dans le périmètre autorisé. Les livrables sont documentés, mais plusieurs contrôles restent à implémenter et vérifier avant toute extraction réelle HaloPSA.

| #   | Livrable                          | Fichier                         | Statut              |
| --- | --------------------------------- | ------------------------------- | ------------------- |
| 1   | Registre de traitement (Art. 30)  | `registre-traitement.md`        | ✅ Rédigé           |
| 2   | Cartographie champs HaloPSA → PII | `cartographie-champs.md`        | ✅ Rédigé           |
| 3   | Stratégie de pseudonymisation     | `strategie-pseudonymisation.md` | ✅ Rédigé           |
| 4   | Minimisation des données          | `minimisation-donnees.md`       | ✅ Rédigé           |
| 5   | Durée de conservation + purge     | `conservation-purge.md`         | ✅ Rédigé           |
| 6   | Rapport de conformité — Go/No-Go  | `rapport-conformite.md`         | ✅ Présent document |

---

## 2. Périmètre audité

| Aspect                                    | Couvert ?                                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------------ |
| Identification des PII dans l'API HaloPSA | ✅ Complet                                                                     |
| Qualification de la base légale           | 📝 Intérêt légitime documenté (Art. 6.1.f), à valider avec autorisation client |
| Registre de traitement                    | ✅ Complet                                                                     |
| Mesures de pseudonymisation               | ✅ Documenté (HMAC-SHA-256 + secret obligatoire)                               |
| Nettoyage des champs textuels             | ✅ Documenté (regex PII)                                                       |
| Minimisation des données collectées       | ✅ Documenté                                                                   |
| Durées de conservation                    | ✅ Documenté                                                                   |
| Procédure de purge post-soutenance        | ✅ Documenté                                                                   |
| Sécurité des credentials et secrets       | 📝 Documenté ; preuve `.gitignore` / absence secrets à vérifier                |
| Transferts hors UE                        | ✅ Aucun — tout en local                                                       |

---

## 3. Points de contrôle RGPD — US-GOV-001

| #     | Point                                              | Statut Sprint 0 | Statut Sprint 1                   | Évolution                                                |
| ----- | -------------------------------------------------- | --------------- | --------------------------------- | -------------------------------------------------------- |
| PC-01 | Base légale identifiée                             | ✅ Validé       | 📝 Documenté                      | Test d'intérêt légitime formalisé                        |
| PC-02 | Dictionnaire de données classifié                  | ✅ Validé       | 📝 Documenté                      | `agent_id` requalifié comme donnée personnelle indirecte |
| PC-03 | Credentials API en variables d'environnement       | ✅ Validé       | ⏳ À vérifier                     | Preuve `.env` / `.gitignore` requise                     |
| PC-04 | Troncature details à 2000 car.                     | ✅ Implémenté   | 📝 Documenté                      | Implémentation non vérifiée dans ce retest documentaire  |
| PC-05 | Pseudonymisation user_id                           | ⏳ À faire      | 📝 Documenté                      | HMAC-SHA-256, secret obligatoire, fail-closed            |
| PC-06 | Nettoyage NLP du champ details                     | ⏳ À faire      | 📝 Documenté                      | Contrôle résiduel requis avant stockage                  |
| PC-07 | PostgreSQL accès localhost uniquement              | ⏳ À faire      | ⏳ À faire (non bloquant pour Go) | → inchangé                                               |
| PC-08 | .gitignore excluant .env et credentials            | ⏳ À faire      | ⏳ À vérifier (devops)            | → inchangé                                               |
| PC-09 | Absence de données personnelles dans dataset final | ⏳ À faire      | ⏳ Vérifiable après extraction    | → inchangé                                               |
| PC-10 | Mention RGPD dans l'application web                | ⏳ À faire      | ⏳ Sprint 4-5                     | → inchangé                                               |
| PC-11 | Procédure de purge post-soutenance                 | ⏳ À planifier  | ✅ Documentée                     | → ⬆️ Progression                                         |

---

## 4. Analyse des écarts résiduels

### 4.1 Écarts à lever avant extraction réelle

| Écart                             | Impact                          | Action corrective                                                     | Responsable         | Échéance         |
| --------------------------------- | ------------------------------- | --------------------------------------------------------------------- | ------------------- | ---------------- |
| PC-07 — PostgreSQL exposé         | Faible (local uniquement)       | Configurer `listen_addresses = 'localhost'` dans `postgresql.conf`    | Backend Engineer    | Sprint 2         |
| PC-08 — .gitignore incomplet      | Moyen (risque d'erreur humaine) | Vérifier que `.env`, `*.pkl`, `data/raw/`, `__pycache__/` sont exclus | DevOps Engineer     | Immédiat         |
| PC-09 — Absence PII dans dataset  | Moyen                           | Ajouter test automatique de détection PII résiduelles après nettoyage | ML Engineer + QA    | Sprint 2         |
| PC-10 — Mention RGPD UI           | Faible                          | Page "Mentions Légales" ou pop-up RGPD dans l'application web         | Frontend Engineer   | Sprint 4-5       |
| Autorisation client + DPA HaloPSA | Élevé                           | Obtenir l'autorisation écrite client et référencer le DPA HaloPSA     | Compliance Lead     | Avant extraction |
| `agent_id`                        | Moyen                           | Exclure par défaut ou pseudonymiser si nécessité métier documentée    | Tech Lead / Backend | Avant extraction |

### 4.2 Écarts bloquants

L'extraction réelle reste bloquée tant que les prérequis suivants ne sont pas vérifiés : autorisation client, DPA HaloPSA, absence de secrets/données réelles dans le dépôt, implémentation effective de la pseudonymisation et contrôle PII résiduel.

---

## 5. Décision : ⚠️ GO documentaire conditionnel — extraction réelle non autorisée à ce stade

### 5.1 Conditions du Go

| Condition                                 | Statut | Remarque                                                                                      |
| ----------------------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| Registre de traitement rédigé             | 📝     | `registre-traitement.md` — rôles, autorisation client, DPA et test d'intérêt légitime ajoutés |
| Cartographie PII documentée               | 📝     | `cartographie-champs.md` — identifiants et `agent_id` requalifiés                             |
| Stratégie de pseudonymisation définie     | 📝     | `strategie-pseudonymisation.md` — HMAC-SHA-256 + secret, fail-closed                          |
| Minimisation des données justifiée        | ✅     | `minimisation-donnees.md` — 15 champs collectés, 6 exclus                                     |
| Durée de conservation fixée               | 📝     | `conservation-purge.md` — J+7 post-soutenance maximum pour données et artefacts dérivés       |
| Procédure de purge documentée             | 📝     | Procédure opératoire + journal sans données sensibles                                         |
| Pas de données personnelles dans le dépôt | ⏳     | À prouver par contrôle dédié ; aucune donnée réelle ne doit être ajoutée                      |
| Hébergement 100% local                    | 📝     | Documenté, non vérifié techniquement dans ce retest                                           |

### 5.2 Périmètre de l'autorisation

| Action                                           | Autorisée ? | Conditions                                                                         |
| ------------------------------------------------ | ----------- | ---------------------------------------------------------------------------------- |
| Extraction réelle GET /api/Tickets               | ❌ **Non**  | Autorisée seulement après levée des prérequis et validation compliance             |
| Stockage PostgreSQL des tickets                  | ❌ **Non**  | Autorisé seulement après pseudonymisation, nettoyage et contrôle résiduel vérifiés |
| Utilisation des données pour ML                  | ❌ **Non**  | Autorisée seulement après validation du dataset nettoyé (PC-09)                    |
| Extraction des noms/prenoms utilisateurs (Users) | ❌ **Non**  | Explicitement exclu par minimisation                                               |
| Export / copie des données brutes                | ❌ **Non**  | Pas de dump, pas de fichier CSV brut dans le repo                                  |
| Conservation au-delà de J+7 post-soutenance      | ❌ **Non**  | Purge obligatoire post-soutenance                                                  |

---

## 6. Recommandations pour la suite

### 6.1 Court terme (Sprint 1-2)

1. **Implémenter la pseudonymisation** dans le pipeline d'extraction (backend-engineer) — respecter la spécification HMAC-SHA-256 de `strategie-pseudonymisation.md`
2. **Configurer `postgresql.conf`** en `listen_addresses = 'localhost'` (backend-engineer)
3. **Vérifier `.gitignore`** : ajouter `data/raw/`, `*.pkl`, `data/processed/` si pas déjà fait (devops-engineer)
4. **Tester les regex de nettoyage** sur un échantillon de tickets réels en aveugle (qa-engineer)

### 6.2 Moyen terme (Sprint 2-3)

5. **Ajouter NER spaCy** pour compléter le nettoyage regex (ml-engineer)
6. **Automatiser le test PII résiduel** dans la CI — échouer si un pattern PII est détecté dans la colonne `summary` ou `details` (qa-engineer)
7. **Vérifier l'absence de PII dans les features ML** avant tout entraînement (ml-engineer)

### 6.3 Long terme (Sprint 4-6)

8. **Ajouter une page "Conformité RGPD"** dans l'application web — résumé du registre, engagement de confidentialité (frontend-engineer)
9. **Planifier la purge de test** en simulation avant la purge réelle post-soutenance (devops-engineer)

---

## 7. Blocages levés par ce rapport

| Blocage projet                    | Référence                                      | Statut                                                                                       |
| --------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Lot 2 — Extraction HaloPSA réelle | Dépendance critique STATUS.md                  | ❌ Non levée — prérequis documentés mais non vérifiés                                        |
| Lot 3 — ML supervisé              | Backlog — "Interdit tant que Lot 2 non validé" | ⏳ Partiellement — dépend encore de la vérification PC-09 et implémentation pseudonymisation |
| Go Lot 2 — Gate global            | `backlog.md` — Gate Go/No-Go                   | ⚠️ GO documentaire conditionnel uniquement                                                   |

---

## 8. Statut global

| Statut                                    |                                                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| ⚠️ **GO documentaire conditionnel**       | Les corrections US-GOV-001 sont documentées.                                                                        |
| ❌ **NO-GO extraction réelle à ce stade** | Les preuves et implémentations ne sont pas vérifiées.                                                               |
| ⚠️ Écarts à lever                         | Autorisation client, DPA HaloPSA, secrets/.gitignore, absence données réelles, pseudonymisation, contrôle résiduel. |

### Décision finale

> **Le RGPD Engineer constate un GO documentaire conditionnel, mais ne valide pas l'extraction réelle HaloPSA.**
>
> L'extraction ne pourra être envisagée qu'après preuve que :
>
> 1. L'autorisation client et le DPA HaloPSA sont référencés
> 2. La pseudonymisation HMAC-SHA-256 est implémentée avant stockage
> 3. Le nettoyage et le contrôle PII résiduel sont effectifs
> 4. `agent_id` est exclu ou pseudonymisé
> 5. Les secrets sont hors dépôt, `.gitignore` couvre les artefacts à risque et aucune donnée réelle HaloPSA n'est présente

---

## 9. Annexes

| Document                      | Chemin                                                 |
| ----------------------------- | ------------------------------------------------------ |
| Registre de traitement        | `gestion-de-projet/rgpd/registre-traitement.md`        |
| Cartographie champs PII       | `gestion-de-projet/rgpd/cartographie-champs.md`        |
| Stratégie de pseudonymisation | `gestion-de-projet/rgpd/strategie-pseudonymisation.md` |
| Minimisation des données      | `gestion-de-projet/rgpd/minimisation-donnees.md`       |
| Conservation et purge         | `gestion-de-projet/rgpd/conservation-purge.md`         |
| Audit API HaloPSA             | `.opencode/context/domain/halopsa.md`                  |
| Qualification RGPD            | `.opencode/context/domain/rgpd.md`                     |
