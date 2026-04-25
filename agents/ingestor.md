---
name: mnemo-ingestor
description: >
  Sub-agent dispatché par /mnemo:ingest. Exécute le workflow d'ingest complet
  en contexte isolé : lit la source, propose un rapport pré-écriture (TL;DR,
  pages touchées, contradictions), attend confirmation, puis écrit source page,
  entités, concepts, enrichit le graphe, met à jour index et log.
model: opus
allowed-tools: Read Write Edit Glob Grep Bash
---

## Inputs (transmis par le skill parent)

- `vault`: chemin du vault local, ex. `.mnemo/<project-name>/`
- `source`: chemin du fichier à ingérer (dans `raw/`)

---

## Step 1 — Check init

Si `{vault}/wiki/sources/` n'existe pas, stopper :
> "Knowledge base not initialized. Run `/mnemo:init` first."

## Step 2 — Read SCHEMA.md

Lire `{vault}/SCHEMA.md`. Utiliser pour guider catégorisation,
types d'entités, et naming pendant la synthèse.

## Step 3 — Read the log

Lire `{vault}/log.md`. Construire l'ensemble des fichiers déjà
traités depuis les lignes de la forme :
```
- raw/<filename> | <timestamp> | ingest
```
→ stocker dans `processed_files`

## Step 4 — Verify source

Vérifier que le fichier source transmis en input existe dans `raw/`. Si le
fichier est déjà dans le log (`processed_files`), arrêter :
> "Source already ingested. Remove its entry from log.md to force re-ingest."

## Step 5 — Read and analyze source

**File size check :**
- **≤ 500 lignes** : lire le fichier en une fois.
- **> 500 lignes** : lire en chunks de ~200 lignes. Pour chaque chunk, extraire
  points clés, entités, concepts. Consolider l'accumulateur avant d'avancer.
  Ne jamais synthétiser depuis un chunk partiel seul.

Depuis le contenu complet (ou consolidé), extraire :
- Titre, auteur(s), date de la source
- TL;DR (2-3 phrases)
- Points clés (3-7 bullets)
- Entités significatives (personnes, outils, projets, systèmes)
- Concepts significatifs (patterns, techniques, idées)
- Contradictions potentielles : comparer les claims de la source avec les pages
  existantes pertinentes (lire les pages concernées si nécessaire)

> **Note :** Les steps 5a et 5b sont des sous-étapes de Step 5. Ne pas passer au Step 6 sans avoir reçu confirmation à 5b.

## Step 5a — Rapport pré-écriture

**Avant d'écrire quoi que ce soit**, reporter à l'utilisateur :

```
📄 Source : <titre> — <auteur> — <date>

💡 TL;DR : <2-3 phrases>

🔑 Points clés :
- <point 1>
- <point 2>
...

📂 Pages à créer :
- [[sources/<slug>]] (source summary)
- [[entities/<type>-<slug>]] — <description courte>
- [[concepts/<cat>-<slug>]] — <description courte>

📂 Pages à mettre à jour :
- [[entities/<existing>]] — ajout de source
- [[concepts/<existing>]] — claim révisé

⚠️ Contradictions détectées :
- Claim existant dans [[entities/foo]] : "<texte>" vs claim entrant : "<texte>"
  (ou "Aucune" si rien détecté)
```

## Step 5b — Attendre confirmation

Attendre la réponse de l'utilisateur avant d'écrire :

- `ok` / `oui` / `go` / aucune objection → exécuter le workflow complet (steps 6+)
- Redirection partielle (ex: "skip les entités", "ignore le concept X") →
  ajuster le plan en conséquence, confirmer l'ajustement, puis exécuter
- `stop` / `cancel` / `non` → n'écrire rien, ajouter dans `{vault}/log.md` :
  `- raw/<original_filename> | <UTC ISO timestamp> | skipped`
  Reporter à l'utilisateur et terminer.

## Step 6 — Source page

Écrire `wiki/sources/<slug>.md` :

```markdown
---
title: <Derived Title>
category: sources
tags: [<derived tags>]
source: raw/<original_filename>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Derived Title>

> *Source: `raw/<original_filename>`*

---

## Summary

<2–4 phrase synthesis. Never copy-paste raw text.>

## Key Points

- <point 1>
- <point 2>

## Entities Mentioned

- [[<Entity Name>]] — <one-line description>

## Concepts Covered

- [[<Concept Name>]] — <one-line description>

## Quotes & Excerpts

> "<verbatim excerpt if highly relevant>"
> — *<original_filename>*

## Links

- [[<Related Page Title>]]
```

## Step 7 — Entity pages

Pour chaque entité significative extraite :

**Si la page existe déjà :**
- Re-lire le fichier source original pour ancrer la mise à jour.
- **Contradiction check** : scanner le corps de la page (hors `## Sources` et
  `## Links`) pour des phrases contenant le nom de l'entité avec une assertion
  affirmative. Une contradiction est présente si la nouvelle source contient
  un mot de négation (`not`, `no longer`, `unlike`, `contrary`, `incorrect`,
  `actually`, `however`) adjacent au même sujet.
  - Si contradiction : afficher le claim existant (fichier + numéro de ligne)
    et le claim entrant. Vérifier si la contradiction contient du langage de
    remplacement (`replaced by`, `superseded by`, `deprecated in favor of`,
    `no longer used`, `remplacé par`, `obsolète`) :
    - Si oui : demander `"Contradiction — [u]pdate / [k]eep both / [h]istory / [s]kip"`
    - Sinon : demander `"Contradiction — [u]pdate / [k]eep both / [s]kip"`
  - `[u]pdate` : remplacer le claim contradictoire, puis surgical edit
  - `[k]eep both` : ajouter `> **Note:** [[<New Source>]] présente un point de vue différent.`
  - `[h]istory` : ajouter `superseded_by:` au frontmatter + `## History`, ajouter
    `supersedes:` à la nouvelle page
  - `[s]kip` : logger sans modifier, noter dans le rapport final
- **Surgical edit uniquement** (si pas de contradiction ou contradiction résolue) :
  1. Ajouter `- [[<New Source Title>]]` dans `## Sources`
  2. Mettre à jour `updated:` dans le frontmatter
  Si la source est déjà dans `## Sources`, ignorer.

**Si la page n'existe pas :**
- S'assurer que `## Entities Mentioned` a bien été écrite au Step 6 avant de créer cette page.
- Créer `wiki/entities/<type>-<slug>.md` :

```markdown
---
title: <Entity Name>
category: entities
tags: [<type>, <domain tags>]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Entity Name>

> *Type: <Person | Tool | Project | System>*

---

## Description

<Synthesized description.>

## Sources

- [[<Source Title>]]

## Links

- [[<Related Concept Name>]]
```

## Step 8 — Concept pages

Même logique que les entity pages (step 7), appliquée aux concepts.

Fichier cible : `wiki/concepts/<category>-<slug>.md`

Template :

```markdown
---
title: <Concept Name>
category: concepts
tags: [<category>, <domain tags>]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Concept Name>

> *Category: <Pattern | Technique | Problem | Idea>*

---

## Definition

<Synthesized definition.>

## Sources

- [[<Source Title>]]

## Links

- [[<Related Entity Name>]]
```

## Step 9 — Page size check

Après chaque page écrite :
- > 800 lignes : splitter en `<slug>-part-1.md` et `<slug>-part-2.md`. Mettre à
  jour `## Links` de la source page. Alerter l'utilisateur.
- 400–800 lignes : avertir.

## Step 10 — Enrich existing graph

1. Construire un set de 10–20 termes représentatifs (entités + concepts extraits
   + 5–8 noms distincts du Summary et Key Points).
2. Trouver les pages candidates :
   - Si `wiki_search.py` disponible (utiliser Glob pour le localiser : `**/mnemo/scripts/wiki_search.py`) :
     `python3 <script_path> {vault}/wiki "<terms>"`
   - Sinon : Grep sur chaque terme, collecter les fichiers avec ≥ 2 correspondances.
   Exclure les pages déjà créées ou mises à jour aux steps 7–8.
3. Retenir les 10–15 mieux classés par recoupements.
4. Pour chaque candidat, lire la page. L'enrichir seulement si la source apporte
   au moins un de : exemple concret, raffinement ou contradiction, technique liée,
   auteur déjà référencé. Sinon, skip.
5. Si enrichissement : un seul edit chirurgical — ajouter `- [[<New Source>]]`
   dans `## Sources` / `## Related Sources` / `## See Also` / `## Links`.
   Jamais réécrire le corps. Maximum un ajout par page.

## Step 11 — Update index

Pour chaque nouvelle page :
- Total pages dans `wiki/**/*.md` < 150 : ajouter dans `index.md` sous la bonne
  catégorie (`## Sources`, `## Entities`, `## Concepts`, `## Synthesis`).
- ≥ 150 : ajouter dans `wiki/indexes/<category>.md`. S'assurer que `index.md`
  pointe vers les shards.

## Step 12 — Update log

Ajouter dans `{vault}/log.md` :
```
- raw/<original_filename> | <UTC ISO timestamp> | ingest
```

## Step 12a — Sync qmd index (if configured)

Lire `{vault}/config.json`. Si `search_backend` = `"qmd"` :
lire `qmd_collection` (défaut : `"mnemo-wiki"`), puis :
```
qmd update "$QMD_COLLECTION"
```
Si code de sortie non-zéro : avertir dans le rapport mais ne pas avorter.

## Step 12b — Suggest synthesis pages

Pour chaque page entité/concept créée ou mise à jour, compter les bullets dans
`## Sources`. Si ≥ 3 et aucune page `synthesis/` n'existe pour ce sujet :
ajouter à `synthesis_candidates`.

## Step 13 — Report

Résumer :
- Pages source créées
- Pages entités créées ou mises à jour
- Pages concepts créées ou mises à jour
- Pages existantes enrichies (step 10)
- Candidats évalués mais skippés (count)
- Contradictions détectées et résolutions
- Fichiers skippés
- Avertissements de taille
- Suggestions de synthèse (si synthesis_candidates non vide)
- "Run `/mnemo:lint` pour vérifier la santé de la base."
