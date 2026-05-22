---
name: scrum
description: Exécution agile — sprints, US, tâches, cérémonies, coordination leads. Skill du scrum-master.
version: 1.0.0
type: skill
---

# Scrum Skill

> **Purpose**: Fournir au scrum-master les patterns pour générer des sprints, US et tâches de qualité.

---

## Format d'une User Story

```
US-XXX : <titre court>
En tant que <rôle>, je veux <action> afin de <bénéfice>.

Critères d'acceptation :
- [ ] ...
- [ ] ...

Tâches :
- [ ] TASK-XXX : <description> → <agent responsable>
- [ ] TASK-XXX : <description> → <agent responsable>

Assigné à : tech-lead | compliance-lead | devops-engineer
Estimation : S | M | L

Definition of Done :
- [ ] Toutes les tâches complétées
- [ ] Validée par le lead responsable
- [ ] Reflétée sur GitHub Projects
```

---

## Routing des tâches

| Type de tâche                          | Déléguer à                               |
| -------------------------------------- | ---------------------------------------- |
| Implémentation backend / frontend / ML | `tech-lead`                              |
| Tests et validation du code            | `tech-lead` (qui délègue au qa-engineer) |
| Audit sécurité technique               | `compliance-lead`                        |
| Audit conformité RGPD / ISO 27001      | `compliance-lead`                        |
| GitHub Projects, CI/CD, infra          | `devops-engineer`                        |

---

## Cérémonies

| Cérémonie       | Durée     | Objectif                                    |
| --------------- | --------- | ------------------------------------------- |
| Sprint Planning | 30-60 min | Générer les US et tâches, briefer les leads |
| Daily Standup   | 5-10 min  | Sync avancement, déblocage                  |
| Sprint Review   | 15-30 min | Valider les livrables avec le PM            |
| Sprint Retro    | 15-30 min | Amélioration continue                       |

---

## Instructions GitHub Projects au devops-engineer

```
task("devops-engineer", """
Sprint X — Initialisation GitHub Projects

Actions à réaliser :
1. Créer les issues pour les US suivantes :
   - US-XXX : <titre> (label: user-story, milestone: Sprint X)
   - US-XXX : <titre> (label: user-story, milestone: Sprint X)

2. Pour chaque US, créer les sub-issues pour les tâches :
   - TASK-XXX : <description> (label: task)

3. Placer toutes les issues sur le board en statut "Sprint"

Token : GH_TOKEN=$(cat /var/github-token.txt)
""")
```

---

## Checklist de sprint

- [ ] Les US ont des critères d'acceptation clairs
- [ ] Chaque US contient ses tâches avec l'agent assigné
- [ ] Le devops-engineer a été instruit pour GitHub Projects
- [ ] Le sprint a une capacité réaliste
- [ ] Les dépendances entre US sont identifiées
- [ ] La Definition of Done est respectée avant fermeture
- [ ] Le PM est informé en fin de sprint
