"""Draw a spec with matplotlib defaults (6.4 x 4.8 in, DejaVu Sans, no usetex, no figure rules).

CLI: python -m autofig raw [<name> ...] [--specs figures/src] [--out figures/raw]
\\rawfig scales the result to \\linewidth, as most papers do; next to \\autofig it shows how small the text gets.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402

from .engine import load_methods, load_module  # noqa: E402
from .style import RawStyle  # noqa: E402


def spec_names(specs: Path) -> list[str]:
    """Every figures/src/*.py that defines plot() (methods.py and _helpers are skipped)."""
    return [p.stem for p in sorted(Path(specs).glob("*.py"))
            if p.stem != "methods" and not p.stem.startswith("_") and "def plot(" in p.read_text()]


def make_raw(name: str, specs="figures/src", out="figures/raw") -> Path:
    specs = Path(specs)
    mod = load_module(specs / f"{name}.py")
    rows, cols = getattr(mod, "PANELS", (1, 1))
    pdf = Path(out) / f"{name}.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context():
        plt.rcdefaults()                       # matplotlib defaults, nothing from the rules
        fig, ax = plt.subplots(rows, cols, **dict(getattr(mod, "SUBPLOTS", {})))
        try:
            mod.plot(fig, ax, RawStyle(load_methods(specs)))
            fig.savefig(pdf)
        finally:
            plt.close(fig)
    return pdf


def main(args) -> int:
    names = args.names or spec_names(args.specs)
    for n in names:
        print(f"raw  {make_raw(n, args.specs, args.out)}")
    return 0
