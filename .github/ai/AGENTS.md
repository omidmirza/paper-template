# Working on this paper

Rules for Codex, Claude Code and any other coding agent. Follow them unless the user says otherwise.
This file is `.github/ai/AGENTS.md`. The top folder has no agent files, so in Claude Code and in Codex the user starts
with "Read .github/ai/AGENTS.md".
`.github/ai/PAPERKIT_FOR_AI.md` has every LaTeX command and the setup recipe for a first chat.
`toggle_helper.tex` (top folder) shows what each command prints in each version.
Everything about assistants is in `.github/ai/`. The paper's own files never mention AI.

## How the paper moves

```
  Overleaf  <-- Overleaf menu, GitHub: push / pull -->  GitHub  <-- git pull / push -->  laptop
  co-authors write on main                               main, branches,                 the user, you,
                                                         pull requests, CI               figures (.github/Makefile)
```

- GitHub (remote `origin`, branch `main`) is the hub. Overleaf syncs with it when a person presses push
  or pull in Overleaf's GitHub menu. You cannot press it; ask the user.
- Optional: a direct git link to Overleaf (remote `overleaf`, branch `master`), used by
  `.github/tools/sync_overleaf.sh` and `make -f .github/Makefile live`. Use it only if that remote exists.
- The user checks every change before it reaches `main`.
- Co-authors may each work on a branch (`anna/intro`) with a pull request to `main`. CI builds every version
  on every push. Overleaf syncs with `main` only. Details: `.github/docs/team.md`.

## Where things are

| Path | What |
|---|---|
| `main.tex` | the body. On Overleaf it builds the review copy. |
| `setup.tex` | title, authors, versions, and every option with a short comment. Look for `EDIT HERE`. |
| `versions/*.tex` | one file per PDF: template (documentclass line), version, page limit. |
| `sections/*.tex` | the text. Edit here. `appendix_*.tex` hold the appendix (proofs), printed only in the long versions; `table_*.tex` hold the tables, read with `\input{sections/table_<name>}`. |
| `figures/src/<name>.py` | figure code, and the experiment code (`figures/src/simulate.py` in the template), which writes the results that the figures read to `figures/data/`. `figures/auto/` holds the made figures (never edit them by hand, always commit them); `figures/static/` holds hand-made images. |
| `refs/references.bib` | bibliography. `refs/extended_labels.tex` holds the labels of the arXiv version, copied there by the build. |
| `.github/` | the GitHub page (`README.md`), the build on every push (`workflows/`), packages and classes (`tex/`), the figure engine (`python/`), the `Makefile`, scripts (`tools/`), short docs (`docs/`). Do not edit it, except `.github/tex/layout.tex`, where another class can get its own title block. |
| `.github/ai/` | these rules, `PAPERKIT_FOR_AI.md`, `README.md` (for people) and `editmarks.cfg`, which declares your editor key `ai`. `.github/ai/skills/paper/SKILL.md` has step-by-step workflows. |

Keep the top folder clean: only `.github/`, `figures/`, `refs/`, `sections/`, `versions/`, `main.tex`, `setup.tex` and `latexmkrc`.
The build writes to `.github/build/` and `.github/pdf/`; nothing else may appear at the top.
New files go into the folders above. TeX finds `.github/tex/` through `latexmkrc`, also on Overleaf.
Never write about AI, assistants or tools in the paper's files (text, comments, `setup.tex`, figure code).
Write one sentence per line in `.tex` files.

## Editing text

- Mark every change with the editor key `ai`: `\added{ai}{new}`, `\deleted{ai}{old}`, `\replaced{ai}{new}{old}`,
  `\authnote{ai}{question}`. For whole paragraphs or floats: `\begin{addedblock}{ai} ... \end{addedblock}`, `deletedblock`.
  The key is declared in `.github/ai/editmarks.cfg`, not in `setup.tex`.
- Edit without marks only when the user says so. The first-chat setup of the template has no marks.
- `\deleted` and `\replaced` cannot span paragraphs. Put `\cite`, `\ref` and math inside them in braces.
- Version-specific text: `\onlyin{arxiv}{..}`, `\exceptin{arxiv}{..}`, `\ifversion{conference}{short}{long}`,
  and the environment `\begin{arxiv} ... \end{arxiv}` (each on its own line).
  Groups such as `long` work in `\onlyin` and `\ifversion` but have no environment.
  Use only names that `setup.tex` declares.
- Never touch another editor's marks unless asked. Accepting them is the authors' decision.

## Figures

- Never scale a figure in LaTeX. Use `\autofig{<name>}`; the slot is measured and the figure is drawn for it.
- To change a figure, edit `figures/src/<name>.py` or the slot (`aspect=`, `height=`, wrap width, column).
- Then run `make -f .github/Makefile`, and check with `PYTHONPATH=.github/python $PAPERKIT_PYTHON -m autofig audit .github/pdf/<entry>.pdf`.

## Build

- Run `make -f .github/Makefile`, or `bash .github/tools/build.sh [versions/<entry>.tex]`.
  Call scripts with `bash`, since Overleaf's GitHub Sync drops the executable bit.
- Report its table: status, pages, page limit, undefined references.
  Fix errors, `??` and OVER before committing. Python: `$PAPERKIT_PYTHON`.

## Git

- Before you change anything, run `git pull origin main`. If co-authors wrote on Overleaf, first ask the
  user to press "Push Overleaf changes to GitHub" in Overleaf. With an `overleaf` remote:
  `bash .github/tools/sync_overleaf.sh --no-push`.
- Commit with a short plain message that says what changed, as a colleague would write it
  ("Intro: shorter motivation"). No tool names, no mention of AI, no generated trailers.
- Never commit `.github/build/`, `.github/pdf/`, tokens or secrets. Always commit `figures/auto/`, since Overleaf cannot run Python.
- Push only when asked. Small work the user asked for: `git push origin main`.
  Anything to review: a branch named after the topic (for example `intro-wording`) and `gh pr create`.
  Then tell the user to press "Pull GitHub changes into Overleaf".
- Never force-push, never rewrite pushed history, never reset someone's work.
  On a merge conflict, stop, show the files and ask.
- Never type a token or password. If git asks for one, stop and tell the user.

## On GitHub (pull requests)

- Read with `gh pr view <n>` and `gh pr diff <n>`, and recent work with `git log -p -3`.
- Comment with `gh pr review <n> --comment -b "..."`. Quote the sentence, say what is unclear, suggest a fix.
  Do not approve or merge unless asked.
- Fixes go to a topic branch and a pull request. Never push to `main` from GitHub.
- As the Claude GitHub app or a Codex cloud task you may have no TeX Live or Python.
  Change the text, and say in the pull request that the figures still need `make -f .github/Makefile` on a laptop.

## Direct edits on Overleaf

- In the Overleaf editor, make small text edits only, marked with `ai`.
  No figures, no `setup.tex`, no deleted or renamed files. Say which file and line you changed.
  They reach GitHub with the next push from Overleaf.

## Requests that work well

1. "Set up this template for my paper: title ..., authors ..., versions ..., templates ..."
2. "Some references show ??. Fix them."
3. "Some numbers changed in the code. Redraw every figure and push."
4. "Add my co-author's comments as their edits."
5. "Make the conference version fit in six pages; keep every trick inside `\onlyin{conference}`."
6. "Review the pull request and comment on unclear sentences."
7. "List all open TODOs and author notes with their authors."
8. "Release v2-arxiv: build, tag, and make the arXiv zip."
