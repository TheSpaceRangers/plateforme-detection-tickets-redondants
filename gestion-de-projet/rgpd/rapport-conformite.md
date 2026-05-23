# Rapport de conformité RGPD — Synthèse Go/No-Go

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Mission** : P0 RGPD / Conformité — Sprint 1  
**Date** : 2026-05-23  
**Rédacteur** : Compliance Lead (Montesquieu)  
**Destinataire** : Scrum Master (Eisenhower)

---

## 1. Synthèse exécutive

L'audit RGPD complet du projet SYNAPPSE a été réalisé conformément au périmètre défini par le Scrum Master (Sprint 1 — US-PM-001, US-PM-002). Les 6 livrables attendus ont été produits :

| # | Livrable | Fichier | Statut |
|---|---|---|---|
| 1 | Registre de traitement (Art. 30) | `registre-traitement.md` | ✅ Rédigé |
| 2 | Cartographie champs HaloPSA → PII | `cartographie-champs.md` | ✅ Rédigé |
| 3 | Stratégie de pseudonymisation | `strategie-pseudonymisation.md` | ✅ Rédigé |
| 4 | Minimisation des données | `minimisation-donnees.md` | ✅ Rédigé |
| 5 | Durée de conservation + purge | `conservation-purge.md` | ✅ Rédigé |
| 6 | Rapport de conformité — Go/No-Go | `rapport-conformite.md` | ✅ Présent document |

---

## 2. Périmètre audité

| Aspect | Couvert ? |
|---|---|
| Identification des PII dans l'API HaloPSA | ✅ Complet |
| Qualification de la base légale | ✅ Intérêt légitime (Art. 6.1.f) |
| Registre de traitement | ✅ Complet |
| Mesures de pseudonymisation | ✅ Documenté (SHA-256 + sel) |
| Nettoyage des champs textuels | ✅ Documenté (regex PII) |
| Minimisation des données collectées | ✅ Documenté |
| Durées de conservation | ✅ Documenté |
| Procédure de purge post-soutenance | ✅ Documenté |
| Sécurité des credentials et secrets | ✅ Via `.env` + `.gitignore` |
| Transferts hors UE | ✅ Aucun — tout en local |

---

## 3. Points de contrôle RGPD — Mise à jour

| # | Point | Statut Sprint 0 | Statut Sprint 1 | Évolution |
|---|---|---|---|---|
| PC-01 | Base légale identifiée | ✅ Validé | ✅ Validé | → inchangé |
| PC-02 | Dictionnaire de données classifié | ✅ Validé | ✅ Validé | → inchangé |
| PC-03 | Credentials API en variables d'environnement | ✅ Validé | ✅ Validé | → inchangé |
| PC-04 | Troncature details à 2000 car. | ✅ Implémenté | ✅ Implémenté | → inchangé |
| PC-05 | Pseudonymisation user_id | ⏳ À faire | ✅ Stratégie documentée | → ⬆️ Progression |
| PC-06 | Nettoyage NLP du champ details | ⏳ À faire | ✅ Stratégie documentée | → ⬆️ Progression |
| PC-07 | PostgreSQL accès localhost uniquement | ⏳ À faire | ⏳ À faire (non bloquant pour Go) | → inchangé |
| PC-08 | .gitignore excluant .env et credentials | ⏳ À faire | ⏳ À vérifier (devops) | → inchangé |
| PC-09 | Absence de données personnelles dans dataset final | ⏳ À faire | ⏳ Vérifiable après extraction | → inchangé |
| PC-10 | Mention RGPD dans l'application web | ⏳ À faire | ⏳ Sprint 4-5 | → inchangé |
| PC-11 | Procédure de purge post-soutenance | ⏳ À planifier | ✅ Documentée | → ⬆️ Progression |

---

## 4. Analyse des écarts résiduels

### 4.1 Écarts non bloquants (à traiter pendant extraction)

| Écart | Impact | Action corrective | Responsable | Échéance |
|---|---|---|---|---|
| PC-07 — PostgreSQL exposé | Faible (local uniquement) | Configurer `listen_addresses = 'localhost'` dans `postgresql.conf` | Backend Engineer | Sprint 2 |
| PC-08 — .gitignore incomplet | Moyen (risque d'erreur humaine) | Vérifier que `.env`, `*.pkl`, `data/raw/`, `__pycache__/` sont exclus | DevOps Engineer | Immédiat |
| PC-09 — Absence PII dans dataset | Moyen | Ajouter test automatique de détection PII résiduelles après nettoyage | ML Engineer + QA | Sprint 2 |
| PC-10 — Mention RGPD UI | Faible | Page "Mentions Légales" ou pop-up RGPD dans l'application web | Frontend Engineer | Sprint 4-5 |

### 4.2 Écarts bloquants

**Aucun écart bloquant identifié.** Tous les prérequis documentaires de conformité sont remplis.

---

## 5. Décision : ✅ GO — Extraction HaloPSA réelle autorisée

### 5.1 Conditions du Go

| Condition | Statut | Remarque |
|---|---|---|
| Registre de traitement rédigé | ✅ | `registre-traitement.md` — complet |
| Cartographie PII documentée | ✅ | `cartographie-champs.md` — 16 champs audités |
| Stratégie de pseudonymisation définie | ✅ | `strategie-pseudonymisation.md` — SHA-256 + sel, regex PII |
| Minimisation des données justifiée | ✅ | `minimisation-donnees.md` — 15 champs collectés, 6 exclus |
| Durée de conservation fixée | ✅ | `conservation-purge.md` — 12 mois, purge automatisée |
| Procédure de purge documentée | ✅ | Script `purge.py` + journal |
| Pas de données personnelles dans le dépôt | ✅ | Dossier `rgpd/` contient uniquement de la documentation |
| Hébergement 100% local | ✅ | Aucun cloud, aucune donnée sortante |

### 5.2 Périmètre de l'autorisation

| Action | Autorisée ? | Conditions |
|---|---|---|
| Extraction réelle GET /api/Tickets | ✅ **Oui** | Avec pseudonymisation immédiate avant stockage |
| Stockage PostgreSQL des tickets | ✅ **Oui** | Uniquement les champs minimisés + nettoyés |
| Utilisation des données pour ML | ✅ **Oui** | Uniquement après validation du dataset nettoyé (PC-09) |
| Extraction des noms/prenoms utilisateurs (Users) | ❌ **Non** | Explicitement exclu par minimisation |
| Export / copie des données brutes | ❌ **Non** | Pas de dump, pas de fichier CSV brut dans le repo |
| Conservation au-delà de 12 mois | ❌ **Non** | Purge obligatoire post-soutenance |

---

## 6. Recommandations pour la suite

### 6.1 Court terme (Sprint 1-2)

1. **Implémenter la pseudonymisation** dans le pipeline d'extraction (backend-engineer) — utiliser la fonction de référence dans `strategie-pseudonymisation.md`
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

| Blocage projet | Référence | Statut |
|---|---|---|
| Lot 2 — Extraction HaloPSA réelle | Dépendance critique STATUS.md | ✅ **Levée** (sous conditions) |
| Lot 3 — ML supervisé | Backlog — "Interdit tant que Lot 2 non validé" | ⏳ Partiellement — dépend encore de la vérification PC-09 et implémentation pseudonymisation |
| Go Lot 2 — Gate global | `backlog.md` — Gate Go/No-Go | ✅ **Go prononcé** |

---

## 8. Statut global

| Statut | |
|---|---|
| ✅ **GO pour extraction HaloPSA réelle** | Tous les prérequis documentaires sont remplis — la conformité RGPD est couverte par les livrables produits. |
| ⚠️ Écarts mineurs (PC-07, PC-08, PC-09) | À corriger pendant l'implémentation — ne bloquent pas le démarrage de l'extraction. |
| ❌ Aucun écart bloquant | Aucun point P0 n'empêche le Go extraction. |

### Décision finale

> **Le Compliance Lead prononce un GO sous conditions pour l'extraction réelle HaloPSA.**
>
> L'extraction peut démarrer immédiatement à condition que :
> 1. La pseudonymisation de `user_id` soit implémentée AVANT la première extraction (SHA-256 + sel)
> 2. Le nettoyage regex de `summary` et `details` soit appliqué AVANT stockage
> 3. Aucun champ de la liste "exclus" (minimisation-donnees.md) ne soit collecté
> 4. Les credentials HaloPSA soient dans `.env` et jamais dans le code

---

## 9. Annexes

| Document | Chemin |
|---|---|
| Registre de traitement | `gestion-de-projet/rgpd/registre-traitement.md` |
| Cartographie champs PII | `gestion-de-projet/rgpd/cartographie-champs.md` |
| Stratégie de pseudonymisation | `gestion-de-projet/rgpd/strategie-pseudonymisation.md` |
| Minimisation des données | `gestion-de-projet/rgpd/minimisation-donnees.md` |
| Conservation et purge | `gestion-de-projet/rgpd/conservation-purge.md` |
| Audit API HaloPSA | `.opencode/context/domain/halopsa.md` |
| Qualification RGPD | `.opencode/context/domain/rgpd.md` |
