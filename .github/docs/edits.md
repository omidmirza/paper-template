# Edits

The review copy shows each co-author's changes in their colour. In the submitted PDFs every change is accepted.
Section 8 of [toggle_helper.tex](../../toggle_helper.tex) shows every command with an example. The package is `.github/tex/editmarks.sty`.

## Set up

In `setup.tex`, one line per person:

```latex
\usepackage[dvipsnames]{xcolor}         % load xcolor first
\usepackage{editmarks}
\DeclareEditor{anna}{AK}                % key and initials
\DeclareEditor[Violet]{ben}{BO}         % with a colour of your choice
\editorname{anna}{Anna Keller}          % full name for the legend
```

## Mark edits

| Command | Review copy | Submitted PDF |
|---|---|---|
| `\added{anna}{new text}` | the text in Anna's colour, tagged `AK` | the text |
| `\deleted{ben}{old text}` | the text struck out | nothing |
| `\replaced{ben}{new}{old}` | the new text, then the old one struck out | the new text |
| `\authnote{anna}{add a reference}` | `[AK: add a reference]` | nothing |
| `\begin{addedblock}{anna}` ... `\end{addedblock}` | the block in colour | the block |
| `\begin{deletedblock}{ben}` ... `\end{deletedblock}` | the block between two marker lines | nothing |
| `\TODO{repeat with ten seeds}` | a note in a red frame | nothing, and a warning in the log |
| `\pending{0.4~ms}` | pink text | pink text, and a warning in the log |

A block may contain paragraphs, equations and figures.

## Accept edits

| Command | Effect |
|---|---|
| `\acceptedits{ben}` | accepts Ben's edits from this point on |
| `\showedits{ben}` | shows them again |
| `\acceptalledits` | accepts everyone's edits |

`\editlegend` and `\editsummary` (both in `main.tex`) print each person's colour and number of edits, in the review copy only.

## Review copy and submitted PDFs

`versions/review.tex` shows every edit. The other files in `versions/` accept them.
Before you submit, look for a `\TODO` or `\pending` left in the text:

```sh
grep -E "TODO left|Pending result" .github/build/*/*.log
```

## Known problems

| Problem | Fix |
|---|---|
| `\deleted` cannot span paragraphs | use `deletedblock` |
| `\cite`, `\ref` or math in `\deleted` | put it in braces: `\deleted{ben}{see {\cite{x}}}` |
| the `changes` package is loaded too | remove it: it defines `\added` and `\deleted` as well |
