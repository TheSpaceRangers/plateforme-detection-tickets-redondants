---
name: compliance-lead
description: Coordination des audits sécurité et conformité réglementaire. Skill du compliance-lead.
version: 1.0.0
type: skill
---

# Compliance Lead Skill

> **Purpose**: Fournir au compliance-lead les patterns de délégation, les déclencheurs d'audit et le format de synthèse.

---

## Distinction cybersecurity / rgpd

| Agent                    | Périmètre                                                                                                                        |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| `cybersecurity-engineer` | Sécurité **technique** : credentials exposés, OWASP LLM, vulnérabilités, permissions agents, endpoints non sécurisés             |
| `rgpd-engineer`          | Conformité **réglementaire** : RGPD, ISO 27001, registre de traitements, cartographie données personnelles, droits des personnes |

> En cas de doute → solliciter les deux.

---

## Quand déclencher un audit

| Événement                          | cybersecurity | rgpd |
| ---------------------------------- | ------------- | ---- |
| Nouvelle fonctionnalité backend    | ✅            | —    |
| Nouveau traitement de données      | —             | ✅   |
| Modification pipeline ML           | ✅            | ✅   |
| Accès à de nouveaux champs HaloPSA | —             | ✅   |
| Fin de sprint                      | ✅            | ✅   |
| Avant livraison finale             | ✅            | ✅   |

---

## Points de vigilance SYNAPPSE

| Risque                                                  | Agent                    |
| ------------------------------------------------------- | ------------------------ |
| Credentials HaloPSA dans le code                        | `cybersecurity-engineer` |
| Credentials PostgreSQL dans le code                     | `cybersecurity-engineer` |
| Endpoints FastAPI sans authentification                 | `cybersecurity-engineer` |
| Données personnelles dans les tickets (noms, emails)    | `rgpd-engineer`          |
| Modèles joblib contenant des données d'entraînement     | les deux                 |
| Logs d'entraînement ML tracant des données personnelles | les deux                 |
| Registre de traitements à jour                          | `rgpd-engineer`          |

---

## Format de brief vers les agents

```
task("cybersecurity-engineer" | "rgpd-engineer", """
Audit — Sprint X / <composant>

Périmètre :
- Fichiers : <liste>
- Composants : <liste>
- Aspects spécifiques : <liste>

Points de vigilance prioritaires :
- <point 1>
- <point 2>

Format de rapport attendu :
[CRITICAL/HIGH/MEDIUM/LOW] Fichier:ligne
Description : ...
Correction suggérée : ...
""")
```

---

## Format de synthèse au scrum-master

```markdown
## Synthèse d'audit — Sprint X

### Périmètre audité

- Fichiers : ...
- Composants : ...

### Cybersécurité

- [CRITICAL] ...
- [HIGH] ...

### RGPD / ISO 27001

- [HIGH] ...
- [MEDIUM] ...

### Actions correctives pour le tech-lead

1. ...
2. ...

### Statut global

✅ Conforme | ⚠️ Écarts mineurs | ❌ Écarts bloquants
```
