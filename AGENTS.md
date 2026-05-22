# Équipe de Développement — Plateforme Intelligente de Détection de Tickets Redondants

Projet développé avec opencode et une équipe d'agents spécialisés.

## Équipe

| Agent                    | Rôle                                                     | Mode                 |
| ------------------------ | -------------------------------------------------------- | -------------------- |
| `project-manager`        | Chef de projet global — vision, roadmap, qualité         | **primary** (défaut) |
| `scrum-master`           | Exécution agile — sprints, coordination, déblocage       | **primary**          |
| `devops-engineer`        | CI/CD, GitHub Projects, infrastructure                   | subagent             |
| `tech-lead`              | Qualité technique, revue de code, coordination engineers | subagent             |
| `compliance-lead`        | Coordination audits sécurité et conformité               | subagent             |
| `backend-engineer`       | Implémentation FastAPI, services, PostgreSQL             | subagent             |
| `frontend-engineer`      | Implémentation React, composants, hooks                  | subagent             |
| `ml-engineer`            | Pipeline ML, extraction, entraînement, évaluation        | subagent             |
| `qa-engineer`            | Tests unitaires et d'intégration                         | subagent             |
| `cybersecurity-engineer` | Audit sécurité technique (read-only)                     | subagent             |
| `rgpd-engineer`          | Audit conformité RGPD / ISO 27001 (read-only)            | subagent             |

## Hiérarchie

```
Utilisateur (escalade critique uniquement)
    │
    └── project-manager ← vision, roadmap, qualité globale
        │
        └── scrum-master ← exécution agile, sprints, coordination
            │
            ├── devops-engineer
            │   └── CI/CD, GitHub Projects, infrastructure
            │
            ├── tech-lead
            │   ├── backend-engineer
            │   ├── frontend-engineer
            │   ├── ml-engineer (si tâche ML explicite)
            │   └── qa-engineer
            │
            └── compliance-lead
                ├── cybersecurity-engineer (read-only)
                └── rgpd-engineer (read-only)
```

## Structure du projet

```
/
├── opencode.json
├── AGENTS.md                        ← vous êtes ici
├── .opencode/
│   ├── agents/                      ← Définitions des agents
│   ├── skills/                      ← Skills métier (dossiers avec SKILL.md)
│   └── context/                     ← Base de connaissances projet
│       ├── navigation.md
│       ├── project/
│       ├── domain/
│       └── technical/
├── ml/
│   ├── Dockerfile
│   └── .env.example
├── backend/
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── Dockerfile
│   └── .env.example
├── tests/
├── gestion-de-projet/
│   ├── STATUS.md
│   ├── backlog.md
│   ├── sprints/
│   └── rgpd/
├── docker-compose.yml
└── README.md
```

## Conventions

- **Langue** : communication en français, code et commentaires en anglais
- **Format** : Markdown GFM
- **Modèle** : `openai/GPT-5.5`
- **Secrets** : jamais hardcodés — via `.env` + GitHub Secrets

## Règles de délégation

| De                | Peut contacter                                                        |
| ----------------- | --------------------------------------------------------------------- |
| `project-manager` | `scrum-master` uniquement                                             |
| `scrum-master`    | `tech-lead`, `compliance-lead`, `devops-engineer`                     |
| `tech-lead`       | `backend-engineer`, `frontend-engineer`, `ml-engineer`, `qa-engineer` |
| `compliance-lead` | `cybersecurity-engineer`, `rgpd-engineer`                             |
| Tous les autres   | Personne — remontent à leur supérieur                                 |

## Distinction cybersecurity / rgpd

- **`cybersecurity-engineer`** : sécurité technique du code (credentials, OWASP, vulnérabilités)
- **`rgpd-engineer`** : conformité réglementaire (RGPD, ISO 27001, documentation)
- En cas de doute → solliciter les deux via le `compliance-lead`

## Changer d'agent

Les agents sont accessibles via leur **alias** (nom de personnalité) dans opencode :

```bash
opencode --agent Napoleon        # Project Manager
opencode --agent Eisenhower      # Scrum Master
opencode --agent Turing          # Tech Lead
opencode --agent Montesquieu     # Compliance Lead
opencode --agent Tesla           # DevOps Engineer
opencode --agent "Von Neumann"   # Backend Engineer
opencode --agent "Da Vinci"      # Frontend Engineer
opencode --agent Curie           # ML Engineer
opencode --agent Descartes       # QA Engineer
opencode --agent "Sun Tzu"       # Cybersecurity Engineer
opencode --agent Voltaire        # RGPD Engineer
```

## Mapping slug ↔ alias

| Slug (documentation)     | Alias (runtime opencode) |
| ------------------------ | ------------------------ |
| `project-manager`        | `Napoleon`               |
| `scrum-master`           | `Eisenhower`             |
| `tech-lead`              | `Turing`                 |
| `compliance-lead`        | `Montesquieu`            |
| `devops-engineer`        | `Tesla`                  |
| `backend-engineer`       | `Von Neumann`            |
| `frontend-engineer`      | `Da Vinci`               |
| `ml-engineer`            | `Curie`                  |
| `qa-engineer`            | `Descartes`              |
| `cybersecurity-engineer` | `Sun Tzu`                |
| `rgpd-engineer`          | `Voltaire`               |

## Vérification rapide

```bash
find .opencode/agents -name "*.md" | sort
find .opencode/skills -name "SKILL.md" | sort
find .opencode/context -name "*.md" | sort
```
