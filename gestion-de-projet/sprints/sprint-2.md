# Sprint 2 — Finaliser dataset ML et labellisation

**Fenêtre cible** : 2026-06-01 → 2026-06-14  
**Lots couverts** : Lot 2 → Lot 3 préparatoire  
**Statut** : ⏳ À venir — bloqué par Go Lot 2  
**Objectif** : obtenir un dataset propre, documenté, labellisable et prêt pour ML supervisé, sans entraîner de modèle tant que Lot 2 n'est pas validé.

## Livrables attendus

- PostgreSQL local opérationnel.
- Schéma tickets documenté.
- Dataset nettoyé ou jeu synthétique si Go extraction réelle absent.
- EDA et rapport qualité dataset.
- Protocole de labellisation.
- Dataset pairwise défini.
- Split train/test ≥ 70/30 préparé.

## Dépendances

- Go conformité/sécurité Sprint 1.
- Registre RGPD + cartographie champs.
- Secrets vérifiés et absence de données réelles dans Git.
- Stratégie pseudonymisation/nettoyage prouvée.

## Critères de validation

- [ ] Dataset exploitable documenté.
- [ ] EDA disponible : volumes, valeurs manquantes, doublons, distributions, déséquilibre.
- [ ] Labels ou protocole de labels validés.
- [ ] Contrôle absence PII réalisé par Compliance Lead.
- [ ] Gate Go Lot 3 formel produit.

## Go/No-Go

**No-Go par défaut** vers Lot 3.  
**Go Lot 3 uniquement si** dataset + labels + split + conformité Lot 2 sont validés.

## Issues GitHub

- Issue globale Sprint 2 : #7.
- US détaillées dans `gestion-de-projet/backlog.md` : US-DATA-003, US-DATA-004, US-ML-000.

## Points de vigilance

- Aucun entraînement ML réel dans ce sprint si le Go Lot 2 n'est pas obtenu.
- Les données réelles et dumps restent interdits dans Git.
