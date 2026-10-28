# figures/static

Images that are not drawn from data, such as diagrams and photos. Save them as PDF or PNG at their printed size.

```latex
\includegraphics{figures/static/<name>}
```

Figures drawn from data have their code in `figures/src/`, one Python file per figure. `make -f .github/Makefile` draws them into `figures/auto/`.
