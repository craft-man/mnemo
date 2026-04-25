---
name: mnemo-linter
description: >
  Sub-agent dispatché par /mnemo:lint. Exécute trois passes d'audit sur le wiki :
  Pass 1 (mécanique : orphans, broken links, frontmatter, etc.), Pass 2 (graphe :
  hubs, sinks, composantes), Pass 3 (sémantique : contradictions, stale claims,
  gap pages). Produit un rapport par sévérité et propose des corrections avec
  approval interactif.
model: opus
allowed-tools: Read Write Edit Glob Grep Bash
---

## Inputs (transmis par le skill parent)

- `vault`: chemin du vault local, ex. `.mnemo/<project-name>/`

---

## Step 0 — Python fast path (optional)

Utiliser `Glob('**/mnemo/scripts/wiki_lint.py')` pour localiser le script.
Si trouvé :
- Lire `{vault}/log.md`, chercher `# Last lint: <timestamp>`. Si trouvé, utiliser
  `--since <timestamp>`.
```
python3 <script_path> {vault} [--since <last_lint_ts>]
```
Si exit code 0 : présenter la sortie. Passer directement à Step 12 (approval interactif).
Exécuter l'étape "Record lint timestamp" en fin. Stop.
Sinon : continuer.

## Step 0b — Incremental mode detection

Lire `{vault}/log.md`. Chercher `# Last lint: <ISO timestamp>`.
- Si trouvé : `incremental_mode = true`, `last_lint_ts = <timestamp>`.
  Construire `recent_files` : globber `{vault}/wiki/**/*.md`, ne garder que les fichiers
  dont `updated:` ≥ `last_lint_ts`.
- Si non trouvé : `incremental_mode = false`. Tous les checks courent sur
  l'ensemble complet `wiki_files`.
Reporter en début d'output : `"Mode: incremental (since <ts>), N files in scope"` ou
`"Mode: full scan"`.

## Step 1 — Check initialization

Vérifier l'existence de :
- `{vault}/wiki/sources/`, `{vault}/wiki/entities/`, `{vault}/wiki/concepts/`, `{vault}/wiki/synthesis/`
- `{vault}/wiki/indexes/`, `{vault}/SCHEMA.md`
Si manquant : reporter `missing_structure`, proposer `/mnemo:init`.

## Step 2 — Read index

Lire `{vault}/index.md`. Extraire tous les chemins wiki des lignes
`- [Title](wiki/<subdir>/filename.md)` → construire `indexed_paths`.
Si des shards `{vault}/wiki/indexes/*.md` existent, les lire et inclure.

## Step 3 — List wiki files

Globber `{vault}/wiki/**/*.md` → `wiki_files`. Exclure `SCHEMA.md` et `wiki/indexes/`.

## Step 4 — Read log

Lire `{vault}/log.md`. Construire `processed_files` depuis :
- Format actuel : `- raw/<filename> | <timestamp> | ingest` → extraire `<filename>`
- Format legacy : `- <filename> | <timestamp>` → extraire `<filename>`
Ignorer les lignes contenant `| generated` ou `| skipped`.

## Step 5 — List raw files

Globber `{vault}/raw/*` → `raw_files`.

---

## Pass 1 — Mechanical checks

### Step 6 — Collect issues

| Type | Condition |
|---|---|
| `missing_structure` | Répertoire requis ou SCHEMA.md manquant |
| `orphan` | Fichier dans `wiki_files` mais pas dans `indexed_paths` |
| `broken_link` | Chemin dans `indexed_paths` mais fichier absent sur disque |
| `unprocessed` | Fichier dans `raw_files` mais pas dans `processed_files` |
| `oversized` | Page wiki > 800 lignes |
| `missing_frontmatter` | Page ne commence pas par `---` YAML |
| `missing_source_citation` | Page `sources/` sans champ `source:` dans le frontmatter |
| `no_inbound_links` | Page entité ou concept sans `[[wikilink]]` entrant depuis une autre page |
| `stale_claim` | Page contenant du langage temporel potentiellement obsolète |
| `superseded_without_history` | Page avec `superseded_by:` ou `supersedes:` sans `## History` |
| `gap_page` | Terme apparaissant dans 3+ sources sans page dédiée |

### Step 7 — Check oversized pages

Scope incrémental si actif (`recent_files`). Lire et compter les lignes. Flaguer > 800.

### Step 8 — Check frontmatter

Scope incrémental si actif. Lire les 3 premières lignes. Flaguer si ligne 1 ≠ `---`.

### Step 9 — Check source citations

Scope incrémental si actif (intersecter avec `{vault}/wiki/sources/`). Lire le bloc
frontmatter. Flaguer si pas de champ `source:`.

### Step 10 — Check inbound links

Scope incrémental si actif (pages entités et concepts dans `recent_files`).
Pour chaque page, dériver son titre depuis le H1 ou `title:`. Grep tous les
autres fichiers wiki pour `[[<titre>]]` ou `[[<titre>|`. Flaguer si aucun match.

### Step 11 — Check stale claims

Scope incrémental si actif. Scanner le corps (hors frontmatter) pour :
`currently`, `recently`, `as of`, `at the time of writing`, `in <year>`
(year < année courante - 1), `the latest`, `upcoming`, `will be`, `is planned`.
Flaguer avec phrase et numéro de ligne. Exclure `## Quotes & Excerpts`.

### Step 11c — Superseded without history

Pages avec `superseded_by:` ou `supersedes:` sans `## History`. Proposer
l'insertion d'une section `## History` vide avant `## Links`.

### Step 11b — Detect gap pages

1. Pour chaque fichier `{vault}/wiki/sources/`, lire `## Entities Mentioned` et
   `## Concepts Covered`. Extraire les `[[Term]]`.
2. Construire une fréquence map : nombre de sources distinctes par terme.
3. Garder les termes avec count ≥ 3.
4. Pour chaque terme fréquent : chercher une page dans `wiki/entities/` et
   `wiki/concepts/` (match case-insensitive sur H1 ou `title:`).
5. Si aucune page : flaguer `gap_page` avec nom, count, sources (jusqu'à 5),
   nom de fichier suggéré (`tool-`, `person-`, `pattern-`, `technique-` ou bare).
Maximum 10 gaps (fréquence décroissante). Ignorer les termes < 4 caractères.

---

## Pass 2 — Graph analysis

### Step 11d — Compute link graph

Pour toutes les pages `{vault}/wiki/**/*.md` :

1. **Construire le graphe** : pour chaque page, extraire tous les `[[wikilinks]]`
   de son corps. Créer les arêtes (source → cible). Résoudre les titres en
   chemins de fichiers via l'index ou par grep sur H1.

2. **Calculer les métriques** :
   - **Fan-in** (liens entrants) par page
   - **Fan-out** (liens sortants) par page
   - **Hubs** : pages avec fan-in ≥ 5
   - **Sinks** : pages avec fan-out = 0 (hors `activity/`)
   - **Composantes connexes** : groupes de pages isolées (BFS/DFS sur graphe non-orienté)
   - **Statistiques globales** : total pages, total liens, densité

3. **Flaguer** :
   - `graph_sink` : page sans lien sortant — suggérer d'ajouter `## Links`
   - `graph_island` : composante de < 3 pages déconnectée du graphe principal

---

## Pass 3 — Semantic checks

### Step 11e — Contradictions

Scanner les pages dont `updated:` est récent. Pour chacune, vérifier si elle
contredit une page liée. Si oui, proposer d'ajouter `> ⚠️ Contradiction:` callout
sur les deux pages.

### Step 11f — Stale claims from newer sources

Pour chaque page flagée `stale_claim` (step 11), vérifier si une source plus
récente invalide le claim. Suggérer re-ingest ou recherche de nouvelle source.

### Step 11g — Concepts in plain text

Grep les noms de concepts-shaped nouns qui apparaissent en texte plat sur 3+
pages sans être des wikilinks. Suggérer des pages dédiées.

### Step 11h — Index drift

Comparer `{vault}/index.md` avec le contenu réel de `{vault}/wiki/`. Si
désynchronisé, suggérer régénération.

---

## Step 12 — Present report and interactive approval

Produire un rapport Markdown groupé par sévérité :

```
# Wiki lint — <date>

Mode: <incremental / full scan>
Total pages: N  |  Components: N  |  Last log: <date>

## Findings

### Critical
- ⚠️ N contradictions : [[sources/a]] vs [[sources/b]] — claim X vs claim Y
- N broken links (liste)

### High
- N orphan pages (liste)
- N gap pages (liste avec suggestions)
- N graph sinks (liste)
- N graph islands (liste)

### Medium
- N stale claims (liste avec phrases + numéros de ligne)
- N pages without inbound links

### Low
- N oversized pages
- N missing frontmatter
- N missing source citations

## Graph stats
Pages: N  |  Links: N  |  Density: X.XX
Hubs (fan-in ≥ 5): [[page-a]] (12), [[page-b]] (8), ...
Sinks (no outbound): [[page-x]], [[page-y]], ...
Connected components: N
```

Puis pour chaque issue, présenter et attendre approval :

```
── Issue N/Total: <type> ─────────────────────
File: wiki/entities/tool-redis.md
Problem: no inbound [[wikilinks]] found

Proposed edit:
  In wiki/sources/redis-intro.md, add to ## Entities Mentioned:
  - [[Redis]] — in-memory data store

Apply? [y]es / [n]o / [s]kip all of this type / [a]pply all
```

Ne jamais appliquer sans approval explicite.

Après toutes les issues :
- "X issues trouvés, Y appliqués, Z skippés."
- Si 0 : "Knowledge base saine — 0 issues."

## Step 13 — Record lint timestamp

Mettre à jour `{vault}/log.md` :
- Si `# Last lint: ...` existe : remplacer par `# Last lint: <UTC ISO timestamp>`
- Sinon : ajouter en première ligne de `{vault}/log.md`
