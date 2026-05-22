# Sprint 4 — API prédiction et intégration modèle

**Fenêtre cible** : 2026-07-01 → 2026-07-15  
**Lots couverts** : Lot 4  
**Statut** : ⏳ À venir  
**Objectif** : exposer le modèle sélectionné via une API FastAPI locale, traçable et conforme.

## Livrables attendus

- Contrat API prédiction.
- Endpoint local de prédiction.
- Service de prédiction découplé du routeur.
- Journalisation PostgreSQL minimisée.
- Tests API préparés.
- Sécurité locale documentée.

## Dépendances

- Modèle sérialisé validé Sprint 3.
- Schéma d'entrée/sortie stable.
- PostgreSQL opérationnel.
- Politique logs prédictions validée.

## Critères de validation

- [ ] Endpoint prédiction opérationnel localement.
- [ ] Payloads validés strictement.
- [ ] Logs sans texte brut ticket ni PII inutile.
- [ ] Erreurs sans stack trace sensible.
- [ ] Contrat prêt pour frontend Sprint 5.

## Go/No-Go

**Go Sprint 5** si contrat API stable, modèle chargé, logs conformes.  
**No-Go** si artefact modèle non validé ou exposition de données dans logs/réponses.

## Issues GitHub

- Issue globale Sprint 4 : #9.
- US détaillées dans `gestion-de-projet/backlog.md` : US-APP-001, US-APP-002.

## Points de vigilance

- API locale par défaut ; exposition réseau uniquement pour démo contrôlée.
- CORS et logs à restreindre dès la conception.
