---
name: rgpd
description: Conformité réglementaire — RGPD, ISO 27001, registre de traitements, données personnelles. Skill du rgpd-engineer.
version: 1.0.0
type: skill
---

# RGPD Skill

> **Purpose**: Fournir au rgpd-engineer la checklist de conformité RGPD et ISO 27001 adaptée au projet SYNAPPSE.

---

## Contexte projet

Le projet traite des tickets de support IT de clients du secteur médico-social (ESSMS). Les données traitées sont des données professionnelles (techniciens, clients IT) — pas de données patients. Le traitement est auto-hébergé sur l'infrastructure SYNAPPSE.

**Données personnelles potentielles dans les tickets HaloPSA** : noms de techniciens, adresses email, identifiants clients, descriptions d'incidents pouvant mentionner des personnes.

---

## Documents réglementaires attendus

| Document                             | Emplacement attendu                              | Statut à vérifier  |
| ------------------------------------ | ------------------------------------------------ | ------------------ |
| Registre des activités de traitement | `gestion-de-projet/rgpd/registre-traitements.md` | Existe et à jour   |
| Cartographie des données             | `gestion-de-projet/rgpd/cartographie-donnees.md` | Existe et complète |
| Politique de sécurité                | `gestion-de-projet/rgpd/politique-securite.md`   | Existe             |
| Charte éthique IA                    | `gestion-de-projet/rgpd/charte-ethique.md`       | Existe             |

---

## Checklist RGPD

### Base légale et registre

- [ ] La base légale du traitement est identifiée (intérêt légitime, contrat)
- [ ] Le registre des activités de traitement (RAT) est présent et à jour
- [ ] Les durées de conservation sont définies pour chaque catégorie de données

### Données personnelles

- [ ] La cartographie des données personnelles est complète (`tickets` table, `predictions` table)
- [ ] Les champs contenant des données personnelles sont identifiés dans le dictionnaire de données
- [ ] Une procédure d'anonymisation ou pseudonymisation est définie pour les données d'entraînement

### Droits des personnes

- [ ] Les droits d'accès, rectification et suppression sont documentés
- [ ] Une procédure de réponse aux demandes d'exercice des droits existe

### Sous-traitants

- [ ] HaloPSA est identifié comme sous-traitant dans le registre
- [ ] Un DPA (Data Processing Agreement) est référencé ou en place

### Sécurité (Article 32 RGPD)

- [ ] Les mesures techniques de sécurité sont documentées
- [ ] Une procédure de notification de violation de données existe

---

## Checklist ISO 27001

### Gestion des actifs

- [ ] Les actifs informationnels sont inventoriés (base PostgreSQL, modèles joblib, API HaloPSA)
- [ ] Les actifs sont classifiés selon leur sensibilité

### Contrôle d'accès

- [ ] Les accès sont accordés selon le principe du moindre privilège
- [ ] Les credentials sont gérés de manière sécurisée (pas de hardcoding)

### Cryptographie

- [ ] Les données en transit sont chiffrées (HTTPS sur les endpoints FastAPI)
- [ ] Les données au repos sensibles sont protégées

### Gestion des incidents

- [ ] Une procédure de gestion des incidents de sécurité est définie
- [ ] Les incidents sont tracés et documentés

---

## Commandes d'audit utiles

```bash
# Vérifier la présence des documents réglementaires
find gestion-de-projet/rgpd/ -type f -name "*.md"

# Chercher des données personnelles potentielles dans le code
grep -rn "email\|nom\|name\|prenom\|firstname\|lastname" ml/src/ backend/app/ \
  --include="*.py"

# Vérifier le schéma de la base de données
find . -name "*.sql" -o -name "*.py" | xargs grep -l "CREATE TABLE" 2>/dev/null
```

---

## Niveaux de criticité

| Niveau       | Exemples                                                                        |
| ------------ | ------------------------------------------------------------------------------- |
| **CRITICAL** | Absence totale de registre de traitements, données personnelles non identifiées |
| **HIGH**     | Durées de conservation non définies, pas de procédure de violation              |
| **MEDIUM**   | Document réglementaire incomplet, sous-traitant non référencé                   |
| **LOW**      | Document existant mais non mis à jour récemment                                 |
