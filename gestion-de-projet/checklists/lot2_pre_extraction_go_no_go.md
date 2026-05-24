# Checklist Go/No-Go pré-extraction — Lot 2 HaloPSA

## Objectif

Valider les conditions préalables à une extraction HaloPSA destinée à constituer un dataset ML conforme, sans réaliser d'extraction réelle à cette étape.

## Décision Go/No-Go

| Critère | Statut |
| --- | --- |
| Stratégie d'extraction définie sans exécution réelle | [ ] GO / [ ] NO-GO |
| Allowlist stricte validée avant extraction | [ ] GO / [ ] NO-GO |
| Règles PII validées avant stockage | [ ] GO / [ ] NO-GO |
| Règles de logs validées | [ ] GO / [ ] NO-GO |
| Critères dataset ML validés | [ ] GO / [ ] NO-GO |
| Critères qualité données et labels validés | [ ] GO / [ ] NO-GO |
| Politique de conservation/purge validée | [ ] GO / [ ] NO-GO |

**Décision globale :** [ ] GO extraction contrôlée / [ ] NO-GO

## Stratégie extraction HaloPSA sans extraction réelle

- [ ] Décrire le périmètre fonctionnel attendu de l'extraction sans appeler l'API HaloPSA.
- [ ] Valider les champs autorisés via une revue documentaire avant toute extraction.
- [ ] Utiliser uniquement des jeux de test synthétiques ou anonymisés pour préparer le pipeline.
- [ ] Interdire tout payload HaloPSA réel dans les documents, tickets, logs, tests ou exemples.
- [ ] Documenter la finalité ML de chaque champ conservé avant extraction.

## Allowlist stricte avant extraction

- [ ] Définir une allowlist positive des champs exploitables pour le ML.
- [ ] Refuser tout champ non explicitement présent dans l'allowlist.
- [ ] Valider l'allowlist par les rôles habilités avant extraction.
- [ ] Exclure par défaut `agent_id` de l'allowlist.
- [ ] Exclure tous les identifiants directs non nécessaires à la finalité ML.

## Données brutes et stockage

- [ ] Ne conserver aucun raw JSON durable.
- [ ] Supprimer les réponses brutes dès transformation contrôlée terminée.
- [ ] Stocker uniquement des données nettoyées, minimisées et nécessaires au dataset ML.
- [ ] Appliquer le nettoyage PII avant tout stockage persistant.
- [ ] Vérifier que les exports intermédiaires ne contiennent ni secret, ni contenu ticket non nettoyé.

## Exceptions identifiants et pseudonymisation

- [ ] Maintenir `agent_id` exclu par défaut.
- [ ] Autoriser une exception uniquement si elle est formellement validée et justifiée.
- [ ] En cas d'exception validée, appliquer une pseudonymisation par HMAC-SHA-256.
- [ ] Gérer la clé HMAC exclusivement hors dépôt, via secret manager ou variable d'environnement sécurisée.
- [ ] Interdire toute clé, valeur secrète ou secret fictif dans le dépôt et la documentation.

## Nettoyage PII avant stockage

- [ ] Supprimer ou pseudonymiser les noms, emails, téléphones, adresses, identifiants clients et tout élément directement identifiant.
- [ ] Supprimer les pièces jointes et références documentaires non nécessaires au ML.
- [ ] Contrôler l'absence de PII résiduelle avant persistance.
- [ ] Documenter les règles de nettoyage appliquées et leurs limites.

## Logs et observabilité

- [ ] Produire des logs sans contenu ticket.
- [ ] Produire des logs sans secret.
- [ ] Journaliser uniquement des métadonnées techniques minimales : horodatage, statut, volume agrégé, erreurs non sensibles.
- [ ] Interdire la journalisation de payloads, champs texte, identifiants directs et valeurs d'authentification.

## Critères dataset ML

- [ ] PII résiduelle égale à 0 avant validation du dataset.
- [ ] Labels présents, documentés et exploitables.
- [ ] Cas ambigus exclus du dataset d'entraînement et d'évaluation.
- [ ] Règles d'anti-fuite train/test validées avant modélisation.
- [ ] Split effectué par groupe ou ticket source, pas uniquement par ligne.
- [ ] Absence de doublons exacts entre train, validation et test.
- [ ] Traçabilité documentaire de la méthode de labellisation.

## Critères qualité données et labels

- [ ] Taux de champs manquants mesuré et jugé acceptable selon la finalité ML.
- [ ] Distribution des labels mesurée et documentée.
- [ ] Déséquilibre de classes identifié avant entraînement.
- [ ] Labels contradictoires détectés et résolus ou exclus.
- [ ] Données trop courtes, vides ou non informatives exclues selon règle documentée.
- [ ] Échantillon validé manuellement pour contrôler la cohérence des labels.

## Champs ML exclus

- [ ] Identifiants directs de personnes, clients, agents ou organisations.
- [ ] `agent_id`, sauf exception validée avec HMAC-SHA-256.
- [ ] Secrets, jetons, clés API, mots de passe et valeurs d'authentification.
- [ ] Horodatages ou statuts pouvant révéler indirectement le label cible si risque de fuite.
- [ ] Champs postérieurs à l'événement de prédiction ou issus du traitement final du ticket.
- [ ] Contenu brut non nettoyé issu de tickets ou commentaires.

## Condition Lot 3 ML

**Lot 3 ML : NO-GO tant qu'aucun dataset réel conforme n'a été validé.**

Le passage au Lot 3 nécessite au minimum : PII résiduelle 0, labels validés, champs ML exclus contrôlés, split par groupe ou ticket source, et absence de fuite train/test.

## Conservation et purge

- [ ] Définir une durée de conservation minimale strictement nécessaire.
- [ ] Purger les données de travail au plus tard J+7 post-soutenance, sauf obligation contraire documentée.
- [ ] Documenter la preuve de purge sans inclure de contenu ticket, secret ou payload réel.
- [ ] Supprimer les artefacts intermédiaires non nécessaires après validation.

## Blocages entraînant un NO-GO

- Présence de PII résiduelle non maîtrisée.
- Absence de labels fiables.
- Allowlist non validée.
- Conservation durable de raw JSON.
- Logs contenant contenu ticket ou secret.
- Split par ligne uniquement en présence de tickets liés ou groupes corrélés.
- Risque de fuite train/test non traité.
