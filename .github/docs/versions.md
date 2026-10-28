# Versions

The conference, journal and arXiv PDFs are built from one source.
[toggle_helper.tex](../../toggle_helper.tex) shows every command with an example. The package is `.github/tex/versiontoggle.sty`.

## Set up

Declare each version with one line in `setup.tex`. The names are up to you.

```latex
\usepackage[dvipsnames]{xcolor}                          % load xcolor first
\usepackage[version=conference, overleaf=review]{versiontoggle}
\DeclareVersion{conference}
\DeclareVersion[magenta]{journal}                        % colour in the review copy, optional
\DeclareVersion{arxiv}
\DeclareVersionGroup{long}{journal,arxiv}                % one name for several versions
```

## Mark text

| Text | Command |
|---|---|
| in some versions only | `\onlyin{arxiv}{...}`, `\onlyin{journal,arxiv}{...}` or `\onlyin{long}{...}` |
| in all versions but one | `\exceptin{arxiv}{...}` |
| two wordings | `\ifversion{conference}{short}{long}` |
| a paragraph, figure or proof | `\begin{arxiv}` ... `\end{arxiv}`, each on its own line |
| a block for a group | `\ifversion{long}{...}{}` (a group has no environment) |
| a whole file | `\ifversion{long}{\input{sections/appendix_proofs}}{}` |
| the version name | `\thisversion` |

Set a figure size per version in `setup.tex`. The review copy then draws the figure once:

```latex
\ifversion{conference}{\newcommand{\stepaspect}{0.5}}{\newcommand{\stepaspect}{0.62}}   % setup.tex
\autofig[aspect=\stepaspect]{example}                                                   % the text
```

## Cross-references

Each version numbers its own figures and sections, with no gaps.

| Reference | Command |
|---|---|
| to text that only arXiv has | `\arxivref{app:proofs}`: "Appendix A" in arXiv, "Appendix A of [5]" elsewhere |
| in a caption with two wordings | `\caption{\ifversion{conference}{short}{long}}`, then one `\label` |

[5] is the `arxiv` entry in `refs/references.bib`. The wording is set in `.github/tex/layout.tex`.
Commit `refs/extended_labels.tex` after a build, so Overleaf prints the same appendix letters.
A `\ref` to a label that a version lacks prints `??`.
`make -f .github/Makefile` prints a table that counts it under undefined references.

## Fit the page limit

Put each change inside `\onlyin{conference}{...}` or `\ifversion{conference}{...}{}`, so the other versions keep the normal spacing.

| Change | Command |
|---|---|
| less space under a figure | `\onlyin{conference}{\vspace{-4pt}}` after its `\label` |
| less space around floats | `\ifversion{conference}{\setlength{\textfloatsep}{6pt plus 2pt minus 2pt}}{}` in `setup.tex` |
| a narrower table | `\onlyin{conference}{\setlength{\tabcolsep}{3pt}}` before `\begin{tabular}` |
| one line fewer | `\onlyin{conference}{\looseness=-1}` inside the paragraph |

Never shrink a figure with `scale` or `width`. Give it a smaller `aspect` or `height`.
To list these changes: `grep -n "onlyin{conference}\|ifversion{conference}" setup.tex sections/*.tex`

## Build

Each PDF has its own file in `versions/`. The `\documentclass` line of that file sets the template.

| File | Template | Version |
|---|---|---|
| `review.tex` | IEEE (`IEEEtran`) | all, edits in colour |
| `conference.tex` | IEEE (`IEEEtran`) | conference |
| `cdc.tex` | IEEE CDC, ACC (`ieeeconf`) | conference |
| `acm.tex` | ACM (`acmart`) | conference |
| `springer.tex` | Springer LNCS (`llncs`) | conference |
| `journal.tex` | Elsevier (`elsarticle`) | journal |
| `tac.tex` | IEEE Transactions (`IEEEtran`) | journal |
| `arxiv.tex` | one column (`article`) | arXiv |

On Overleaf, open a file in `versions/` and press Recompile.
On a laptop, `make -f .github/Makefile` builds all of them.
For another template, copy a file and change its `\documentclass` line.

The line `% page limit: 6` (or `none`) near the top of each file sets the limit that the build checks.

## Review copy

`versions/review.tex` (and `main.tex` on its own on Overleaf) prints each version's text in that version's colour.
Text shared by several versions is dark blue. Both sides of `\ifversion` appear, with a grey bar between them.

## More versions

Most of these start as a copy of a file in `versions/`.

| Version | Change |
|---|---|
| anonymous | `\def\paperanonymous{}` before `\input{main}`, plus the lines below |
| with edits marked | remove the `\PassOptionsToPackage{final}{editmarks}` line |
| thesis chapter | copy `versions/arxiv.tex`; in the copy, class `report` and `\def\paperversion{thesis}`; in `setup.tex`, `\DeclareVersion{thesis}` and add it to `long` |
| rebuttal | at submission: `make -f .github/Makefile release TAG=conference-submitted`; later: `make -f .github/Makefile diff OLD=conference-submitted ENTRY=versions/conference.tex` |
| supplement (the appendix as its own PDF) | copy `versions/arxiv.tex` to `versions/supplement.tex`; build with `PAPERKIT_EXTENDED=supplement make -f .github/Makefile`, so the other versions take their appendix numbers from it |

For the anonymous version, add to `setup.tex` after the title lines:

```latex
\ifdefined\paperanonymous \renewcommand{\paperauthors}{Anonymous authors}\renewcommand{\paperaffiliation}{}\fi
\newcommand{\selfcite}[1]{\ifdefined\paperanonymous [anonymized]\else\cite{#1}\fi}
```

Cite your own papers with `\selfcite{key}`. Put the acknowledgement inside `\ifdefined\paperanonymous\else ... \fi`.

## Errors

| Message or symptom | Cause |
|---|---|
| `Unknown version 'arxv'` | a misspelled or undeclared name |
| `No version selected` | no `version=` and no `\paperversion` |
| `... is already a version` | a group and a version have the same name |
| the figure appears twice in the review copy | an `\autofig` on each side of `\ifversion`; set the size in `setup.tex` instead |
