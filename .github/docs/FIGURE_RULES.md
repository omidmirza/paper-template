# Figure rules

`make -f .github/Makefile` checks most of these rules and stops when a figure breaks one.

| # | Rule |
|---|---|
| 1 | Draw the figure at its printed size, usually one column wide. Never shrink it in LaTeX. |
| 2 | LaTeX sets all text, with the paper's notation. |
| 3 | No text smaller than the body text or 10 pt. With a 10 pt body: axis labels 12 pt, ticks and legend 11 pt. A compact figure may set all text at the body size. |
| 4 | Line widths: curves 2.5 pt, noisy series 1.5 pt, reference lines 1.8 pt. Markers 3 to 3.5 pt. |
| 5 | Every axis label gives a quantity and a unit. A plot with several series has a legend inside the axes that covers no data. |
| 6 | Vector PDF with embedded fonts, no white border and no pixel images inside. |
| 7 | Each method has the same colour-blind-safe colour in every figure, plus its own line style or marker. |
| 8 | Look at the figure in the compiled paper before you send it. |

## More rules

- Separate close points by the axis range or the marker shape. Do not enlarge the markers.
- Write tick labels as 0.1 and 1, not as powers of ten: the exponents print below 10 pt.
- Share axes and keep the gaps between panels small.
- A new figure is about as tall as the one it replaces.
- A zoomed axis range is allowed when every event of interest lies inside it. Say so in the caption.

## Check

```sh
PYTHONPATH=.github/python .github/.venv/bin/python -m autofig check figures/auto/*.pdf
PYTHONPATH=.github/python .github/.venv/bin/python -m autofig audit .github/pdf/conference.pdf
```

`check` tests figure PDFs against the rules.
`audit` finds the smallest text in each figure of a compiled paper and compares it with the body text.
