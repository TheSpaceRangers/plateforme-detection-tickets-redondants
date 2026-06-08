# Checklist ML — No raw export

## Principe

Aucun dataset, artefact de debug, log ou stockage ML ne doit contenir de ticket brut. L'export est autorisé uniquement après nettoyage ou pseudonymisation.

## État actuel observé

- Aucun export dataset ML opérationnel n'existe encore.
- Aucun stockage ML opérationnel n'existe encore.
- Les fonctions de garde-fous PII/HMAC sont disponibles dans `ml/src/preprocessing/*`.

## Contrôles obligatoires avant export

- [ ] Le flux appelle `build_preprocessed_ticket_dataset()` avant tout export.
- [ ] Le dataset exporté est construit depuis le résultat prétraité, pas depuis le payload source.
- [ ] `assert_no_residual_pii()` est bloquant.
- [ ] Une allowlist stricte filtre les champs exportés.
- [ ] `agent_id` brut est absent.
- [ ] `agent_id_pseudonym` est absent par défaut ou produit par HMAC-SHA-256 avec secret runtime.
- [ ] Aucune valeur de `SYNAPPSE_AGENT_ID_HMAC_SECRET` n'est loggée ou exportée.
- [ ] Les logs ne contiennent ni contenu de ticket, ni PII, ni secret.

## Champs interdits par défaut

- [ ] JSON source complet.
- [ ] Texte ticket avant sanitation.
- [ ] `agent_id` brut.
- [ ] Identifiants client, utilisateur, compte, login ou assimilés.
- [ ] Toute colonne non validée par allowlist.

## Critères No-Go

- [ ] Export brut détecté.
- [ ] PII résiduelle détectée.
- [ ] Secret HMAC absent alors que pseudonymisation demandée.
- [ ] Absence de test d'intégration bloquant.
- [ ] Besoin d'extraction réelle HaloPSA dans cette étape documentaire.

## Preuve attendue à l'implémentation future

- [ ] Test d'intégration démontrant que l'export brut échoue.
- [ ] Test d'intégration démontrant que la PII résiduelle bloque le flux.
- [ ] Test d'intégration démontrant que les champs hors allowlist ne sont pas exportés.
- [ ] Test d'intégration démontrant le fail-closed HMAC sans secret.
