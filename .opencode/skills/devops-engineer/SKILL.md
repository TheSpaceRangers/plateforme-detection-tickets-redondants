---
name: devops
description: CI/CD, GitHub Projects, conventions Git, infrastructure locale. Skill du devops-engineer.
version: 1.0.0
type: skill
---

# DevOps Skill

> **Purpose**: Fournir au devops-engineer les normes et commandes pour gérer l'infrastructure et le board GitHub Projects.

---

## Règles gh CLI — NON NÉGOCIABLES

```bash
# ✅ Utiliser gh directement
gh <commande>

# ✅ Si 401 → régénérer le token et réessayer
GH_TOKEN=$(.opencode/scripts/tesla-devops-token.sh) gh <commande>

# ❌ Jamais un token personnel hardcodé
GH_TOKEN=$(< /var/github-token.txt) gh <commande>
```

- Si 401 → exécuter `GH_TOKEN=$(.opencode/scripts/tesla-devops-token.sh) gh <commande>`
- Une commande à la fois — pas de `;` ou `&&`
- Ne jamais appeler `gh auth status`
- Ne jamais utiliser `--source`, `--remote` ou `--push` dans `gh repo create`
- Si 401 → regénérer avec `GH_TOKEN=$(.opencode/scripts/tesla-devops-token.sh) gh <commande>`

---

## Créer un repo GitHub

```bash
# Étape 1 — créer le repo
gh repo create <nom> --private

# Étape 2 — ajouter le remote
git remote add origin git@github.com:TheSpaceRangers/<nom>.git

# Étape 3 — pusher
git push -u origin main
```

---

## GitHub Projects

### Initialisation du board

```bash
gh project create --title "Plateforme Tickets Redondants" --owner "@me"
```

### Créer une US (issue parent)

```bash
gh issue create \
  --title "US-XXX : <titre>" \
  --body "<description avec critères d'acceptation>" \
  --label "user-story" \
  --milestone "Sprint X"
```

### Créer une sub-issue (tâche)

```bash
# 1. Créer l'issue tâche
gh issue create \
  --title "TASK-XXX : <titre>" \
  --body "<description>" \
  --label "task" \
  --milestone "Sprint X"

# 2. Lier comme sub-issue à l'US parent
gh api \
  repos/TheSpaceRangers/plateforme-detection-tickets-redondants/issues/<task-number>/sub_issues \
  --method POST \
  --field parent_issue_id=<us-issue-number>
```

### Mettre à jour le statut d'une issue

```bash
gh project item-edit <project-id> \
  --id <item-id> \
  --field-id <status-field-id> \
  --single-select-option-id <option-id>
```

### Fermer une issue validée

```bash
gh issue close <issue-number> --comment "Validé en fin de sprint X"
```

### Labels obligatoires

| Label        | Usage           |
| ------------ | --------------- |
| `user-story` | Issue US        |
| `task`       | Sub-issue tâche |
| `bug`        | Anomalie        |
| `blocked`    | Tâche bloquée   |

---

## Conventions Git

### Branches

```
feat/<description>     ← nouvelle fonctionnalité
fix/<description>      ← correction de bug
refactor/<description> ← refactoring
chore/<description>    ← maintenance
docs/<description>     ← documentation
ci/<description>       ← CI/CD
```

### Commits conventionnels

```
feat(backend): add redundancy prediction endpoint
fix(ml): correct TF-IDF vectorizer parameters
chore(deps): update scikit-learn to 1.4
ci: add frontend build job
```

### Règles PR

- Aucun push direct sur `main`
- Toute PR doit passer la CI avant merge
- Le qa-engineer valide avant merge

---

## Pipeline CI de référence

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-python:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install ruff
      - run: ruff check ml/src/ backend/app/

  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: lint-python
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r ml/requirements.txt -r backend/requirements.txt
      - run: pytest tests/ -v --junitxml=report.xml
      - uses: actions/upload-artifact@v4
        with:
          name: test-report
          path: report.xml
          retention-days: 7

  build-frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci && npm run build
```

**Règles GitHub Actions** : timeout max 15 min, artifacts 7 jours, secrets via GitHub Secrets, versions fixées (`@v4` pas `@latest`).

---

## Scripts d'installation

```bash
# ML
pip install -r ml/requirements.txt

# Backend
pip install -r backend/requirements.txt

# Frontend
cd frontend && npm install

# Base de données
docker-compose up -d postgres
```

---

## Checklist DevOps

- [ ] GH_TOKEN exporté en début de tâche
- [ ] Branches respectent les conventions de nommage
- [ ] Commits suivent le format conventionnel
- [ ] Aucun push direct sur main
- [ ] Issues GitHub Projects créées avec bons labels et milestones
- [ ] Sub-issues liées à leur US parent
- [ ] Secrets dans GitHub Secrets (jamais hardcodés)
- [ ] docker-compose.yml démarre sans erreur
- [ ] Badges CI à jour dans README
