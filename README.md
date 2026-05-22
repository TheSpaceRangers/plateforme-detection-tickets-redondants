# Plateforme Intelligente de Détection de Tickets Redondants

> Plateforme IA privée et auto-hébergée pour la détection automatique de tickets redondants sur HaloPSA — SYNAPPSE

---

## Prérequis

| Outil          | Version minimale |
| -------------- | ---------------- |
| Python         | 3.11+            |
| Node.js        | 20+              |
| Docker         | 24+              |
| Docker Compose | 2.x              |
| Git            | 2.x              |
| opencode       | dernière version |

---

## Installation

### 1. Cloner le repo

```bash
git clone git@github.com:TheSpaceRangers/plateforme-detection-tickets-redondants.git
cd plateforme-detection-tickets-redondants
```

### 2. Variables d'environnement

```bash
# ML
cp ml/.env.example ml/.env

# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

Renseigner les valeurs dans chaque `.env` :

```bash
# HaloPSA
HALOPSA_BASE_URL=https://wiptservicedesk.halopsa.com
HALOPSA_CLIENT_ID=<votre_client_id>
HALOPSA_CLIENT_SECRET=<votre_client_secret>

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=synappse_tickets
POSTGRES_USER=<votre_user>
POSTGRES_PASSWORD=<votre_password>

# Backend
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Base de données

```bash
docker-compose up -d postgres
```

### 4. Pipeline ML

```bash
cd ml
pip install -r requirements.txt
```

### 5. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 6. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Lancer avec Docker

```bash
docker-compose up -d
```

Services disponibles :

| Service        | URL                   |
| -------------- | --------------------- |
| API FastAPI    | http://localhost:8000 |
| Frontend React | http://localhost:5173 |
| PostgreSQL     | localhost:5432        |

---

## Système agentique

Ce projet utilise **opencode** avec une équipe de 11 agents spécialisés.

```bash
# Lancer opencode (agent par défaut : Napoleon — Project Manager)
opencode

# Lancer un agent spécifique
opencode -a scrum-master
opencode -a ml-engineer
```

| Agent                    | Nom         | Rôle                               |
| ------------------------ | ----------- | ---------------------------------- |
| `project-manager`        | Napoleon    | Vision, roadmap, qualité globale   |
| `scrum-master`           | Eisenhower  | Exécution agile, sprints           |
| `devops-engineer`        | Tesla       | CI/CD, GitHub Projects             |
| `tech-lead`              | Turing      | Qualité technique, revue de code   |
| `compliance-lead`        | Montesquieu | Audits sécurité et conformité      |
| `backend-engineer`       | Von Neumann | FastAPI, PostgreSQL                |
| `frontend-engineer`      | Da Vinci    | React, shadcn/ui                   |
| `ml-engineer`            | Curie       | Pipeline ML                        |
| `qa-engineer`            | Descartes   | Tests et validation                |
| `cybersecurity-engineer` | Sun Tzu     | Audit sécurité (read-only)         |
| `rgpd-engineer`          | Voltaire    | Audit RGPD / ISO 27001 (read-only) |

Voir `AGENTS.md` pour la hiérarchie complète et les règles de délégation.

---

## Structure du projet

```
├── ml/               ← Pipeline Machine Learning
├── backend/          ← API FastAPI
├── frontend/         ← Interface React
├── tests/            ← Tests unitaires et d'intégration
├── gestion-de-projet/← Sprints, backlog, RGPD
├── .opencode/        ← Agents, skills, context
├── AGENTS.md         ← Documentation équipe agentique
├── opencode.json     ← Configuration opencode
└── docker-compose.yml
```

---

## Tests

```bash
# Linting Python
ruff check ml/src/ backend/app/

# Tests
pytest tests/ -v

# Build frontend
cd frontend && npm run build
```

---

## Contexte académique

Projet réalisé dans le cadre du **Mastère Data et Intelligence Artificielle** (RNCP 37137) à **Nexa Digital School**, en alternance chez **SYNAPPSE**.

- Référence Abraxio : PRJ000229
- Soutenance : Octobre 2026
