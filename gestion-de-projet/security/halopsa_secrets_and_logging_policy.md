# Politique secrets et journalisation HaloPSA — Lot 2

## Objectif

Définir les règles de gestion des secrets et des logs pour une future intégration HaloPSA, sans secret, sans payload réel et sans extraction réelle.

## Secrets

- Les secrets ne doivent jamais être versionnés.
- Les secrets ne doivent jamais être copiés dans la documentation, les tickets, les logs ou les jeux de données.
- Les secrets doivent être fournis par variables d'environnement ou par secret manager.
- Aucun secret fictif ressemblant à une clé ne doit être utilisé dans les exemples ou procédures.
- Les fichiers locaux d'environnement ne doivent pas contenir de valeurs réelles dans le dépôt.

## Variables d'environnement et secret manager

Les paramètres sensibles attendus pour une intégration future doivent être injectés à l'exécution. La documentation peut nommer les variables de manière descriptive, mais ne doit jamais fournir de valeur.

Exemples de noms autorisés sans valeur :

- `HALOPSA_BASE_URL`
- `HALOPSA_CLIENT_ID`
- `HALOPSA_CLIENT_SECRET`
- `HALOPSA_TENANT`
- `SYNAPPSE_AGENT_ID_HMAC_SECRET`

Pourquoi : nommer les variables clarifie le contrat d'exploitation sans exposer de secret.

## Journalisation interdite

Les logs ne doivent jamais contenir :

- contenu de ticket ;
- titre complet ;
- description complète ;
- payload HaloPSA ;
- headers HTTP ;
- secrets, tokens, cookies ou clés ;
- identifiants personnels bruts ;
- pièces jointes ou commentaires internes bruts.

## Journalisation autorisée

Les logs peuvent contenir uniquement des informations techniques minimisées :

- identifiant interne de lot ;
- mode d'exécution, par exemple dry-run ou import contrôlé ;
- compteurs agrégés ;
- codes d'erreur non sensibles ;
- durée d'exécution ;
- statut de validation ;
- statut de purge.

## Politique HMAC-SHA-256 pour exception

Toute conservation de pseudonyme dérivé d'un identifiant personnel, notamment `agent_id_pseudo`, nécessite une exception validée.

Règles :

- utiliser HMAC-SHA-256 avec une clé stockée hors base et hors dépôt ;
- injecter le secret HMAC via `SYNAPPSE_AGENT_ID_HMAC_SECRET`, sans valeur documentée ;
- échouer en mode fermé si `SYNAPPSE_AGENT_ID_HMAC_SECRET` est absent ou vide lorsqu'une pseudonymisation est requise ;
- gérer une version de clé ;
- ne jamais stocker l'identifiant brut ;
- ne jamais logger la valeur brute, la clé ou les entrées de calcul ;
- purger les pseudonymes selon la même échéance que les données associées.

## Rotation et révocation conceptuelles

La stratégie future doit prévoir :

- rotation périodique des secrets ;
- révocation immédiate en cas de suspicion d'exposition ;
- remplacement des clés HMAC avec suivi de version ;
- invalidation des accès non utilisés ;
- preuve interne de rotation ou révocation sans valeur secrète.

## Contrôles avant extraction réelle

Avant toute extraction HaloPSA réelle, les validations suivantes sont obligatoires :

- confirmation que les secrets sont fournis uniquement par variable d'environnement ou secret manager ;
- vérification qu'aucun secret n'est présent dans le dépôt ;
- revue de la configuration de logs ;
- test dry-run sans persistance et sans payload journalisé ;
- validation de l'allowlist de champs ;
- validation de la politique de purge ;
- validation de l'exception HMAC-SHA-256 si des pseudonymes sont nécessaires.

## Réaction en cas d'incident

En cas de suspicion de fuite de secret ou de log sensible :

1. révoquer le secret concerné ;
2. suspendre l'extraction ;
3. identifier le périmètre exposé sans recopier le contenu sensible ;
4. purger les traces non conformes selon procédure validée ;
5. documenter l'incident avec références internes non sensibles ;
6. redémarrer uniquement après validation sécurité et conformité.
