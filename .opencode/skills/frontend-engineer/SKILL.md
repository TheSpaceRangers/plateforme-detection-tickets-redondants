---
name: frontend-engineering
description: React, Vite, Tailwind CSS, shadcn/ui, hooks, composants. Skill du frontend-engineer.
version: 1.0.0
type: skill
---

# Frontend Engineering Skill

> **Purpose**: Fournir au frontend-engineer les standards React et les patterns d'architecture du projet.

---

## Stack imposée

| Outil        | Usage         | Interdit                          |
| ------------ | ------------- | --------------------------------- |
| React 18     | Framework UI  | —                                 |
| Vite         | Bundler       | Create React App                  |
| JavaScript   | Langage       | TypeScript                        |
| Tailwind CSS | Styling       | CSS inline, autres frameworks CSS |
| shadcn/ui    | Composants UI | Autres librairies de composants   |

---

## Structure frontend/

```
frontend/
├── src/
│   ├── components/   ← Composants réutilisables (UI pure)
│   ├── pages/        ← Pages de l'application
│   ├── hooks/        ← Custom hooks (fetch, état, effets)
│   └── lib/
│       └── config.js ← Config API (VITE_API_BASE_URL)
├── package.json
└── vite.config.js
```

---

## Component Pattern — obligatoire

Les composants sont de la **UI pure** — pas de logique, pas de fetch.

```javascript
// ✅ Correct — composant sans logique
function MonComposant({ data }) {
    return (
        <div className="rounded-lg border p-4">
            <h3 className="text-lg font-semibold">{data.title}</h3>
        </div>
    );
}

// ❌ Interdit — logique ou fetch dans le composant
function MonComposant() {
    useEffect(() => {
        fetch("/api/resource").then(...);
    }, []);
}
```

---

## Custom Hooks — toute la logique ici

```javascript
// ✅ Correct — fetch et état dans un hook
function useMonRessource() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/ma-ressource`)
      .then((res) => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

// Utilisation dans un composant
function MaPage() {
  const { data, loading, error } = useMonRessource();
  // rendu uniquement
}
```

---

## shadcn/ui — premier réflexe

Avant de créer un élément UI from scratch, vérifier si shadcn/ui le couvre. Si oui, l'utiliser.

```javascript
// ✅ Correct — importer depuis shadcn/ui
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

// ❌ Interdit — créer un composant qu'shadcn/ui couvre déjà
function MonBouton({ children }) {
  return <button className="...">{children}</button>;
}
```

---

## Tailwind CSS — styling uniquement

```javascript
// ✅ Correct
<div className="flex items-center gap-4 rounded-lg p-4">

// ❌ Interdit — CSS inline
<div style={{ display: 'flex', padding: '16px' }}>
```

---

## Configuration API

```javascript
// src/lib/config.js
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Utilisation dans les hooks
import { API_BASE_URL } from "@/lib/config";
fetch(`${API_BASE_URL}/api/v1/ma-ressource`);
```

---

## Checklist frontend

- [ ] Pas de logique dans les composants — tout dans des hooks
- [ ] Pas de fetch direct dans les composants
- [ ] Pas de CSS inline — Tailwind uniquement
- [ ] shadcn/ui utilisé pour les éléments UI existants dans la lib
- [ ] URL API via `import.meta.env.VITE_API_BASE_URL`
- [ ] Gestion des états loading et error dans chaque hook
- [ ] JavaScript uniquement — pas de TypeScript
- [ ] Imports shadcn/ui depuis `@/components/ui/`
