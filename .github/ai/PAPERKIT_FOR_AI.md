# paperkit for any AI chat

Upload or paste this file (`.github/ai/PAPERKIT_FOR_AI.md` in the paper) into ChatGPT, Claude, Gemini or any
other AI chat, or open the paper folder in Claude Code or Codex.
The assistant reads it and answers with lines that work in this paper.

## What paperkit is

One set of LaTeX files for every version of a paper: conference, journal and arXiv.
The text that differs is marked once, and each version is built from the same files.
A review copy shows all versions at once, in colour.
Each edit carries its author's initials and colour, and each figure is drawn for the exact space it sits in.

## How the paper moves

```
  Overleaf  <-- Overleaf menu, GitHub: push / pull -->  GitHub (main)  <-- git pull / push -->  laptop
  co-authors write                                       reviews,                               the user, the
                                                         pull requests                          assistant, .github/Makefile
```

- GitHub is the hub. Overleaf syncs with it when a person presses "Push Overleaf changes to GitHub"
  or "Pull GitHub changes into Overleaf" in Overleaf's GitHub menu.
  A new Overleaf project can start from the repo with New project, Import from GitHub.
- The laptop pulls from and pushes to GitHub with git, and redraws the figures with `make -f .github/Makefile`.
- An assistant on GitHub reviews pull requests and suggests fixes as pull requests. The user checks before anything is merged.
- Overleaf cannot run Python, so the made figures in `figures/auto/` are always committed.
- Optional: a direct git link from the laptop to Overleaf (`git.overleaf.com` with a token) for
  `make -f .github/Makefile live`, where a figure resized on Overleaf comes back redrawn in seconds.

## The paper

| File | What |
|---|---|
| `main.tex` | the body. Compiled on its own (Overleaf) it gives the review copy. |
| `setup.tex` | title, authors and their colours, versions, every option with a short comment. Every place to change says `EDIT HERE`. |
| `versions/<name>.tex` | one file per PDF: the template (its documentclass line), the version, the page limit. On Overleaf, open it and press Recompile. |
| `sections/*.tex` | the text. `appendix_*.tex`: the appendix (proofs), only in the long versions. `table_*.tex`: tables, `\input{sections/table_<name>}`. |
| `figures/src/<name>.py` | draws figure `<name>`. LaTeX includes it with `\autofig{<name>}`. Made figures: `figures/auto/`; hand-made images: `figures/static/`. |
| `figures/src/simulate.py` | experiment code; the results it writes to `figures/data/` are what the figures read. |
| `refs/references.bib` | bibliography. |
| `.github/tex/layout.tex` | the title block of each template (IEEE, IEEE CDC/ACC, Elsevier, Springer, ACM, article). Rarely changed. The rest of `.github/` (packages, classes, figure engine, scripts) is never edited. |
| `.github/docs/` | short notes for people. `toggle_helper.tex` (top folder) lists every command with what each version prints. |
| `.github/ai/` | this file, `AGENTS.md` (the rules for coding agents), `README.md` and `editmarks.cfg`, which declares the editor `ai`, and `skills/paper/SKILL.md` with step-by-step workflows. |

The top folder holds only `.github/`, `figures/`, `refs/`, `sections/`, `versions/`, `main.tex`, `setup.tex` and `latexmkrc`.
New files go into a folder. A build on a laptop writes only to `.github/build/` and `.github/pdf/`.
The paper's files never mention AI: no text or comments about assistants outside `.github/ai/`.
Write one sentence per line in `.tex` files.

The template declares the versions `conference`, `journal`, `arxiv`, the group `long` (journal and arXiv),
the editors `author1`, `author2`, `author3`, and `ai` (in `.github/ai/editmarks.cfg`, not in `setup.tex`).
A paper may rename them: use the names the user gives.

## One file per PDF

On Overleaf, open the file you want in `versions/` (for example `versions/tac.tex`) and press Recompile.
Overleaf compiles the open file.
To make one the default, go to Settings (the gear, bottom left), Compiler, Main document, or right-click the file and choose Set as main file.
With a section file open, Overleaf compiles the main document; `main.tex` alone gives the review copy.
Each file sets its own template and version, so nobody has to edit a switch.
To add a template, copy a file and change its documentclass line.

| File | Template | Version |
|---|---|---|
| `review.tex` | IEEE conference (`IEEEtran`) | review copy: every version and every edit in colour |
| `conference.tex` | IEEE conference (`IEEEtran`) | conference |
| `cdc.tex` | IEEE CDC and ACC (`ieeeconf`, in the project) | conference |
| `acm.tex` | ACM `sigconf` (`acmart`), as used by HSCC and ICCPS | conference |
| `springer.tex` | Springer LNCS (`llncs`) | conference |
| `journal.tex` | Elsevier (`elsarticle`) | journal |
| `tac.tex` | IEEE Transactions, for example TAC (`IEEEtran` journal) | journal |
| `arxiv.tex` | one column (`article`) | arXiv, with the proofs |

## Set up a new paper (first chat)

The user says: "Set up this template for my paper: title ..., authors ..., versions ..., templates ...".
Change only the `EDIT HERE` places, without edit marks:

1. `setup.tex`, title: `\papertitle`, `\paperauthors`, `\paperaffiliation`.
2. `setup.tex`, authors: one line per person, `\DeclareEditor{jane}{JD} \editorname{jane}{Jane Doe}`.
   The key is a short lowercase name. Colours are assigned in order; `\DeclareEditor[RoyalBlue]{..}` picks one.
   The `ai` editor needs no line. Replace the example keys `author1`, `author2`, `author3` in `sections/`.
3. `setup.tex`, versions: one `\DeclareVersion[colour]{name}` per version, a group for several if useful,
   and `version=<first version>` in the `versiontoggle` line.
4. `versions/`: one file per PDF. Copy one, then set its documentclass line, `\def\paperversion{name}` and
   `% page limit: N`. Delete the files of unused versions. Keep `review.tex`. The long version's file name
   must contain `arxiv` (or set `PAPERKIT_EXTENDED=<file stem>` when you run `make -f .github/Makefile`), since the other
   versions read its labels for `\arxivref`.
5. The text: every version or group name used in `sections/`, `main.tex` and `.github/tex/layout.tex`
   (`\onlyin`, `\exceptin`, `\ifversion`, `\begin{arxiv}`) must still be declared. Rename or remove the rest.
6. Check. On a laptop: `make -f .github/Makefile` prints one row per PDF; each must say `ok`, with 0 undefined references and
   pages within the limit (`OVER` means too long). Without a laptop: give the user the changed files, and on
   Overleaf open each file in `versions/` and press Recompile (Overleaf compiles the open entry file).

| Template | documentclass line |
|---|---|
| IEEE conference | `documentclass[conference]{IEEEtran}` |
| IEEE journal (TAC and other Transactions) | `documentclass[journal]{IEEEtran}` |
| IEEE CDC and ACC | `documentclass[letterpaper,10pt,conference]{ieeeconf}` (`ieeeconf.cls` is in `.github/tex/`) |
| Elsevier | `documentclass{elsarticle}` |
| Springer LNCS | `documentclass{llncs}` |
| ACM (HSCC, ICCPS) | `documentclass[sigconf]{acmart}` |
| arXiv, one column | `documentclass[11pt]{article}` and `\usepackage[a4paper,margin=1in]{geometry}` |

Each class line starts with a backslash. This file leaves it out, because Overleaf tries to compile an open
file that contains a class line, and a Markdown file would then break Recompile.

Another class: copy a file in `versions/`, change its documentclass line, and add a branch for the class in
`.github/tex/layout.tex` if the title block looks wrong.

## Figures

One Python file per figure, `figures/src/<name>.py`, drawn for its slot. Copy this one
(`figures/src/example.py` in the template):

```python
from pathlib import Path
import numpy as np
ASPECT = 0.62                                   # height / width when the slot gives none
DATA = Path(__file__).resolve().parents[2] / "figures/data/example.csv"   # written by figures/src/simulate.py

def plot(fig, ax, s):                           # s holds the sizes and styles for this slot
    d = np.genfromtxt(DATA, delimiter=",", names=True)
    ax.plot(d["t"], d["method_a"], **s.style("Method A", markevery=(1, 5)))
    ax.plot(d["t"], d["method_b"], **s.style("Method B", markevery=(3, 5)))
    ax.axhline(1, **s.style("Reference", lw=s.lw_ref, marker="None"))
    ax.set(xlabel=r"Time $t$ (s)", ylabel=r"Output $y$ (-)")
    s.legend(ax, loc="lower right")             # inside the axes, in an empty corner
```

- The numbers come from `figures/data/`, written by the experiment code in `figures/src/`. Name the data file in the figure file
  as a string (`"figures/data/example.csv"`), and `make -f .github/Makefile` redraws the figure whenever that file changes.
- `s.style(name)` gives the colour, line style, marker and label of `name` from `METHODS` in
  `figures/src/methods.py`. A new method name goes there first.
- Label every axis with a quantity and a unit. With dense data, `markevery` keeps the markers apart.
- Slot sizes: `s.W`, `s.H` (pt), `s.F` (body text size).
- In LaTeX: `\autofig{<name>}`. Then run `make -f .github/Makefile` and commit `figures/auto/*.pdf` and `*.json`.

## Commands

| Need | Write |
|---|---|
| declare a version | `\DeclareVersion[OliveGreen]{arxiv}` in `setup.tex` (the colour is for the review copy) |
| one name for several | `\DeclareVersionGroup{long}{journal,arxiv}` |
| text in some versions | `\onlyin{arxiv}{ All proofs are in the appendix.}` |
| a list or a group | `\onlyin{journal,arxiv}{...}`, `\onlyin{long}{ and~\cite{ogata2010}}` |
| this or that | `We use a \ifversion{conference}{PI controller}{PI controller with anti-windup}.` |
| all but some | `\exceptin{conference}{We also tested a second motor.}` |
| a block in one version | `\begin{arxiv}` and `\end{arxiv}`, each on its own line, around paragraphs, figures or a section |
| a block in a group | `\ifversion{long}{\input{sections/related}}{}` (groups have no environment) |
| the version name as text | `\thisversion` |
| a label only arXiv has | `The proof is in \arxivref{app:proofs}.` prints "Appendix A" in arXiv and "Appendix A of [5]" elsewhere |
| point to the long version | `\onlyin{conference}{A long version with all proofs is on arXiv~\cite{arxiv}.}` |
| declare an editor | `\DeclareEditor{anna}{AK}` and `\editorname{anna}{Anna Keller}` in `setup.tex` |
| accept one person's edits | `\acceptedits{anna}` in `setup.tex`; `\showedits{anna}` undoes it |
| added text | `\added{ai}{with input limits}` |
| deleted text | `\deleted{ai}{very }` |
| replaced text | `\replaced{ai}{settles}{converges}` (new first, then old) |
| a note | `\authnote{ai}{add a reference}` |
| a whole paragraph or figure | `\begin{addedblock}{ai}` ... `\end{addedblock}`, or `deletedblock` |
| a figure | `\autofig{step}`, or `\autofig[aspect=0.5]{step}`, `\autofig[height=4cm]{step}` |
| a wrapped figure | `\begin{wrapfigure}{r}{0.45\linewidth}\centering \autofig{bars}\end{wrapfigure}` |

The review copy shows each version in its colour, and both sides of `\ifversion` with a grey bar between them.
The PDFs you send accept every edit.

## Make it fit

Every trick sits inside a conference command, so the journal and arXiv versions keep normal spacing.

| Trick | Write |
|---|---|
| less space under a figure | `\onlyin{conference}{\vspace{-2mm}}` after the `\label` in the figure |
| smaller gap around floats | `\ifversion{conference}{\setlength{\textfloatsep}{6pt}}{}` in `setup.tex` |
| narrower table | `\ifversion{conference}{\setlength{\tabcolsep}{3pt}}{}` before `\begin{tabular}` |
| shorter caption | `\caption{Speed after a step\onlyin{long}{ of the reference, for all three controllers}.}` |
| one line less | `\onlyin{conference}{\looseness=-1}` at the end of the paragraph |
| proof moved out | `\begin{arxiv}` around the proof and `\arxivref{...}` where it was |
| smaller figure | a smaller aspect in `setup.tex`: `\ifversion{conference}{\newcommand{\stepaspect}{0.5}}{\newcommand{\stepaspect}{0.62}}`, then `\autofig[aspect=\stepaspect]{step}` |

## Rules

1. Mark every change with the editor key `ai`: `\added{ai}{..}`, `\deleted{ai}{..}`, `\replaced{ai}{new}{old}`.
   Leave text unmarked only in the first-chat setup or when the user says so.
2. Never scale a figure. No `\includegraphics[width=...]`, no `\resizebox`, no `scale`. Use `\autofig`
   and change the slot (column, `aspect`, `height`, wrap width); the figure is drawn again for it.
3. Keep fit tricks inside `\onlyin{conference}{..}` or `\ifversion{conference}{..}{}`.
4. Use only version, group and editor names that `setup.tex` declares. If you do not know them, ask, or use
   the template names above and say so.
5. `\deleted` and the old text of `\replaced` stay inside one paragraph. Put `\cite`, `\ref` and maths inside
   them in braces: `\deleted{ai}{see {\cite{x}}}`.
6. Never put two `\autofig` of one figure in the two sides of `\ifversion`; set a size per version instead.
7. Do not touch another editor's marks unless asked.
8. Never scale or edit a file in `figures/auto/`; change `figures/src/<name>.py` and run `make -f .github/Makefile`.
9. Never force-push. Push only when asked. Work to review goes on a topic branch with a pull request.
10. Answer with the lines to paste and the file they go in. Keep it short.

## Example requests

**"Add a sentence that only the arXiv version prints: the code is on GitHub."**
In `sections/conclusion.tex`: `\onlyin{arxiv}{\added{ai}{The code is on GitHub.}}`

**"The sentence says PI controller. Make it PI in the conference version and PI with anti-windup elsewhere."**
`We use a \replaced{ai}{\ifversion{conference}{PI}{PI with anti-windup}}{PI controller}.`

**"Cite Ogata only in the journal and arXiv versions."**
`as in~\cite{franklin2019}\onlyin{long}{\added{ai}{ and~\cite{ogata2010}}}.`
Each bibliography lists only what its version cites.

**"Move the proof to the arXiv appendix and refer to it in the conference paper."**
Move it to `sections/appendix_proofs.tex`, which `main.tex` reads inside `\begin{arxiv}` ... `\end{arxiv}`.
Or, in place, around the proof: `\begin{arxiv}` and `\end{arxiv}`, each on its own line.
Where it was: `\added{ai}{The proof is in \arxivref{app:proofs}.}`

**"Make the step figure smaller in the conference version only."**
In `setup.tex`: `\ifversion{conference}{\newcommand{\stepaspect}{0.5}}{\newcommand{\stepaspect}{0.62}}`.
In the figure: `\autofig[aspect=\stepaspect]{step}`. Never `width=0.8\linewidth`.

**"We are three lines over the page limit."**
Conference only: `\onlyin{conference}{\vspace{-2mm}}` under a figure,
`\ifversion{conference}{\setlength{\textfloatsep}{6pt}}{}` in `setup.tex`, and
`\onlyin{conference}{\looseness=-1}` at the end of a paragraph with a short last line.

**"Delete the sentence about PID and replace converges with settles."**
`\deleted{ai}{We also tried a PID controller. }` and `\replaced{ai}{settles}{converges}`.

**"Add a figure of the voltage that only the long versions have."**
```latex
\onlyin{long}{
\begin{addedblock}{ai}
\begin{figure}[!tb]
  \centering
  \autofig{voltage}
  \caption{Voltage after a reference step.}
  \label{fig:voltage}
\end{figure}
\end{addedblock}
}
```
Draw it in `figures/src/voltage.py` (copy the figure file above). References to it go inside `\onlyin{long}{...}`.
