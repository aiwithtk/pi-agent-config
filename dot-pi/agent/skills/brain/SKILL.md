---
name: brain
description: Mémoire long terme MongoDB du projet (db `brain` sur Atlas) — faits durables, projets, personnes, tâches, décisions et leçons. À utiliser dès qu'il faut mémoriser quelque chose pour les prochaines sessions, retrouver un contexte oublié, ou consigner une décision/erreur. Charge cette skill quand l'utilisateur dit "retiens", "souviens-toi", "note que", "qu'est-ce qu'on avait décidé", "où on en est", ou quand une information durable sur lui, ses projets ou son environnement apparaît en conversation.
license: MIT
---

# brain — mémoire long terme

Le cerveau est une base MongoDB `brain` (sur le cluster Atlas `n8n`, cf. `~/.pi/agent/mcp.json`)
pilotée par un CLI : **`brain`** (dans `~/.pi/agent/bin/`, déjà dans le `PATH`).

Une extension pi injecte automatiquement un **digest** compact (faits + projets + tâches ouvertes +
décisions + leçons + journal) au début de chaque session. Si tu ne vois pas ce digest, tu peux
toujours l'obtenir avec `brain digest`.

## Quand écrire

Écris **sans qu'on te le demande** dès qu'apparaît une information qui servira dans une autre session :

| Situation | Commande |
|---|---|
| Préférence, contrainte, info durable sur l'utilisateur | `brain put facts '{"key":"...","value":"...","category":"preference"}'` |
| Nouveau projet, changement de statut, stack, chemin | `brain put projects '{"name":"...","status":"active","stack":["..."],"path":"..."}'` |
| Personne, client, organisation, service récurrent | `brain put people '{"name":"...","kind":"client"}'` |
| Chose à faire plus tard, boucle ouverte | `brain add tasks '{"title":"...","project":"...","priority":"medium"}'` |
| Choix technique structurant | `brain add decisions '{"title":"...","decision":"...","rationale":"...","alternatives":["..."]}'` |
| Erreur rencontrée et sa résolution | `brain add lessons '{"problem":"...","cause":"...","fix":"..."}'` |
| Fait marquant, résumé de session, idée | `brain add journal '{"kind":"session","text":"..."}'` |
| Commande/config réutilisable | `brain put snippets '{"name":"...","lang":"bash","code":"..."}'` |

`facts`, `projects`, `people` et `snippets` sont des **upserts** (clé `key` ou `name`) : réécrire
met à jour sans dupliquer. Les autres collections sont en insertion, avec horodatage automatique.

## Quand lire

- **Toujours en début de tâche non triviale** : `brain search "<mots-clés>"` avant de redemander
  une information à l'utilisateur ou de réinventer une solution.
- Avant de proposer une architecture : `brain ls decisions --limit 20` et `brain ls lessons`.
- Pour savoir où en est un projet : `brain ls tasks --filter '{"project":"brain","status":{"$ne":"done"}}'`.
- Détail d'un document : `brain get <collection> <id>`.

## Commandes

```bash
brain digest [--max 6000] [--json]         # contexte compact complet
brain search "<texte>" [--limit 8] [--collection facts]
brain ls <coll> [--filter '<json>'] [--limit 25] [--sort '<json>']
brain get <coll> <id> | brain rm <coll> <id> | brain done <taskId>
brain stats | brain schema | brain init
```

Collections : `facts`, `projects`, `people`, `tasks`, `decisions`, `lessons`, `journal`, `sessions`, `snippets`.
Toutes ont un index texte nommé `text_search` (recherche insensible au stemming, `default_language: none`).

## Trace automatique des sessions

L'extension `mongodb-brain` écrit **automatiquement** une entrée par session dans `sessions`
(clé `sessionId`) : dossier, modèle, durée, nombre d'échanges, outils utilisés, fichiers touchés,
premier et dernier message. Aucun appel modèle, aucun token consommé.

Conséquence pratique : tu n'as pas besoin de noter « telle session a servi à X », c'est déjà là.
Pour retrouver à quoi a servi une session :

```bash
brain ls sessions --limit 10                                    # les dernières
brain search "migration atlas" --collection sessions            # par contenu
brain ls sessions --filter '{"cwd":"/chemin/vers/projet"}'    # par dossier
```

En revanche la trace ne contient **pas** le sens de ce qui a été fait : les faits, décisions,
leçons et tâches restent à écrire à la main (voir tableau ci-dessus).

## Règles

1. **Ne jamais stocker de secret** (mot de passe, token, clé API) dans le cerveau — seulement
   *l'emplacement* du secret et comment le lire.
2. `facts.value` est **toujours une chaîne** : stringifier les objets (`"{\"a\":1}"`), ne pas
   stocker de sous-document (les index texte n'indexent que les chaînes).
3. Une clé `facts` = un concept unique, en `snake_case`, stable dans le temps. Pour corriger une
   info, réutiliser la même clé (upsert) plutôt que d'en créer une variante.
4. Écrire court et factuel : le digest est relu à chaque session, pas de blabla.
5. Marquer la fraîcheur : `confidence` (`low`/`medium`/`high`) et `source` (`user`, `session`,
   `deduction`) sur les faits, pour distinguer une info vérifiée d'une supposition.
6. Une leçon ne s'écrit qu'après avoir réellement résolu le problème (`fix` non vide).
7. Ne pas dupliquer ce qui est déjà dans le repo (code, docs) : le cerveau stocke du contexte,
   pas des copies de fichiers.
