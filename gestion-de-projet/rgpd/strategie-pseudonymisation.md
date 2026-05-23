# Stratégie de pseudonymisation

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date** : 2026-05-23  
**Version** : 1.0  
**Conformité** : Art. 4.5, Art. 5.1.c, Art. 32 RGPD — Recommandation CNIL pseudonymisation

---

## 1. Principes généraux

La pseudonymisation est appliquée **avant stockage en PostgreSQL** comme couche de protection immédiate.

| Principe | Application |
|---|---|
| Déterministe | Un même `user_id` donne toujours le même hash → cardinalité préservée pour l'apprentissage ML |
| Non réversible | SHA-256 avec sel local — pas de fonction de déchiffrement possible |
| Précoce | Appliquée dès l'extraction, avant toute persistance |
| Systématique | Tous les `user_id` sont pseudonymisés, sans exception |
| Sans clé de déréférencement | Le sel est local et ne permet pas de retrouver l'identifiant d'origine |

---

## 2. Pseudonymisation de `user_id`

### 2.1 Algorithme

```
hash = SHA-256(sel_local || str(user_id))
user_id_pseudonyme = hex(hash)[:16]   # 16 premiers caractères hexadécimaux
```

### 2.2 Implémentation Python (référence)

```python
import hashlib
import os

# Le sel est généré une fois et stocké localement dans .env
# SALT = os.getenv("PSEUDO_SALT", os.urandom(32).hex())

def pseudonymiser_user_id(user_id: int, salt: str) -> str:
    """
    Pseudonymise un user_id HaloPSA.
    Déterministe : même user_id + même sel → même hash.
    Non réversible : SHA-256 interdit tout déréférencement.
    """
    raw = f"{salt}|{user_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

### 2.3 Gestion du sel

| Propriété | Valeur |
|---|---|
| Génération | `os.urandom(32).hex()` — une seule fois en local |
| Stockage | Variable d'environnement `PSEUDO_SALT` dans `.env` |
| Exclusion Git | `.env` est dans `.gitignore` — jamais commité |
| Rotation | Non nécessaire (pas de déréférencement possible) |
| Perte du sel | Les hashs deviennent inexploitables → ré-extraction nécessaire |

### 2.4 Impact ML

Le hash déterministe préserve les relations entre tickets d'un même `user_id`, ce qui est suffisant pour la détection de redondance (les tickets similaires émis par un même utilisateur sont détectables sans connaître son identité réelle).

---

## 3. Nettoyage de `summary` et `details`

### 3.1 Règles de suppression

Les motifs suivants sont détectés par regex et remplacés par le token `[PII_REDACTED]` :

| # | Motif | Regex | Exemple |
|---|---|---|---|
| 1 | Adresse email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | `jean.dupont@societe.fr` → `[PII_REDACTED]` |
| 2 | Numéro de téléphone FR | `(?:0|\+33)[1-9](?:[\s.-]?\d{2}){4}` | `06 12 34 56 78` → `[PII_REDACTED]` |
| 3 | Numéro de téléphone international | `\+\d{1,3}[\s.-]?\d{4,}` | `+33123456789` → `[PII_REDACTED]` |
| 4 | Civilité + Nom | `(?:M\.|Mme|Mlle)\s+[A-Z][a-zéêèëàâäûüôöîïç]+(?:\s+[A-Z][a-zéêèëàâäûüôöîïç-]+)*` | `M. Dupont` → `[PII_REDACTED]` |
| 5 | Adresse postale (mots-clés) | `(?:rue|avenue|boulevard|impasse|allée|chemin|place|route|lotissement)\s+\S+` | `rue de la Paix` → `[PII_REDACTED]` |
| 6 | Code postal + ville | `\d{5}\s*[A-Z][a-zéêèëàâäûüôöîïç]+` | `75001 Paris` → `[PII_REDACTED]` |
| 7 | IP locale ou publique | `\b(?:\d{1,3}\.){3}\d{1,3}\b` | `192.168.1.1` → `[PII_REDACTED]` |

### 3.2 Application

```python
import re

PII_PATTERNS = [
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',           # email
    r'(?:0|\+33)[1-9](?:[\s.-]?\d{2}){4}',                         # téléphone FR
    r'\+\d{1,3}[\s.-]?\d{4,}',                                      # téléphone international
    r'(?:M\.|Mme|Mlle)\s+[A-Z][a-zéêèëàâäûüôöîïç]+(?:\s+[A-Z][a-zéêèëàâäûüôöîïç-]+)*',  # civilité + nom
    r'(?:rue|avenue|boulevard|impasse|allée|chemin|place|route|lotissement)\s+\S+',
    r'\d{5}\s*[A-Z][a-zéêèëàâäûüôöîïç]+',
    r'\b(?:\d{1,3}\.){3}\d{1,3}\b',                                 # IP
]

def nettoyer_texte(texte: str) -> str:
    """
    Nettoie un champ texte en supprimant les PII identifiables par regex.
    Les correspondances sont remplacées par [PII_REDACTED].
    """
    for pattern in PII_PATTERNS:
        texte = re.sub(pattern, '[PII_REDACTED]', texte)
    return texte
```

### 3.3 Nettoyage NLP complémentaire

En complément des regex, une étape NER (Named Entity Recognition) avec spaCy peut être introduite pour détecter les noms de personnes non couverts par les motifs de civilité.

| Option | Quand | Bénéfice |
|---|---|---|
| Regex seules | Version initiale (Sprint 1) | Rapide, déterministe, sans dépendance NLP |
| Regex + spaCy NER | Sprint 2 (avant ML) | Couverture plus large des entités nommées |

---

## 4. Troncature de `details`

Le champ `details` peut contenir de très longs textes (plusieurs pages HTML). Pour limiter l'exposition :

- Longueur maximale après extraction : **2000 caractères** (UTF-8)
- La troncature est appliquée **avant** le nettoyage regex

```python
details_tronque = details[:2000]
details_propre = nettoyer_texte(details_tronque)
```

---

## 5. Pipeline complet de pseudonymisation

```
[Données brutes HaloPSA]
    │
    ├─── user_id  →  SHA-256(sel + user_id)  →  [user_id_pseudo]
    │
    ├─── summary  →  troncature? (déjà court)  →  nettoyage regex  →  [summary_propre]
    │
    ├─── details  →  troncature 2000 car.  →  nettoyage regex  →  [details_propre]
    │
    ├─── autres champs  →  inchangés (non sensibles)
    │
    ▼
[Stockage PostgreSQL]
```

---

## 6. Tests de validation

| Test | Attendu | Méthode |
|---|---|---|
| Même user_id → même hash | Vrai | Appeler 2× avec user_id=42, même sel |
| user_id différent → hash différent | Vrai | user_id=1 ≠ user_id=2 |
| Pas de collision (SHA-256) | Négligeable | 2^128 collisions prob. |
| Nettoyage email dans summary | `[PII_REDACTED]` | Regex sur `"Contacter jean@test.fr"` |
| Nettoyage téléphone dans details | `[PII_REDACTED]` | Regex sur `"Tél : 06 12 34 56 78"` |
| Troncature details > 2000 car. | Max 2000 car. | Chaîne artificielle de 5000 car. → doit être coupée |
| Token PII non présent après nettoyage | Pas de pattern PII résiduel | Nouvelle passe de regex sur le résultat |

---

## 7. Références

- Registre de traitement : `registre-traitement.md`
- Cartographie des champs : `cartographie-champs.md`
- Minimisation des données : `minimisation-donnees.md`
- CNIL — Guide de la pseudonymisation : https://www.cnil.fr/fr/pseudonymisation
