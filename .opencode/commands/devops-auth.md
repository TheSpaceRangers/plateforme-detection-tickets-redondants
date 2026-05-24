---
agent: Tesla
description: Authentifie Tesla auprès de GitHub via la GitHub App tesla-devops. À appeler en début de tâche GitHub.
---

Execute uniquement la commande suivante pour générer le token, puis ne fais plus rien.

```bash
export GH_TOKEN=$(.opencode/scripts/tesla-devops-token.sh)
```
