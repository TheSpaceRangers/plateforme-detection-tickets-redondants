---
name: backend-engineering
description: FastAPI, services, schemas Pydantic, Repository Pattern, Singleton, PostgreSQL. Skill du backend-engineer.
version: 1.0.0
type: skill
---

# Backend Engineering Skill

> **Purpose**: Fournir au backend-engineer les patterns d'architecture et les standards FastAPI du projet.

---

## Structure backend/

```
backend/
├── app/
│   ├── main.py           ← Point d'entrée FastAPI + lifespan
│   ├── routers/          ← Un fichier par domaine fonctionnel
│   ├── schemas/          ← Modèles Pydantic (entrée/sortie)
│   ├── services/         ← Logique métier
│   └── db/               ← Accès PostgreSQL
│       └── repositories/ ← Un repository par entité
└── requirements.txt
```

---

## Endpoints obligatoires

```python
GET /health    ← statut de l'API et des services chargés
GET /version   ← version de l'API (ex: {"version": "1.0.0", "api": "v1"})
```

Tous les autres endpoints sont versionnés sous `/api/v1/`.

---

## Singleton — non négociable

Toute ressource partagée (modèles ML, connexion DB, services) doit être instanciée une seule fois via le pattern Singleton.

```python
# ✅ Correct — Singleton
class MonService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, dependency=None):
        if not hasattr(self, "_initialized"):
            self.dependency = dependency
            self._initialized = True
```

Chargement au lifespan FastAPI — une seule fois au démarrage :

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mon_service = MonService(dependency=charger_ressource())
    yield

app = FastAPI(lifespan=lifespan)
```

---

## Service Layer — obligatoire

La logique métier va **toujours** dans `services/`, jamais dans les routers.

```python
# ✅ Correct
class MonService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, input_data) -> OutputSchema:
        """Docstring obligatoire."""
        ...

# ❌ Interdit — logique dans le router
@router.post("/endpoint")
def endpoint(data: InputSchema):
    # logique métier ici
    ...
```

---

## Repository Pattern — obligatoire

Les accès PostgreSQL vont **toujours** dans `db/repositories/`, jamais dans les routers ou services.

```python
# ✅ Correct
class MonRepository:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_by_id(self, id: int) -> list:
        """Récupère une entité par son identifiant."""
        ...

# ❌ Interdit — SQL dans un router ou service
@router.get("/items")
def get_items(db=Depends(get_db)):
    return db.execute("SELECT * FROM table")
```

---

## Schemas Pydantic — obligatoires

Tout endpoint doit avoir un schema Pydantic strict en entrée **et** en sortie. Jamais de `dict` retourné directement.

```python
from pydantic import BaseModel
from typing import Optional

class InputSchema(BaseModel):
    field_one: str
    field_two: int
    optional_field: Optional[str] = None

class OutputSchema(BaseModel):
    result: bool
    score: float

# ✅ Correct
@router.post("/endpoint", response_model=OutputSchema)
def endpoint(data: InputSchema) -> OutputSchema: ...

# ❌ Interdit
@router.post("/endpoint")
def endpoint(data: dict) -> dict: ...
```

---

## Variables d'environnement

```python
import os
from dotenv import load_dotenv

load_dotenv()

MA_VARIABLE = os.getenv("MA_VARIABLE")  # ✅
# MA_VARIABLE = "valeur_en_dur"         # ❌ jamais
```

---

## Checklist backend

- [ ] Endpoints `/health` et `/version` implémentés
- [ ] Tous les services et repositories implémentent le pattern Singleton
- [ ] Logique métier dans `services/`, pas dans les routers
- [ ] SQL dans `db/repositories/`, pas dans les routers ni services
- [ ] Tous les endpoints utilisent des schemas Pydantic en entrée ET sortie
- [ ] Type hints sur toutes les fonctions
- [ ] Docstrings sur toutes les fonctions publiques
- [ ] Ressources lourdes chargées une fois via le lifespan
- [ ] Pas de credentials hardcodés — toujours via `os.getenv()`
- [ ] Pas de `SELECT *` sans filtre sur des tables volumineuses
