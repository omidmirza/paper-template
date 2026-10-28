"""autofig: draw each figure at the size of its LaTeX slot, by the rules in .github/docs/FIGURE_RULES.md.

Run from the paper root:  python -m autofig {make,raw,check,audit,watch} --help
Each figure has a spec, figures/src/<name>.py, with ASPECT, PANELS and plot(fig, ax, s); see .github/docs/figures.md.
"""
from .style import STYLE_VERSION, Style, RawStyle  # noqa: F401

__version__ = "1.0"
