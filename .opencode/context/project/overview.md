# Projet — Vue d'ensemble

## Identité

| Champ             | Valeur                                                       |
| ----------------- | ------------------------------------------------------------ |
| Projet            | Plateforme Intelligente de Détection de Tickets Redondants   |
| Entreprise        | SYNAPPSE — ESN médico-social, Mouilleron-le-Captif (Vendée)  |
| Chef de projet    | Charles TRONEL (alternant Mastère DIA — Nexa Digital School) |
| Référence Abraxio | PRJ000229                                                    |

## Problématique

> "Comment concevoir, au sein d'une plateforme d'intelligence artificielle privée et auto-hébergée, un système de détection automatique de tickets redondants permettant d'alerter proactivement nos équipes support ?"

## Contexte

SYNAPPSE gère quotidiennement les tickets IT de ses clients ESSMS via HaloPSA. Des tickets redondants sont régulièrement ouverts pour des incidents déjà traités, sans mécanisme d'alerte préventif. Les historiques HaloPSA constituent une source riche inexploitée.

## Objectif principal

Détecter automatiquement si un ticket entrant est redondant avec un ticket existant du même client, et alerter les techniciens avant traitement avec score de confiance et explication.

## Périmètre

| Dans le scope                                   | Hors scope                           |
| ----------------------------------------------- | ------------------------------------ |
| Extraction tickets HaloPSA via API              | Intégration native HaloPSA (webhook) |
| Nettoyage, structuration, chargement PostgreSQL | Données NinjaOne, SharePoint         |
| Entraînement modèles supervisés + Grid Search   | Déploiement cloud externe            |
| Dashboard monitoring (alertes, scores)          | Formation des équipes                |
| Application web FastAPI + Vite/React            | —                                    |

## Bénéfices attendus

- Gain de temps technicien — alerte avant traitement d'un ticket redondant
- Meilleure qualité de service pour les clients ESSMS
- Première exploitation IA des historiques HaloPSA
- Fondation d'une plateforme IA auto-hébergée extensible
