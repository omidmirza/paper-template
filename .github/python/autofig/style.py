"""Style: the sizes from the figure rules (.github/docs/FIGURE_RULES.md) for a slot of width W, height H, body size F.

Use in a spec:  ax.plot(t, e, **s.style("Ours", lw=s.lw_noisy)); s.legend(ax)
The engine builds the Style from the LaTeX slot (W, H, F in TeX pt, family serif|sans, compact)
and applies s.rc while the figure is drawn. RawStyle applies no rule (matplotlib defaults, for autofig raw).
"""
from __future__ import annotations

from cycler import cycler

STYLE_VERSION = "v8-paperkit-1"   # bump when sizes below change: every figure is then remade
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
LINESTYLES = ["-", "--", "-.", ":", (0, (5, 1, 1, 1)), (0, (1, 1)), (0, (8, 2))]
MARKERS = ["o", "s", "^", "D", "v", "P", "X"]
MIN_TEXT = 10.0          # rule 3: never under 10 pt, never under the body size
COMPACT_BELOW = 200.0    # slots narrower than this (TeX pt) use the body size for all text
PT_PER_IN = 72.27        # TeX points per inch (LaTeX reports \linewidth in these)


class Style:
    """Sizes and per-method styles for one slot. All sizes are TeX pt (= matplotlib usetex pt)."""
    raw = False

    def __init__(self, w, h=0.0, f=10.0, family="serif", compact=None, methods=None):
        self.W, self.H, self.F_body = float(w), float(h or 0), float(f)
        self.F = max(self.F_body, MIN_TEXT)
        self.family = family if family in ("serif", "sans") else "serif"
        self.compact = bool(compact) or self.W < COMPACT_BELOW
        up = 0 if self.compact else 1
        self.fs_label = self.fs_title = self.F + 2 * up
        self.fs_tick = self.fs_legend = self.F + up
        self.lw, self.lw_noisy, self.lw_ref, self.lw_spine = 2.5, 1.5, 1.8, 1.2
        self.ms, self.ms_curve, self.mew = 3.5, 3.0, 0.5
        self.methods = dict(methods or {})

    def style(self, method, **over):
        """dict(color, ls, marker, ...) of a registered method; keyword overrides win."""
        if method not in self.methods:
            raise ValueError(f"method {method!r} is not in figures/src/methods.py METHODS "
                           f"(known: {', '.join(self.methods) or 'none'})")
        spec = self.methods[method]
        if isinstance(spec, int):   # METHODS = {"Ours": 0, ...}: index into the default tables
            spec = dict(color=OKABE_ITO[spec % 7], ls=LINESTYLES[spec % 7], marker=MARKERS[spec % 7])
        d = dict(label=method, lw=self.lw, ms=self.ms_curve, mew=self.mew)
        d.update(color=spec["color"], ls=spec.get("ls", "-"), marker=spec.get("marker") or "None")
        d["mec"] = d["color"]
        d.update(over)
        return d

    def legend(self, ax, **kw):
        """Legend inside the axes in the emptiest region (rule 5)."""
        return ax.legend(**{"loc": "best", "framealpha": 0.9, **kw})

    @property
    def rc(self):
        """matplotlib rcParams for this slot."""
        F = self.F
        pre = r"\usepackage{amsmath}\usepackage{amssymb}\usepackage{bm}"
        rc = {
            "text.usetex": True, "pdf.fonttype": 42, "font.size": F,
            "axes.labelsize": self.fs_label, "axes.titlesize": self.fs_title,
            "xtick.labelsize": self.fs_tick, "ytick.labelsize": self.fs_tick,
            "legend.fontsize": self.fs_legend, "legend.title_fontsize": self.fs_legend,
            "lines.linewidth": self.lw, "lines.markersize": self.ms, "lines.markeredgewidth": self.mew,
            "patch.linewidth": 1.2, "hatch.linewidth": 1.0, "errorbar.capsize": 3,
            "axes.linewidth": self.lw_spine, "axes.grid": True, "axes.axisbelow": True,
            "axes.labelpad": 2, "grid.linewidth": 0.6, "grid.alpha": 0.35,
            "xtick.major.width": 1.2, "ytick.major.width": 1.2, "xtick.minor.width": 0.8,
            "ytick.minor.width": 0.8, "xtick.major.size": 3.5, "ytick.major.size": 3.5,
            "xtick.direction": "in", "ytick.direction": "in", "xtick.major.pad": 2.5, "ytick.major.pad": 2.5,
            "legend.frameon": True, "legend.framealpha": 0.9, "legend.edgecolor": "0.6",
            "legend.borderpad": 0.3, "legend.labelspacing": 0.25, "legend.handlelength": 1.8,
            "legend.handletextpad": 0.4, "legend.columnspacing": 0.9, "legend.borderaxespad": 0.3,
            "legend.loc": "best", "axes.prop_cycle": cycler(color=OKABE_ITO),
            "figure.constrained_layout.use": True, "figure.constrained_layout.h_pad": 0.01,
            "figure.constrained_layout.w_pad": 0.01, "figure.constrained_layout.hspace": 0.01,
            "figure.constrained_layout.wspace": 0.01,
            "savefig.bbox": "tight", "savefig.pad_inches": 0, "savefig.format": "pdf",
        }
        if self.family == "sans":   # Helvetica text + sans math: matches Arial/Helvetica slide text
            rc.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica"],
                       "text.latex.preamble": pre + r"\usepackage[helvet]{sfmath}"})
        else:                       # Computer Modern, like the paper body
            rc.update({"font.family": "serif", "font.serif": ["Computer Modern Roman"],
                       "text.latex.preamble": pre})
        return rc


class RawStyle(Style):
    """matplotlib defaults, for the before/after comparison: every size is None (the default) and style() sets only the label."""
    raw = True

    def __init__(self, methods=None):
        super().__init__(w=6.4 * 72, f=10, methods=methods)
        for k in ("fs_label", "fs_title", "fs_tick", "fs_legend", "lw", "lw_noisy", "lw_ref", "lw_spine",
                  "ms", "ms_curve", "mew"):
            setattr(self, k, None)

    def style(self, method, **over):
        d = {"label": method}
        d.update({k: v for k, v in over.items() if v is not None})
        return d

    def legend(self, ax, **kw):
        return ax.legend()

    @property
    def rc(self):
        return {}
