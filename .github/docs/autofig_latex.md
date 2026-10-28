# Figure slots in LaTeX

`\autofig{<name>}` includes the figure that `figures/src/<name>.py` draws, as wide as the line where `\autofig` stands. That space is the figure's slot.
The package is `.github/tex/autofig.sty`.

## Examples

```latex
\begin{figure}[t]\centering \autofig{example} \caption{...}\end{figure}
\begin{figure*}[t]\centering \autofig[aspect=0.38]{response} \end{figure*}
\begin{wrapfigure}{r}{0.45\linewidth}\centering \autofig{bars} \end{wrapfigure}
```

| Option | Effect |
|---|---|
| `height=4cm` | fixed height |
| `aspect=0.5` | height is half the width (default: `ASPECT` in the figure file) |
| `font=11pt` | base size 11 pt: axis labels 13 pt, ticks and legend 12 pt (default: the body size) |
| `compact` | all text at the body size (always so in slots under 200 pt wide) |

## Rules

- The figure is as wide as the line where `\autofig` stands.
- In a table, use a `p{}` column. `c`, `l` and `r` columns have no width.
- Never scale an `\autofig`. Change the slot and build again.
- Figure names and folder names must not contain spaces.

## Build steps

1. LaTeX writes the size of each slot to `.github/build/<entry>/<entry>.afg`.
2. Python draws each figure at that size in `figures/auto/`.
3. LaTeX runs again and includes the figures.

`make -f .github/Makefile` runs all three steps.
File names give the sizes in tenths of a point: `example_w2520_f100.pdf` is 252 pt wide, with 10 pt text.

## Red frames

A figure that is not yet drawn for its slot gets a red frame.

| Figure file | Draft (default) | `\usepackage[final]{autofig}` |
|---|---|---|
| drawn only for other sizes | `<name>.pdf` (the widest one), scaled, framed "stale" | `<name>.pdf`, scaled |
| more than 1 pt too wide or too narrow | framed "size mismatch" | the figure |
| none | a red "missing" box | a red "missing" box |

Build the figures before you send a PDF. After `make -f .github/Makefile` no red frame is left.
