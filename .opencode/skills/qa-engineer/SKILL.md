---
name: qa
description: Tests unitaires et d'intégration — AAA, positif/négatif, mocking, pytest. Skill du qa-engineer.
version: 1.0.0
type: skill
---

# QA Skill

> **Purpose**: Fournir au qa-engineer les patterns de test adaptés au projet SYNAPPSE.

---

## Structure des tests

```
tests/
├── unit/
│   ├── ml/           ← Tests unitaires pipeline ML
│   ├── backend/      ← Tests unitaires FastAPI services
│   └── frontend/     ← Tests unitaires composants React
├── integration/
│   ├── api/          ← Tests d'intégration endpoints
│   └── ml/           ← Tests d'intégration pipeline complet
├── fixtures/         ← Données de test partagées
└── conftest.py       ← Fixtures pytest partagées
```

---

## Pattern AAA — obligatoire sur tous les tests

```python
def test_predict_redundancy_returns_true_for_duplicate():
    # Arrange
    ticket = Ticket(client_id=1, category_1="réseau", summary="Pas d'accès internet")
    existing_ticket = Ticket(client_id=1, category_1="réseau", summary="Internet en panne")
    service = RedundancyService(model=mock_model)

    # Act
    result = service.predict(ticket, context=[existing_ticket])

    # Assert
    assert result.is_redundant is True
```

---

## Positif + Négatif — obligatoire sur chaque comportement

```python
# ✅ Test positif — cas nominal
def test_predict_redundancy_returns_true_for_duplicate():
    ...

# ✅ Test négatif — cas d'échec ou edge case
def test_predict_redundancy_returns_false_for_different_client():
    ...

def test_predict_redundancy_returns_false_outside_time_window():
    ...
```

---

## Mocking des dépendances externes

```python
from unittest.mock import MagicMock, patch

# ✅ Mocker HaloPSA
@patch("ml.src.extraction.halopsa.requests.get")
def test_extract_tickets_returns_dataframe(mock_get):
    mock_get.return_value.json.return_value = {"tickets": [...]}
    result = extract_tickets()
    assert isinstance(result, pd.DataFrame)

# ✅ Mocker PostgreSQL
@patch("backend.app.db.get_db")
def test_get_tickets_endpoint(mock_db, client):
    mock_db.return_value = MagicMock()
    response = client.get("/api/v1/tickets")
    assert response.status_code == 200

# ✅ Mocker joblib
@patch("backend.app.services.redundancy.joblib.load")
def test_redundancy_service_loads_model(mock_load):
    mock_load.return_value = MagicMock()
    service = RedundancyService()
    assert service.model is not None
```

---

## Checklist QA par couche

### Pipeline ML (`ml/`)

- [ ] Extraction HaloPSA retourne un DataFrame valide (mocké)
- [ ] Preprocessing ne lève pas d'exception sur des tickets vides ou malformés
- [ ] Les 4 classifieurs s'entraînent sans erreur sur le jeu d'entraînement
- [ ] GridSearchCV converge et retourne un `best_estimator_`
- [ ] Fichiers `.joblib` générés dans `ml/models/`
- [ ] Métriques (accuracy, F1, recall) sont reproductibles (random_state=42)
- [ ] Train/test split respecte le ratio minimum 70/30

### Backend FastAPI (`backend/`)

- [ ] Tous les endpoints répondent avec le bon status code
- [ ] Les schémas Pydantic valident correctement les entrées
- [ ] Les schémas Pydantic rejettent les entrées invalides (test négatif)
- [ ] Les modèles joblib se chargent au démarrage sans erreur (mocké)
- [ ] Les endpoints de prédiction retournent un résultat cohérent

### Frontend React (`frontend/`)

- [ ] L'application démarre sans erreur
- [ ] Les appels API retournent les données attendues (mockés)
- [ ] Aucune erreur console en navigation normale

---

## Commandes d'exécution

```bash
# Linting Python
ruff check ml/src/ backend/app/

# Tests avec rapport
pytest tests/ -v --junitxml=report.xml

# Tests avec couverture
pytest tests/ --cov=ml/src --cov=backend/app --cov-report=term-missing
```

---

## Règles absolues

- Ne jamais modifier le code source — reporter les anomalies au tech-lead
- Ne jamais faire d'appels réseau réels dans les tests
- Toujours proposer le plan de test avant d'écrire
- Un test qui passe ne signifie pas que le code est correct — chercher les edge cases
