# Minimisation des données

**Projet** : SYNAPPSE — Plateforme de détection de tickets redondants  
**Date** : 2026-05-23  
**Conformité** : Art. 5.1.c RGPD — seules les données nécessaires à la finalité sont collectées

---

## 1. Principe

Conformément à l'Art. 5.1.c du RGPD, seules les données strictement nécessaires à la détection de tickets redondants sont collectées et stockées. Tout champ non indispensable est exclu dès l'extraction HaloPSA.

---

## 2. Tableau de minimisation

### 2.1 Champs collectés (après transformation)

| Champ | Collecté ? | Justification métier | Mesure de minimisation |
|---|---|---|---|
| `id` | **Oui** | Identifiant unique du ticket — clé primaire nécessaire au référencement | Conservé tel quel |
| `summary` | **Oui** | Titre du ticket — essentiel pour la comparaison textuelle de similarité | Nettoyé (regex PII) |
| `details` | **Oui, tronqué** | Description détaillée — utile pour affiner la similarité sémantique | Troncature 2000 car. + nettoyé |
| `client_id` | **Oui** | Regroupement des tickets par client — condition sine qua non (la redondance est intra-client) | Conservé tel quel |
| `site_id` | **Oui** | Sous-regroupement géographique — utile pour affiner la détection | Conservé tel quel |
| `user_id` | **Oui, pseudonymisé** | Identifiant du demandeur — utile pour détecter les redondances par le même utilisateur | HMAC-SHA-256 avec secret local |
| `agent_id` | **Non par défaut** | L'affectation technicien n'est pas nécessaire à la similarité ; conservation seulement si un cas d'usage validé l'exige | Exclu ou HMAC-SHA-256 si indispensable |
| `tickettype_id` | **Oui** | Catégorisation fonctionnelle — filtre de similarité | Conservé tel quel |
| `category_1` | **Oui** | Catégorie niveau 1 — forte valeur discriminante pour similarité | Conservé tel quel |
| `category_2` | **Oui** | Catégorie niveau 2 — granularité supplémentaire | Conservé tel quel |
| `category_3` | **Oui** | Catégorie niveau 3 — granularité fine | Conservé tel quel |
| `dateoccurred` | **Oui** | Date d'occurrence — critère temporel de similarité (proximité dans le temps) | Conservé tel quel |
| `dateentered` | **Oui** | Date de saisie — critère temporel | Conservé tel quel |
| `dateclosed` | **Oui** | Date de clôture — indicateur d'état | Conservé tel quel |
| `status_id` | **Oui** | Statut — filtre (tickets clos vs ouverts) | Conservé tel quel |
| `priority_id` | **Oui** | Priorité — critère de similarité | Conservé tel quel |

### 2.2 Champs exclus (non collectés)

| Champ | Raison de l'exclusion | Risque si collecté |
|---|---|---|
| `user.email` (endpoint Users) | Non disponible via Tickets — nécessiterait API Users (PII directe) | Email personnel/nom/prénom exposé |
| `user.name` (endpoint Users) | Non nécessaire à la détection de redondance | PII directe — interdite par principe de minimisation |
| `client.name` | Non nécessaire — seul client_id compte pour le regroupement | Données non nécessaires |
| `site.name` | Non nécessaire — seul site_id suffit | Données non nécessaires |
| `agent.name` | Non nécessaire — seul agent_id suffit | Données non nécessaires |
| `agent_id` | Non nécessaire au calcul de similarité par défaut | Identifiant professionnel indirectement personnel |
| `custom_fields` | Non documentés — non pertinents pour la similarité | Exposition inconnue |
| `attachments` | Non traités — hors périmètre de l'analyse textuelle | Volume, données cachées, PII potentielles |
| `history` / `actions` | Non nécessaires — seuls l'état présent et les dates comptent | Volume, complexité, risque PII |
| `tags` / `keywords` | Non utilisés dans le modèle de similarité | Non pertinents |
| SLA associé | Non nécessaire à la détection de redondance | Non pertinent |

### 2.3 Champs optionnels interdits par défaut

| Champ | Statut | Condition exceptionnelle |
|---|---|---|
| `resolution_details` | Interdit par défaut | Activation uniquement après cartographie PII, minimisation documentée et nettoyage validé |
| `custom_field_values` | Interdit par défaut | Activation uniquement si mapping connu, non PII et besoin métier démontré |
| Tout champ hors tableau 2.1 | Interdit | Toute extension de collecte impose une mise à jour du registre avant extraction |

---

## 3. Justification consolidée

| Finalité | Champs nécessaires | Champs exclus |
|---|---|---|
| Regroupement par client | `client_id`, `site_id` | `client_name`, `site_name`, infos de contact |
| Détection de similarité textuelle | `summary` (nettoyé), `details` (tronqué + nettoyé) | `attachments`, `history`, tags |
| Filtrage et contexte | `category_1/2/3`, `tickettype_id`, `status_id`, `priority_id` | SLA, métadonnées de workflow |
| Regroupement par utilisateur | `user_id` (pseudonymisé) | `user.email`, `user.name`, téléphone, `agent_id` par défaut |
| Fenêtre temporelle | `dateoccurred`, `dateentered`, `dateclosed` | Timestamps secondaires |

---

## 4. Vérification d'absence de PII résiduelles

Avant chaque extraction réelle HaloPSA, un script de contrôle vérifie :

1. Qu'aucun champ de la section "exclus" n'est présent dans la requête API
2. Que `user_id` a bien été pseudonymisé avant stockage et que `agent_id` est absent ou pseudonymisé
3. Que les champs `summary` et `details` ne contiennent plus de motifs PII après nettoyage
4. Qu'aucune donnée n'est stockée en dehors du schéma PostgreSQL défini
5. Qu'aucune collecte hors périmètre ni champ optionnel n'est activé sans validation documentaire préalable

---

## 5. Références

- Registre de traitement : `registre-traitement.md`
- Cartographie des champs PII : `cartographie-champs.md`
- Stratégie de pseudonymisation : `strategie-pseudonymisation.md`
- Art. 5.1.c RGPD — Principe de minimisation
