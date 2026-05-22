# Technique — Stack

## Stack retenue

| Couche                  | Technologies                                |
| ----------------------- | ------------------------------------------- |
| Extraction & traitement | Python 3.11+, Requests, Pandas              |
| NLP                     | spaCy (modèle français)                     |
| Base de données         | PostgreSQL 15+                              |
| Machine Learning        | scikit-learn, TF-IDF, Grid Search, joblib   |
| Visualisation           | Matplotlib, Plotly                          |
| Backend                 | FastAPI + Uvicorn                           |
| Frontend                | Vite + React 18 + shadcn/ui + Tailwind CSS  |
| LLM / RAG               | Ollama (Mistral/LLaMA), ChromaDB, LangChain |
| Gestion de projet       | Abraxio, Kanban                             |

## Contraintes non négociables

- Frontend en JavaScript — pas de TypeScript
- Hébergement 100% local — pas de cloud
- Credentials jamais hardcodés — via variables d'environnement
- PostgreSQL — pas de SQLite

## Dépendances RNCP Bloc 3 — obligatoires

Ces algorithmes doivent figurer dans le projet pour satisfaire le référentiel :

- KNN, Random Forest, Decision Tree, Logistic Regression (scikit-learn)
- Train/test split ≥ 70/30
- Métriques : Accuracy (obligatoire), F1, Recall
- Grid Search
- Application web intégrant le modèle
