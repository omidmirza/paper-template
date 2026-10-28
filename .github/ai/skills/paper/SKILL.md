---
name: paper
description: Work on a paperkit LaTeX paper kept on GitHub and synced with Overleaf - set up the template for a new paper (title, authors, versions, templates, page limits), edit text as tracked AI edits, add version-specific text, make the conference version fit, resize or redraw figures for their slot, build every version, push to GitHub, review pull requests with gh, release an arXiv zip, latexdiff. Use for any request about the paper, its versions, figures, co-author edits, pull requests or Overleaf.
---

# Paper workflows

Rules first: `.github/ai/AGENTS.md` (tracked edits with key `ai`, never scale figures, never force-push, no tokens).
Commands and the setup recipe in full: `.github/ai/PAPERKIT_FOR_AI.md`. Every command with its output per version: `toggle_helper.tex` in the top folder.
Folders: text, appendix (`appendix_*.tex`) and tables (`table_*.tex`) in `sections/`, figure and experiment code in
`figures/src/`, results in `figures/data/`, packages, classes and `layout.tex` in `.github/tex/`, docs in `.github/docs/`.
Nothing new in the top folder; builds write to `.github/build/` and `.github/pdf/`. Text: one sentence per line.
Python for figures: `$PAPERKIT_PYTHON`, else `.github/.venv/bin/python`. Engine: `PYTHONPATH=.github/python <python> -m autofig`.

GitHub (`origin`, `main`) is the hub. Overleaf pushes to and pulls from it through its own GitHub menu,
pressed by a person. The laptop uses `git pull` and `git push`. A direct `overleaf` remote is optional.

## Set up the template (first chat)
"Set up this template for my paper: title ..., authors ..., versions ..., templates ..." Edit silently
(no `\added`), only at the `EDIT HERE` places:
1. `setup.tex` title block: `\papertitle`, `\paperauthors`, `\paperaffiliation`.
2. `setup.tex` authors block: one `\DeclareEditor{key}{XY} \editorname{key}{Full Name}` per person
   (key: short lowercase first name). The `ai` editor is predefined in `.github/ai/editmarks.cfg`: no line for it.
   Replace the example keys `author1`... in `sections/`.
3. `setup.tex` versions block: one `\DeclareVersion[colour]{name}` per version, groups if useful, and
   `version=<first version>` in the `versiontoggle` options.
4. `versions/`: one file per PDF. Set the documentclass line, `\def\paperversion{name}` and `% page limit: N`.
   Remove files of versions the user does not want. Keep `review.tex`. The long version's file name
   contains `arxiv` (its labels feed `\arxivref`), or set `PAPERKIT_EXTENDED`.
5. Version names used in the text: `grep -rn "onlyin\|exceptin\|ifversion\|begin{arxiv\|begin{journal\|begin{conference" sections main.tex .github/tex/layout.tex`.
   Rename or remove every use of a version or group that no longer exists.
6. `make -f .github/Makefile`. Every row `ok`, `undef` 0, pages within the limit. Fix and repeat. Then `git add -A && git commit -m "Set up: <title>"`.
Report: title, authors with colours, the table, and what the user should check.

## Before any change
`git pull origin main` (ask the user to press "Push Overleaf changes to GitHub" first if co-authors wrote
on Overleaf). With an `overleaf` remote: `bash .github/tools/sync_overleaf.sh --no-push`.

## Edit text (tracked)
1. Find the sentence in `sections/` (grep). 2. Wrap the change: `\replaced{ai}{new}{old}` / `\added{ai}{..}` /
   `\deleted{ai}{..}`. Version-only change: inside `\onlyin{<v>}{..}` or `\ifversion{<v>}{..}{..}`.
3. Build the affected entry (`bash .github/tools/build.sh versions/<entry>.tex`), check 0 errors / 0 undefined refs.
4. `git add -A && git commit -m "<what changed>"`: a short plain message, as a colleague would write it.

## Resize or redraw a figure
1. Slot change: the width macro, `aspect=`, `height=` or the float. Look change: `figures/src/<name>.py`.
   New results: run the experiment code in `figures/src/` that writes `figures/data/` (`make -f .github/Makefile data` in the template); a spec that
   names `"figures/data/<file>"` is redrawn when that file changes.
2. `make -f .github/Makefile` (LaTeX notes the slot, the engine draws `figures/auto/<name>_w<W>_h<H>_f<F>.pdf`, LaTeX again).
3. `git add figures/auto figures/src sections && git commit -m "<figure>: <change>"`. Commit the `.json` files too.

## Fix labels and references
1. `??` in a PDF: build, then read `.github/build/<entry>/<entry>.log` for `Reference ... undefined` / `Citation ... undefined`.
2. Missing label: add `\label{..}` or fix the name. Missing citation: add it to `refs/references.bib`.
   A reference to the arXiv appendix needs `refs/extended_labels.tex`: `make -f .github/Makefile` builds the arXiv entry first.
3. Axis labels: `xlabel`/`ylabel` in `figures/src/<name>.py` (quantity and unit), then `make -f .github/Makefile`.

## Edits for someone else
"Add my co-author's comments as their edits": use that person's key from `setup.tex`, never `ai`,
and say so in the commit message.

## Send
Push only when asked. Small asked-for work: `git push origin main`. Anything to review: a topic branch such as `intro-wording`,
`git push origin <branch>`, `gh pr create --base main`. Then tell the user: "In Overleaf, press Pull GitHub
changes into Overleaf." With an `overleaf` remote: `bash .github/tools/sync_overleaf.sh` (exit 2 = conflict: stop, list, ask).

## Make it fit
Conference only: every trick inside `\onlyin{conference}{..}` (preamble: `\ifversion{conference}{..}{}`):
`\vspace{-4pt}` after a figure label, `\setlength{\tabcolsep}{3pt}` before a tabular, a shorter caption with
`\ifversion`, `\looseness=-1` at a paragraph end, a smaller `aspect`. Never scale a figure.
Rebuild and report pages against `% page limit` per entry.

## Review on GitHub
1. `git pull origin main`; `gh pr view <n>`, `gh pr diff <n>`.
2. Build the affected entries if you can; note `??` and figure problems.
3. `gh pr review <n> --comment -b "<file:line, the sentence, what is unclear, a suggested fix>"`.
4. Fixes asked for: a topic branch, tracked `ai` edits, push the branch, `gh pr create --base main`.
   Never push to `main`, never merge, never force-push unless the user says so.

## Direct Overleaf edits
Small text fixes only, as tracked `ai` edits. No figures, no preamble, no file moves. Tell the user the file
and the line; they reach GitHub with the next push in Overleaf.

## Release and diff
- `make -f .github/Makefile release TAG=<tag>` → `.github/releases/<tag>/` (PDFs and a checked `arxiv.zip`). Push tags only when asked.
- `make -f .github/Makefile diff OLD=<ref>` → `.github/pdf/diff_<old>_<new>.pdf`.
