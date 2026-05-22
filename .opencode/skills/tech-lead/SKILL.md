---
name: tech-lead
description: Standards de qualité technique — Clean Code, SOLID, design patterns, revue de code. Skill du tech-lead.
version: 1.0.0
type: skill
---

# Tech Lead Skill

> **Purpose**: Fournir au tech-lead les standards à imposer et la checklist de revue de code.

---

## Routing des engineers

| Tâche                                                   | Engineer            |
| ------------------------------------------------------- | ------------------- |
| Endpoints FastAPI, services, schemas Pydantic           | `backend-engineer`  |
| Composants React, pages, hooks, shadcn/ui               | `frontend-engineer` |
| Pipeline ML, extraction HaloPSA, preprocessing, modèles | `ml-engineer`       |
| Tests unitaires et d'intégration                        | `qa-engineer`       |

---

## Standards Clean Code

| Règle           | ✅ Correct                                             | ❌ Interdit                            |
| --------------- | ------------------------------------------------------ | -------------------------------------- |
| Nommage         | `predict_redundancy()`, `redundant_tickets`            | `data`, `tmp`, `res`, `obj`            |
| Taille fonction | ≤ 20 lignes                                            | > 20 lignes sans décomposition         |
| Paramètres      | ≤ 3 paramètres                                         | > 3 → utiliser un objet/dataclass      |
| Commentaires    | Expliquent le _pourquoi_                               | Expliquent le _quoi_ (le code le fait) |
| Docstrings      | Obligatoires sur toutes les fonctions publiques Python | Absent                                 |

---

## Principes SOLID appliqués au projet

| Principe                    | Application                                                                |
| --------------------------- | -------------------------------------------------------------------------- |
| **S** Single Responsibility | `extraction/`, `preprocessing/`, `training/` strictement séparés           |
| **O** Open/Closed           | Classifieurs interchangeables dans le pipeline sans modifier le pipeline   |
| **L** Liskov                | Tout classifieur scikit-learn substituable dans le pipeline                |
| **I** Interface Segregation | Routers FastAPI n'exposent que ce dont le client a besoin                  |
| **D** Dependency Inversion  | Services FastAPI dépendent d'abstractions, pas d'implémentations concrètes |

---

## Design Patterns imposés

### Pipeline Pattern (ML)

```python
# ✅ Correct
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", RandomForestClassifier()),
])

# ❌ Interdit
X = tfidf.fit_transform(X)
y_pred = clf.predict(X)
```

### Repository Pattern (Backend — accès données)

```python
# ✅ Correct
class TicketRepository:
    def get_by_client(self, client_id: int) -> list[Ticket]: ...

# ❌ Interdit dans un router
@router.get("/tickets")
def get_tickets(db = Depends(get_db)):
    return db.execute("SELECT * FROM tickets")
```

### Service Layer (Backend — logique métier)

```python
# ✅ Correct
class RedundancyService:
    def predict(self, ticket: Ticket) -> RedundancyResult: ...

# ❌ Interdit dans un router
@router.post("/predict")
def predict(ticket: Ticket):
    model = joblib.load("models/clf.joblib")
    return model.predict([ticket.summary])
```

### Component Pattern (Frontend)

```javascript
// ✅ Correct — logique de fetch dans un hook
function useTickets() {
    const [tickets, setTickets] = useState([]);
    useEffect(() => { fetchTickets().then(setTickets) }, []);
    return tickets;
}

// ❌ Interdit — fetch dans le composant
function TicketList() {
    useEffect(() => { fetch("/api/tickets").then(...) }, []);
}
```

---

## Checklist de revue de code

### Structure générale

- [ ] Fichiers dans les bons répertoires (structure mono-repo respectée)
- [ ] Pas de code mort ou commenté
- [ ] Pas de `print()` de debug

### Clean Code

- [ ] Nommage explicite et intentionnel
- [ ] Fonctions ≤ 20 lignes et ≤ 3 paramètres
- [ ] Docstrings présentes sur toutes les fonctions publiques Python
- [ ] Commentaires expliquent le pourquoi, pas le quoi

### SOLID & Patterns

- [ ] SRP respecté — chaque module/fonction a une seule responsabilité
- [ ] Pipeline Pattern utilisé pour tout le ML
- [ ] Repository Pattern utilisé pour tous les accès PostgreSQL
- [ ] Service Layer pour toute la logique métier FastAPI
- [ ] Logique de fetch dans les custom hooks React

### Sécurité minimale

- [ ] Pas de credentials hardcodés
- [ ] Variables d'environnement via `.env` + `python-dotenv`
- [ ] Pas de `SELECT *` sans filtre sur des tables volumineuses
