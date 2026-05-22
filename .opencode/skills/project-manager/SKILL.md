---
name: project-management
description: Pilotage stratégique — roadmap, STATUS.md, coordination scrum-master. Skill du project-manager.
version: 1.0.0
type: skill
---

# Project Management Skill

> **Purpose**: Fournir au PM les outils de pilotage pour superviser sans exécuter.

---

## Responsabilités du PM

| Ce qu'il fait             | Ce qu'il ne fait PAS                     |
| ------------------------- | ---------------------------------------- |
| Lit la note de cadrage    | Écrit du code                            |
| Déduit roadmap et jalons  | Modifie des fichiers hors STATUS.md      |
| Maintient STATUS.md       | Contacte les agents sous le scrum-master |
| Valide les fins de sprint | Lance des commandes bash                 |
| Briefer le scrum-master   | Produit des livrables techniques         |

---

## STATUS.md — Format de référence

```markdown
# STATUS — Plateforme Détection Tickets Redondants

**Dernière mise à jour** : YYYY-MM-DD

## Roadmap

| Lot   | Description           | Statut      |
| ----- | --------------------- | ----------- |
| Lot 1 | Cadrage et analyse    | ✅ Terminé  |
| Lot 2 | Extraction et données | 🔄 En cours |
| Lot 3 | Pipeline ML           | ⏳ À venir  |
| Lot 4 | Application web       | ⏳ À venir  |
| Lot 5 | Tests et déploiement  | ⏳ À venir  |

## Sprint courant

**Sprint X** — Objectif : ...

- [ ] US-XXX : ...
- [x] US-XXX : ...

## Décisions et risques

| Date | Décision / Risque | Impact |
| ---- | ----------------- | ------ |
| ...  | ...               | ...    |
```

---

## Délégation au scrum-master

Pattern de brief de sprint :

```
task("scrum-master", """
Sprint X — Objectif : <objectif>

US à traiter :
- US-XXX : <titre> (priorité haute)
- US-XXX : <titre>

Contraintes :
- <contrainte 1>
- <contrainte 2>

Critères de succès du sprint :
- <critère 1>
- <critère 2>
""")
```

---

## Checklist de pilotage

- [ ] Note de cadrage lue et roadmap documentée dans STATUS.md
- [ ] Jalons identifiés et suivis
- [ ] Scrum-master briefé sur les priorités du sprint en cours
- [ ] Livrables de fin de sprint validés contre la roadmap
- [ ] Risques documentés dans STATUS.md
