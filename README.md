# pi-agent-config

Configuration complète et prête à l'emploi de mon agent **[pi](https://github.com/earendil-works/pi-coding-agent)**.
Le dépôt contient mes extensions, skills, scripts et réglages, plus un installeur qui
les déploie dans `~/.pi` et `~/.agents`.

> **Aucun secret n'est versionné.** Les clés API et chaînes de connexion vivent dans le
> Trousseau macOS ou dans des fichiers locaux ignorés par git. Les fichiers fournis
> (`*.example`) ne contiennent que des placeholders.

---

## 1. Ce que contient le dépôt

| Chemin | Cible | Rôle |
|---|---|---|
| `dot-pi/` | `~/.pi/` | Configuration de l'agent (réglages, MCP, extensions, skills, scripts) |
| `dot-agents/skills/` | `~/.agents/skills/` | Skills partagés au format [Agent Skills](https://agentskills.io/specification) |
| `install.sh` | — | Installeur idempotent (copie + npm install + exemples) |

### Arborescence

```text
pi-agent-config/
├── install.sh                     # installeur
├── dot-pi/
│   ├── agent/
│   │   ├── settings.json          # modèle, provider, packages, extensions
│   │   ├── models.json            # providers/modèles additionnels (Ollama/cloud)
│   │   ├── mcp-adapter.json       # config du package pi-mcp-adapter
│   │   ├── mcp.json.example       # serveurs MCP (sanitisé)
│   │   ├── auth.json.example      # clés API providers (sanitisé)
│   │   ├── trust.json.example     # dossiers de confiance
│   │   ├── pi-langfuse/
│   │   │   └── config.example.json
│   │   ├── bin/
│   │   │   ├── brain              # CLI de mémoire long terme MongoDB
│   │   │   ├── mongo-mcp          # lance mongodb-mcp-server via le Trousseau
│   │   │   └── mongoq             # helper de requêtes MongoDB pour le bash tool
│   │   ├── lib/                   # dépendances Node stables (mongodb, mongodb-mcp-server)
│   │   ├── npm/                   # packages pi (pi-langfuse, pi-mcp-adapter, …)
│   │   └── extensions/            # extensions TypeScript
│   └── skills/                    # skills spécifiques à cette config
└── dot-agents/
    └── skills/                    # brand-guidelines, canvas-design, postiz
```

---

## 2. Prérequis

- **macOS** (Apple Silicon de préférence) — plusieurs scripts s'appuient sur le Trousseau.
- **Node.js ≥ 22** et **npm**.
- Le CLI **pi** installé :
  ```bash
  npm i -g @earendil-works/pi-coding-agent
  ```
- *(optionnel)* **[Composio CLI](https://composio.dev)** pour l'extension `composio` :
  ```bash
  pip install composio-core && composio login
  ```
- *(optionnel)* **Playwright/Chromium** pour l'extension `browser` (installé via npm).
- *(optionnel)* **Python 3** pour le skill `pdf-reader`.

---

## 3. Installation

```bash
git clone <URL_DU_DEPOT> pi-agent-config
cd pi-agent-config
./install.sh            # n'écrase pas les fichiers existants
```

Options :

```bash
./install.sh --force    # écrase (avec sauvegarde .bak.<timestamp>)
./install.sh --dry-run  # montre ce qui serait fait
```

L'installeur :

1. copie `dot-pi/` → `~/.pi/` et `dot-agents/` → `~/.agents/` ;
2. génère les fichiers de config réels depuis les `*.example` **sans écraser** l'existant ;
3. rend exécutables les scripts de `~/.pi/agent/bin/` ;
4. lance `npm install` dans `~/.pi/agent/lib`, `~/.pi/agent/npm` et chaque extension
   possédant un `package.json`.

---

## 4. Configuration manuelle (secrets)

Tout ce qui est sensible reste **hors du dépôt**. À faire une fois après l'installation.

### 4.1 Clés API des modèles — `~/.pi/agent/auth.json`

Copie `auth.json.example` vers `auth.json` et renseigne les providers souhaités
(`xai`, `deepseek`, `moonshotai`, `zai`, …).

### 4.2 Secrets MCP — Trousseau macOS

Les serveurs MongoDB, Jev et treg lisent leurs identifiants dans le Trousseau :

```bash
security add-generic-password -s pi-mongod-local-agent -a "$USER" -w 'mongodb://user:pass@127.0.0.1:27017/?authSource=admin'
security add-generic-password -s pi-mongodb-atlas      -a "$USER" -w 'mongodb+srv://user:pass@cluster.mongodb.net'
security add-generic-password -s pi-jev-api            -a "$USER" -w '<cle_jev>'
security add-generic-password -s pi-treg-token         -a "$USER" -w '<token_treg>'
```

Puis renseigne `~/.pi/agent/mcp.json` (ou pars de `mcp.json.example`).
Pour n8n, exporte avant de lancer pi :

```bash
export N8N_API_URL='https://<ton-instance>'
export N8N_API_KEY='<ta-cle>'
```

### 4.3 Recherche web Google — `~/.pi/agent/extensions/web-search/auth.json`

```bash
cp ~/.pi/agent/extensions/web-search/auth.example.json \
   ~/.pi/agent/extensions/web-search/auth.json
# puis renseigne google_search_api_key et google_cse_id
```

### 4.4 Langfuse (traçage) — `~/.pi/agent/pi-langfuse/config.json`

Renseigne `publicKey` / `secretKey` (ou supprime le package `pi-langfuse` de
`settings.json` si tu n'utilises pas Langfuse).

### 4.5 Mémoire long terme MongoDB

```bash
~/.pi/agent/bin/brain init     # crée collections, validateurs et index (idempotent)
```

---

## 5. Détail des composants

### 5.1 Réglages (`settings.json`)

```json
{
  "defaultModel": "deepseek-flash",
  "defaultProvider": "deepseek",
  "defaultThinkingLevel": "high",
  "theme": "dark",
  "packages": ["npm:pi-langfuse", "npm:pi-mcp-adapter"],
  "extensions": ["-builtin:mcp"]
}
```

- `packages` installe automatiquement des packages pi (Langfuse, adaptateur MCP).
- `extensions: ["-builtin:mcp"]` désactive le MCP intégré au profit de
  **pi-mcp-adapter**.

### 5.2 Extensions (`~/.pi/agent/extensions/`)

| Extension | Ce qu'elle apporte |
|---|---|
| `ask-user-question.ts` | Outil `ask_user_question` : poser une question à choix multiples à l'utilisateur |
| `bash-guard/` | Analyse et bloque/confirme les commandes bash risquées |
| `browser/` | Pilote un Chromium headless (goto, eval, console, network, screenshot…) |
| `composio.ts` | Outils `composio_search` / `composio_execute` / `composio_connections` (250+ apps) |
| `custom-header.ts` | Personnalisation de l'en-tête de démarrage |
| `mongodb-brain.ts` | Mémoire long terme : injecte le digest au démarrage, trace les sessions, expose l'outil `brain` |
| `prompt-snippets/` | Raccourcis de prompts (alt+s) : orchestration, vérification, diagnostic… |
| `web-fetch/` | Outil `web_fetch` : extraction lisible d'une page (Readability, PDF, fallback Jina) |
| `web-search/` | Outil `web_search` via Google Custom Search |
| `herdr-agent-state.ts` | *Géré par [herdr](https://herdr.dev)* — ne pas modifier, régénéré à l'installation |

### 5.3 Scripts (`~/.pi/agent/bin/`)

- **`brain`** — CLI de mémoire long terme (MongoDB) : `init`, `digest`, `ingest`,
  `search`, `put`, `add`, `ls`, `get`, `rm`, `done`, `stats`, `schema`.
  Résolution de l'URI : `--uri` > `$BRAIN_URI` > Trousseau > `$MDB_MCP_CONNECTION_STRING`
  > `mcp.json` > `mongodb://127.0.0.1:27017`.
  Variables : `BRAIN_DISABLE`, `BRAIN_DIGEST_MAX`, `BRAIN_DIGEST_TTL`, `BRAIN_TRACE_EVERY`.
- **`mongo-mcp`** — enveloppe qui lit une URI dans le Trousseau puis lance
  `mongodb-mcp-server`. Usage : `mongo-mcp <service-trousseau> [args…]`.
- **`mongoq`** — helper de requêtes ad hoc pour le bash tool :
  `mongoq 'db.forms.countDocuments({})' --db heyform`.

### 5.4 Skills

Skills de cette config (dans `~/.pi/agent/skills/`) :

`analyze-sessions`, `brain`, `composio`, `convert-documents-to-markdown`,
`langfuse`, `mongodb-atlas-stream-processing`, `mongodb-connection`,
`mongodb-mcp-setup`, `mongodb-natural-language-querying`,
`mongodb-query-optimizer`, `mongodb-schema-design`, `mongodb-search-and-ai`,
`n8n-*` (code JS/Python, expression-syntax, mcp-tools-expert, node-configuration,
validation-expert, workflow-patterns), `pdf-reader`, `remotion`, `web-debug`.

Skills partagés (dans `~/.agents/skills/`) : `brand-guidelines`, `canvas-design`,
`postiz`.

> pi découvre automatiquement `~/.pi/agent/skills/` **et** `~/.agents/skills/`,
> aucun lien symbolique n'est nécessaire.
>
> Le skill `pdf-reader` a besoin de son venv Python :
> ```bash
> cd ~/.pi/agent/skills/pdf-reader && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
> ```

### 5.5 Modèles (`models.json`)

Déclare un provider additionnel `ollama` (API OpenAI-compatible sur
`http://127.0.0.1:11434/v1`) et le modèle cloud `nemotron-3-super:cloud`.
Adapte l'URL si ton serveur Ollama tourne ailleurs.

---

## 6. Sécurité

- **Jamais de secret dans ce dépôt.** Le `.gitignore` exclut `auth.json`,
  `mcp.json`, `trust.json`, les logs/caches MCP, `models-store.json` et leurs variantes.
- Les identifiants de bases de données passent par le **Trousseau macOS** via
  `security find-generic-password`.
- Avant toute publication, vérifie :
  ```bash
  git grep -nE '(sk-|xai-|apikey_|pk-lf-|sk-lf-|mongodb(\+srv)?://)'
  ```

---

## 7. Dépannage

| Symptôme | Piste |
|---|---|
| Un serveur MCP ne se connecte pas | `pi mcp list` ; vérifie `~/.pi/agent/mcp.log` |
| `brain` : « mongodb driver introuvable » | `cd ~/.pi/agent/lib && npm install mongodb` |
| `composio` : CLI absent | `pip install composio-core && composio login` |
| `web_fetch` vide sur un site JS | normal : fallback Jina puis erreur explicite |
| Extension modifiée non prise en compte | `/reload` dans pi, ou `npm install` dans son dossier |

---

## 8. Crédits

- **pi** — [earendil-works/pi-coding-agent](https://github.com/earendil-works/pi-coding-agent)
- **Composio**, **Langfuse**, **Playwright**, **MongoDB MCP Server**, **herdr** — projets tiers
  respectifs, sous leurs licences.
- Les skills `mongodb-*` proviennent de
  [mongodb/agent-skills](https://github.com/mongodb/agent-skills) ;
  `postiz`, `canvas-design` et `brand-guidelines` proviennent de leurs dépôts d'origine
  (voir les fichiers `LICENSE`/`LICENSE.txt` inclus dans chaque skill).

Les extensions et scripts propres à cette configuration sont fournis « tels quels »,
sans garantie. Vérifie chaque composant avant de l'exécuter.
