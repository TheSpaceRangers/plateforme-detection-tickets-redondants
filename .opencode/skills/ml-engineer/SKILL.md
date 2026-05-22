---
name: ml-engineering
description: Pipeline ML — extraction, preprocessing NLP, algorithmes, métriques, sérialisation. Skill du ml-engineer.
version: 1.0.0
type: skill
---

# ML Engineering Skill

> **Purpose**: Fournir au ml-engineer les standards du pipeline, les algorithmes à explorer et les métriques attendues.

---

## Structure ml/

```
ml/
├── data/
│   ├── raw/              ← Données brutes (gitignored)
│   └── processed/        ← Données nettoyées (gitignored)
├── notebooks/            ← Exploration et expérimentation
├── src/
│   ├── extraction/       ← Extraction source de données
│   ├── preprocessing/    ← Nettoyage, NLP, vectorisation
│   ├── training/         ← Entraînement et comparaison
│   └── evaluation/       ← Métriques et rapports
├── models/               ← Modèles sérialisés .joblib (gitignored)
└── requirements.txt
```

---

## Exploration des données — toujours en premier

Avant toute modélisation, explorer exhaustivement le dataset :

```python
import pandas as pd

df = pd.DataFrame(data)

# Explorer la structure complète
print(df.dtypes)
print(df.describe())
print(df.isnull().sum())
print(df.nunique())
```

**Les features à utiliser sont déduites de l'exploration — jamais supposées a priori.**

---

## Preprocessing NLP

```python
import spacy
nlp = spacy.load("fr_core_news_sm")

def preprocess_text(text: str) -> str:
    """Lemmatisation et suppression des stopwords."""
    doc = nlp(text.lower())
    tokens = [t.lemma_ for t in doc if not t.is_stop and not t.is_punct]
    return " ".join(tokens)
```

Vectorisation de base : **TF-IDF**. Alternatives à explorer selon les résultats : Word2Vec, FastText, sentence-transformers.

---

## Pipeline Pattern — obligatoire

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

# ✅ Correct — tout dans un pipeline
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("clf", MonClassifieur(random_state=42)),
])

# ❌ Interdit — transformations manuelles hors pipeline
X = tfidf.fit_transform(X)
y_pred = clf.predict(X)
```

---

## Split — règles obligatoires

```python
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42  # Partout, sans exception

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.3,          # Minimum 70/30
    random_state=RANDOM_STATE,
    stratify=y              # Obligatoire si classes déséquilibrées
)
```

---

## Algorithmes — exploration exhaustive obligatoire

Ne jamais se limiter à un sous-ensemble. Explorer tout ce qui est pertinent.

### Machine Learning classique (scikit-learn)

```python
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
# XGBoost, LightGBM si installés
```

### Deep Learning

```python
# TensorFlow / Keras
from tensorflow import keras

# PyTorch
import torch

# Hugging Face — NLP français
from transformers import CamembertForSequenceClassification
```

---

## Optimisation des hyperparamètres

```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

# Grid Search — espaces réduits
gs = GridSearchCV(pipeline, param_grid, cv=5, scoring="f1", n_jobs=-1)

# Randomized Search — espaces larges
rs = RandomizedSearchCV(pipeline, param_distributions, n_iter=50, cv=5, scoring="f1")

# Optuna — optimisation bayésienne si nécessaire
import optuna
```

---

## Métriques

| Métrique                 | Justification                          |
| ------------------------ | -------------------------------------- |
| **Accuracy**             | Obligatoire (RNCP Bloc 3)              |
| **F1-score**             | Prioritaire — classes déséquilibrées   |
| **Recall**               | Critique — minimiser les faux négatifs |
| **ROC-AUC**              | Vision globale du classifieur          |
| **Matrice de confusion** | Analyse détaillée des erreurs          |

### Déséquilibre de classes

Si les classes sont déséquilibrées, traiter et documenter :

```python
# Option 1 — class_weight
clf = RandomForestClassifier(class_weight="balanced", random_state=42)

# Option 2 — SMOTE
from imblearn.over_sampling import SMOTE
X_resampled, y_resampled = SMOTE().fit_resample(X_train, y_train)
```

---

## Sérialisation

```python
import joblib

# Nommage obligatoire : <tâche>_<algorithme>_v<version>.joblib
joblib.dump(best_model, "ml/models/<tâche>_<algorithme>_v1.joblib")
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

## Checklist ML

- [ ] Exploration exhaustive du dataset avant de choisir les features
- [ ] Preprocessing NLP appliqué uniformément train/test
- [ ] Pipeline Pattern utilisé — pas de transformations manuelles
- [ ] Split ≥ 70/30 avec `stratify=y` et `random_state=42`
- [ ] Tous les algorithmes pertinents testés (ML + deep learning si applicable)
- [ ] Déséquilibre de classes traité et documenté
- [ ] Métriques loggées et comparées dans un tableau
- [ ] Modèle final sérialisé avec le bon nommage
- [ ] Résultats documentés dans `ml/notebooks/`
