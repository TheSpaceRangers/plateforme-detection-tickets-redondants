# Durée de conservation et procédure de purge

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date** : 2026-05-23  
**Conformité** : Art. 5.1.e RGPD — limitation de la conservation

---

## 1. Durées de conservation

| Catégorie de données | Durée de conservation | Point de départ | Justification |
|---|---|---|---|
| **Tickets pseudonymisés en PostgreSQL** | **12 mois** | Date d'extraction initiale | Cycle d'entraînement ML (pipeline reproductible) + démonstration soutenance + batterie de tests |
| **Logs de prédiction** (scores, ids tickets, timestamp) | **Durée du projet + 6 mois** | Date de première prédiction | Traçabilité des alertes pour audit — pas de texte brut dans les logs |
| **Données brutes HaloPSA** (avant transformation) | **24 heures max** | Date d'extraction | Fenêtre technique nécessaire à la pseudonymisation — jamais persistées au-delà |
| **Modèle ML sérialisé** (joblib) | **Durée du projet + 1 an** | Date de sérialisation | Reproductibilité des résultats pour le mémoire |
| **Jeux de données ML** (train/test/val) | **Durée du projet** | Date de split | Démonstration et reproductibilité — pas de PII après pseudonymisation |
| **Mémoire PDF et annexes** | **Permanent** (anonymisé) | Dépôt mémoire | Engagement académique — vérifier absence totale de PII avant dépôt |
| **Journal des purges** | **2 ans post-soutenance** | Date de purge | Preuve de conformité pour tout audit ultérieur (Art. 5.2 — Responsabilité) |

---

## 2. Procédure de purge — post-soutenance (octobre 2026)

### 2.1 Calendrier

| Étape | Date butoir | Action |
|---|---|---|
| Jalon mémoire | 2026-09-01 | Vérification qu'aucune PII n'est dans le mémoire ou les annexes |
| Soutenance | Octobre 2026 | Dernière utilisation des données de production |
| J+7 post-soutenance | Octobre 2026 | Exécution de la purge complète |
| J+30 post-soutenance | Novembre 2026 | Attestation de purge signée |

### 2.2 Périmètre de la purge

Toutes les données suivantes sont définitivement supprimées :

- [ ] Base PostgreSQL `halopsa_tickets` : `DROP DATABASE` ou `TRUNCATE` toutes les tables
- [ ] Fichiers de cache/computed : `ml/data/raw/`, `ml/data/processed/`, `ml/models/`
- [ ] Logs d'extraction : tout fichier contenant des données HaloPSA brutes
- [ ] Logs de prédiction : `predictions_logs` table
- [ ] Artefacts ML : modèles joblib, vectorizers, encoders

### 2.3 Ce qui est conservé après purge

- Le code source (backend, frontend, ml) — aucune PII
- Les fichiers de documentation (registre, stratégie, etc.) — aucune PII
- Les métriques et rapports d'évaluation — valeurs agrégées
- Les captures d'écran du dashboard — vérifiées sans PII
- Le journal de purge — preuve documentaire

### 2.4 Script de purge (référence)

```python
"""
purge.py — Exécuté post-soutenance pour purge complète.
Usage : python purge.py --confirm
"""

import os
import shutil
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

DIRS_TO_PURGE = [
    "ml/data/raw",
    "ml/data/processed",
    "ml/models",
]

def purge_database():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    tables = ["tickets", "predictions_logs", "training_logs"]
    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    conn.commit()
    cur.close()
    conn.close()
    print(f"[{datetime.now()}] Base de données purgée.")

def purge_files():
    for d in DIRS_TO_PURGE:
        if os.path.exists(d):
            shutil.rmtree(d)
            os.makedirs(d, exist_ok=True)
            print(f"[{datetime.now()}] Dossier {d} purgé.")

def write_purge_log():
    with open("gestion-de-projet/rgpd/purge-log.txt", "w") as f:
        f.write(f"PURGE EXECUTED: {datetime.now().isoformat()}\n")
        f.write("Toutes les données de production ont été supprimées.\n")
        f.write("Seuls le code source et la documentation sont conservés.\n")

if __name__ == "__main__":
    import sys
    if "--confirm" not in sys.argv:
        print("DRY RUN — Aucune action effectuée. Passez --confirm pour exécuter.")
        sys.exit(0)
    purge_database()
    purge_files()
    write_purge_log()
    print("Purge terminée. Attestation : gestion-de-projet/rgpd/purge-log.txt")
```

---

## 3. Engagement de suppression — mention mémoire

Le mémoire devra contenir un engagement écrit similaire à :

> **Engagement de suppression des données**
>
> Conformément à l'article 5.1.e du RGPD, l'ensemble des données extraites de l'API HaloPSA dans le cadre du projet SYNAPPSE sont conservées au maximum jusqu'à la date de soutenance (octobre 2026).
>
> Une purge complète est exécutée dans les 7 jours suivant la soutenance :
> - Suppression de la base PostgreSQL contenant les tickets pseudonymisés
> - Suppression des artefacts modèles et jeux de données
> - Suppression de tous les logs contenant des données de production
>
> Seul le code source et la documentation technique (exempts de PII) sont conservés à titre de preuve académique.
>
> Le journal de purge est archivé dans le dépôt GitHub pour justification.

---

## 4. Surveillance et application

| Mécanisme | Responsable | Fréquence |
|---|---|---|
| Vérification des durées de conservation | Compliance Lead | Mensuelle |
| Alerte de purge post-soutenance | Scrum Master | Jalon dédié dans le backlog |
| Mise à jour du registre de traitement | Compliance Lead | Après chaque modification de durée |
| Vérification d'absence de données brutes dans Git | DevOps Engineer | À chaque PR |

---

## 5. Références

- Registre de traitement : `registre-traitement.md` (section 7)
- Art. 5.1.e RGPD — Limitation de la conservation
- Art. 17 RGPD — Droit à l'effacement
- Art. 5.2 RGPD — Responsabilité (comptes rendus de purge)
