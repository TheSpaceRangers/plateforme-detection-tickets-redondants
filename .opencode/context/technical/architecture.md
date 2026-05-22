# Technique — Architecture

## Mono-repo

```
plateforme-detection-tickets-redondants/
├── ml/                   ← Pipeline Machine Learning
│   ├── data/             ← Données (gitignored)
│   ├── notebooks/        ← Exploration
│   ├── src/
│   │   ├── extraction/
│   │   ├── preprocessing/
│   │   ├── training/
│   │   └── evaluation/
│   ├── models/           ← Modèles sérialisés (gitignored)
│   └── requirements.txt
├── backend/              ← API FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── db/
│   │       └── repositories/
│   └── requirements.txt
├── frontend/             ← Vite + React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── lib/
│   └── package.json
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── gestion-de-projet/
│   ├── STATUS.md
│   ├── backlog.md
│   ├── sprints/
│   └── rgpd/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Base de données PostgreSQL

Tables principales :

| Table       | Description                            |
| ----------- | -------------------------------------- |
| tickets     | Tickets importés depuis HaloPSA        |
| predictions | Log des prédictions (traçabilité RGPD) |
| clients     | Référentiel clients ESSMS              |
| categories  | Référentiel catégories HaloPSA         |

Index à créer sur les colonnes utilisées pour le groupement et les requêtes fréquentes.

## Variables d'environnement

```bash
# HaloPSA
HALOPSA_BASE_URL=
HALOPSA_CLIENT_ID=
HALOPSA_CLIENT_SECRET=

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=synappse_tickets
POSTGRES_USER=
POSTGRES_PASSWORD=

# Backend
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```
