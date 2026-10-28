"""FIGURE RULES checks: on the matplotlib Figure before saving, and on a finished figure PDF.

CLI: python -m autofig check figures/auto/*.pdf [--body 10]   (expected W/H/F come from <pdf>.json)
check_figure(fig, s) returns a list of problems (empty = passes); check_pdf(pdf, ...) returns (problems, info).
Sub/superscripts are judged like body scripts: >= 0.69 F (LaTeX sets scripts at 0.7 of the text size).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import matplotlib as mpl
import numpy as np

BP = 72.27 / 72      # TeX pt per PDF point
TOL = 0.05           # pt tolerance on sizes
SCRIPT = 0.69        # scripts may be this fraction of the body size
MIN_DATA_LINE = 1.5


# ---------- matplotlib Figure ----------
def _series(ax):
    """Labeled data series of an axes (lines, collections, bar containers)."""
    items = list(ax.get_lines()) + list(ax.collections) + list(ax.containers)
    return [a for a in items if a.get_label() and not a.get_label().startswith("_")]


def _legend_covers(fig, leg):
    """Number of data points (vertices + segment samples) of the legend's axes inside the legend box."""
    ax = leg.axes
    box = leg.get_window_extent().padded(-1)
    n = 0
    for line in ax.get_lines():
        if not line.get_visible() or len(line.get_xdata()) == 0:
            continue
        xy = line.get_transform().transform(line.get_xydata())
        if len(xy) < 400:          # sparse curve: sample the segments too
            t = np.linspace(0, 1, 12)[:, None, None]
            xy = (xy[:-1] * (1 - t) + xy[1:] * t).reshape(-1, 2) if len(xy) > 1 else xy
        n += int(sum(box.contains(x, y) for x, y in xy))
    for p in ax.patches:
        if p.get_visible() and box.overlaps(p.get_window_extent().padded(-1)):
            n += 1
    return n


def check_figure(fig, s) -> list[str]:
    fig.draw_without_rendering()
    probs = []
    if fig._suptitle is not None and fig._suptitle.get_text().strip():
        probs.append("figure-wide suptitle (put the title in the LaTeX caption)")
    for t in fig.findobj(mpl.text.Text):
        if t.get_visible() and t.get_text().strip() and t.get_fontsize() < s.F - TOL:
            probs.append(f"text {t.get_text()[:30]!r} is {t.get_fontsize():.1f} pt < {s.F:g} pt (rule 3)")
    legend_labels = {t.get_text() for leg in [a.get_legend() for a in fig.axes] + list(fig.legends)
                     if leg is not None for t in leg.get_texts()}
    for ax in fig.axes:
        if not ax.get_visible() or not ax.axison:
            continue
        if ax.images:
            probs.append("axes contains a raster image (imshow); rule 6 needs vector content")
        if not hasattr(ax, "_colorbar"):
            for xy, lab in (("x", ax.get_xlabel()), ("y", ax.get_ylabel())):
                shared = getattr(ax, f"get_shared_{xy}_axes")().get_siblings(ax)
                if not lab.strip() and not any(getattr(o, f"get_{xy}label")().strip() for o in shared if o is not ax):
                    probs.append(f"axes {ax.get_title() or fig.axes.index(ax)}: no {xy} label (rule 5)")
        for line in ax.get_lines():
            if (len(line.get_xdata()) > 2 and line.get_linestyle() not in ("None", "none", "")
                    and line.get_linewidth() < MIN_DATA_LINE - 1e-6):
                probs.append(f"line {line.get_label()!r} is {line.get_linewidth():.2f} pt < 1.5 pt (rule 4)")
        labeled = {a.get_label() for a in _series(ax)}
        if len(labeled) > 1 and not labeled <= legend_labels:
            probs.append(f"axes {fig.axes.index(ax)} has {len(labeled)} series but no legend for "
                         f"{sorted(labeled - legend_labels)} (rule 5)")
        leg = ax.get_legend()
        if leg is not None:
            lb, ab = leg.get_window_extent(), ax.get_window_extent()
            if lb.x0 < ab.x0 - 1 or lb.y0 < ab.y0 - 1 or lb.x1 > ab.x1 + 1 or lb.y1 > ab.y1 + 1:
                probs.append(f"legend of axes {fig.axes.index(ax)} sticks out of the axes (rule 5)")
            n = _legend_covers(fig, leg)
            if n:
                probs.append(f"legend of axes {fig.axes.index(ax)} covers {n} data point(s) (rule 5)")
    raster = sorted({type(a).__name__ for a in fig.findobj() if getattr(a, "get_rasterized", None)
                     and a.get_rasterized()})
    if raster:
        probs.append(f"rasterized artists {raster} (rule 6)")
    return probs


# ---------- PDF ----------
def text_sizes(page, rect=None):
    """(min base size, min script size) in TeX pt of the text spans on a pymupdf page (inside rect)."""
    base, script = [], []
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            spans = [sp for sp in line["spans"] if sp["text"].strip()]
            if rect is not None:
                spans = [sp for sp in spans if _center_in(sp["bbox"], rect)]
            if not spans:
                continue
            top = max(sp["size"] for sp in spans)
            for sp in spans:
                (script if sp["size"] < 0.85 * top else base).append(sp["size"] * BP)
    return (min(base) if base else None), (min(script) if script else None)


def _polyline_len(items):
    """Longest run of connected straight segments (a data curve; hatch/grid strokes are disconnected)."""
    best = run = 0
    prev = None
    for it in items:
        if it[0] == "l" and prev is not None and abs(it[1].x - prev.x) + abs(it[1].y - prev.y) < 1e-3:
            run += 1
        else:
            run = 1 if it[0] == "l" else 0
        best, prev = max(best, run), (it[2] if it[0] == "l" else None)
    return best


def _center_in(bb, r):
    x, y = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    return r[0] - 0.5 <= x <= r[2] + 0.5 and r[1] - 0.5 <= y <= r[3] + 0.5


def ink_bbox(pdf: Path):
    """Ink bounding box (x0, y0, x1, y1) in PDF points (origin bottom left) from Ghostscript's bbox device."""
    gs = shutil.which("gs")
    if gs is None:
        return None
    err = subprocess.run([gs, "-q", "-dBATCH", "-dNOPAUSE", "-sDEVICE=bbox", str(pdf)],
                         capture_output=True, text=True).stderr
    m = re.search(r"%%HiResBoundingBox:\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)", err)
    return tuple(map(float, m.groups())) if m else None


def margins_pt(pdf: Path):
    """White margins (left, bottom, right, top) in TeX pt between the page box and the ink."""
    import pymupdf
    ink = ink_bbox(pdf)
    if ink is None:
        return None
    with pymupdf.open(pdf) as d:
        W, H = d[0].rect.width, d[0].rect.height
    x0, y0, x1, y1 = ink
    return [round(v * BP, 2) for v in (x0, y0, W - x1, H - y1)]


def check_pdf(pdf, w=None, h=None, f=10.0, margin_limit=0.3) -> tuple[list[str], dict]:
    """Rule checks on a figure PDF. w/h/f in TeX pt (h=None: height not checked)."""
    import pymupdf
    pdf, probs = Path(pdf), []
    with pymupdf.open(pdf) as doc:
        if doc.page_count != 1:
            probs.append(f"{doc.page_count} pages (a figure PDF has 1)")
        page = doc[0]
        W, H = page.rect.width * BP, page.rect.height * BP
        if page.get_images():
            probs.append(f"{len(page.get_images())} raster image(s) inside (rule 6)")
        bad = [x[3] for x in page.get_fonts() if x[1] in ("n/a", "") and x[2] != "Type3"]
        if bad:
            probs.append(f"fonts not embedded: {bad} (rule 6)")
        base, script = text_sizes(page)
        F = max(f, 10.0)
        if base is not None and base < F - TOL:
            probs.append(f"smallest text {base:.2f} pt < {F:g} pt (rule 3)")
        if script is not None and script < SCRIPT * F - TOL:
            probs.append(f"smallest sub/superscript {script:.2f} pt < {SCRIPT * F:.2f} pt (rule 3)")
        thin = [d["width"] for d in page.get_drawings() if d.get("width") and d.get("color") is not None
                and d["width"] < MIN_DATA_LINE - TOL and _polyline_len(d["items"]) >= 8]
        if thin:
            probs.append(f"{len(thin)} data line(s) thinner than 1.5 pt (min {min(thin):.2f}) (rule 4)")
    if w is not None and abs(W - w) > 0.5:
        probs.append(f"width {W:.2f} pt != slot {w:.2f} pt (rule 1)")
    if h and abs(H - h) > 0.5:
        probs.append(f"height {H:.2f} pt != slot {h:.2f} pt (rule 1)")
    m = margins_pt(pdf)
    if m is not None and max(m) > margin_limit:
        probs.append(f"white margin (l, b, r, t) {m} pt > {margin_limit:g} pt (rule 6)")
    info = dict(width=round(W, 2), height=round(H, 2), min_text=base and round(base, 2),
                min_script=script and round(script, 2), margins=m)
    return probs, info


def main(args) -> int:
    bad = 0
    for p in args.pdfs:
        p = Path(p)
        meta = p.with_suffix(".json")
        req = json.loads(meta.read_text())["request"] if meta.exists() else {}
        w = args.width if args.width is not None else req.get("w")
        probs, info = check_pdf(p, w=w, h=req.get("h") or None, f=args.body or req.get("f", 10.0))
        txt = f"{info['width']:.2f}x{info['height']:.2f} pt, text >= {info['min_text']} pt"
        print(f"{'ok  ' if not probs else 'FAIL'} {p} ({txt})")
        for q in probs:
            print(f"     - {q}")
        bad += bool(probs)
    return 1 if bad else 0
