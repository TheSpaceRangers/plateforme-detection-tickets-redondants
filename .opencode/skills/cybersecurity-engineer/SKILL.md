---
name: cybersecurity
description: Audit sécurité technique — credentials, OWASP LLM, vulnérabilités, permissions. Skill du cybersecurity-engineer.
version: 1.0.0
type: skill
---

# Cybersecurity Skill

> **Purpose**: Fournir au cybersecurity-engineer la checklist d'audit et les patterns de détection de vulnérabilités.

---

## OWASP LLM Top 10 — Référence rapide

| #     | Risque            | À vérifier                                                |
| ----- | ----------------- | --------------------------------------------------------- |
| LLM01 | Prompt Injection  | Entrées utilisateur non sanitisées vers le LLM            |
| LLM02 | Data Leakage      | Données sensibles dans les logs ou réponses               |
| LLM03 | Insecure Output   | Sorties LLM exécutées sans validation                     |
| LLM06 | Permission Issues | Agents avec trop de permissions                           |
| LLM08 | Excessive Agency  | Agent pouvant modifier des fichiers hors de son périmètre |

---

## Checklist d'audit SYNAPPSE

### Credentials & secrets

```bash
# Détecter les credentials hardcodés
grep -rn "client_id\|client_secret\|password\|token\|api_key" ml/ backend/ --include="*.py"
grep -rn "HALOPSA\|POSTGRES" ml/ backend/ --include="*.py"

# Vérifier que .env est dans .gitignore
cat .gitignore | grep .env
```

- [ ] Aucun credential HaloPSA hardcodé dans le code
- [ ] Aucun credential PostgreSQL hardcodé
- [ ] `.env` présent dans `.gitignore`
- [ ] `.env.example` ne contient aucune valeur sensible réelle

### Backend FastAPI

- [ ] Tous les endpoints valident et sanitisent les entrées (schémas Pydantic)
- [ ] Les erreurs ne retournent pas de stack trace en production
- [ ] Rate limiting configuré sur les endpoints publics
- [ ] Pas de `SELECT *` sur des tables volumineuses sans filtre

### Pipeline ML

- [ ] Les fichiers `.joblib` ne contiennent pas de données personnelles
- [ ] Les logs d'entraînement ne tracent pas de données patients ou noms
- [ ] Le dump SQL ne contient pas de données non anonymisées

### Agents & permissions

- [ ] Chaque agent a des permissions `edit` restreintes à son périmètre
- [ ] Les agents read-only ont bien `edit: deny`
- [ ] Aucun agent ne peut accéder à `**/*.env*` ou `**/*.key`
- [ ] Les permissions `task` sont restreintes aux agents autorisés

### Infrastructure

- [ ] `docker-compose.yml` n'expose pas de ports non nécessaires
- [ ] Les variables d'environnement PostgreSQL ne sont pas en clair dans `docker-compose.yml`

---

## Commandes d'audit utiles

```bash
# Chercher des secrets potentiels
grep -rn "password\|secret\|token\|api_key\|private_key" . \
  --include="*.py" --include="*.js" --include="*.json" \
  --exclude-dir=".git" --exclude-dir="node_modules"

# Vérifier les imports suspects
grep -rn "import os\|os.environ\|getenv" backend/app/ ml/src/

# Vérifier la structure des permissions dans les agents
grep -rn "edit:" .opencode/agents/

# Vérifier le .gitignore
cat .gitignore
```

---

## Niveaux de criticité

| Niveau       | Exemples                                                              |
| ------------ | --------------------------------------------------------------------- |
| **CRITICAL** | Credentials hardcodés, token exposé dans le code                      |
| **HIGH**     | Endpoint sans validation d'entrée, données personnelles dans les logs |
| **MEDIUM**   | Permission agent trop large, port non nécessaire exposé               |
| **LOW**      | Stack trace en mode debug, log verbeux                                |
