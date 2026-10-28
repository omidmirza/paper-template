"""Draw each requested figure at its slot size: load the spec, draw it with Style, fit the size, check the
rules, then save the PDF and its .json record.

CLI: python -m autofig make [--builds .github/build] [--specs figures/src] [--force] [--no-strict]
API: make(requests, specs="figures/src") -> list of (name, W) made; render(spec_path, request) -> info
The saved PDF (tight bbox, pad 0) is W wide and H tall to within 0.3 pt (H = slot height, else ASPECT*W).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402

from . import check  # noqa: E402
from .requests import Request, collect  # noqa: E402
from .style import PT_PER_IN, STYLE_VERSION, Style  # noqa: E402


def _stable_subset_names():
    """matplotlib names font subsets (ABCDEF+CMR10) from a hash that changes on every run.
    Use a hash of the glyphs instead, so the same figure gives the same PDF bytes and two
    branches that redraw it do not conflict."""
    import string
    from matplotlib.backends.backend_pdf import PdfFile
    if not hasattr(PdfFile, "_get_subset_prefix"):
        return

    def prefix(charset):
        n = int(hashlib.sha256(repr(sorted(charset)).encode()).hexdigest(), 16)
        return "".join(string.ascii_uppercase[(n >> (5 * i)) % 26] for i in range(6)) + "+"
    PdfFile._get_subset_prefix = staticmethod(prefix)


_stable_subset_names()

FIT_TOL = 0.05   # pt: stop iterating when the tight bbox is this close
SAVE_TOL = 0.3   # pt: accepted error of the saved PDF


class FigureRuleError(RuntimeError):
    pass


def load_module(path: Path):
    """Import a spec (or methods.py) by path, fresh each time (watch reloads edited specs)."""
    path = Path(path).resolve()
    for k, m in list(sys.modules.items()):     # forget modules imported from the spec folder
        if getattr(m, "__file__", None) and Path(m.__file__).resolve().parent == path.parent:
            del sys.modules[k]
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"autofig_spec_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_methods(specs: Path) -> dict:
    p = Path(specs) / "methods.py"
    return getattr(load_module(p), "METHODS", {}) if p.exists() else {}


DATA_REF = re.compile(r"""["'](?:\.\./|\./)*((?:figures/|code/)?data/[^"'\s]+)["']""")   # "figures/data/example.csv" in a spec


def spec_hash(spec_path: Path) -> str:
    """Hash of the spec, methods.py, every file next to the spec named <spec stem>_*, and each file under
    figures/data/, data/ or code/data/ that the spec names in a quoted string ("figures/data/example.csv").
    A change in any of them redraws the figure on the next make."""
    spec_path = Path(spec_path)
    raw = spec_path.read_bytes()
    h = hashlib.sha256(raw)
    extra = [spec_path.parent / "methods.py"] + sorted(spec_path.parent.glob(f"{spec_path.stem}_*"))
    root = spec_path.resolve().parent.parent.parent        # figures/src/<spec>.py -> the paper root
    for rel in sorted(set(DATA_REF.findall(raw.decode("utf-8", "ignore")))):
        extra += [p for p in (root / rel, Path(rel)) if p.is_file()][:1]
    for p in extra:
        if p.is_file():
            h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()[:16]


def _subplots(mod, s, w_in, h_in):
    rows, cols = getattr(mod, "PANELS", (1, 1))
    kw = dict(getattr(mod, "SUBPLOTS", {}))
    return plt.subplots(rows, cols, figsize=(w_in, h_in), squeeze=True, **kw)


def _fit(fig, w_in, h_in):
    """Change figsize until the tight bbox is w_in x h_in (2-4 passes)."""
    cw, ch = fig.get_size_inches()
    for _ in range(8):
        fig.set_size_inches(cw, ch)
        fig.draw_without_rendering()
        bb = fig.get_tightbbox()
        dw, dh = w_in - bb.width, h_in - bb.height
        if abs(dw) * 72 < FIT_TOL and abs(dh) * 72 < FIT_TOL:
            return
        cw, ch = cw + dw, ch + dh


def crop_to_ink(pdf: Path, keep=0.05):
    """Cut white margins left by text boxes (e.g. descender room, rotated labels); returns size in TeX pt."""
    import pymupdf
    ink = check.ink_bbox(pdf)
    doc = pymupdf.open(pdf)
    page = doc[0]
    W, H = page.rect.width, page.rect.height
    if ink and max(ink[0], ink[1], W - ink[2], H - ink[3]) > 0.2:
        x0, y0, x1, y1 = ink
        page.set_mediabox(pymupdf.Rect(max(x0 - keep, 0), max(y0 - keep, 0), min(x1 + keep, W), min(y1 + keep, H)))
        W, H = page.rect.width, page.rect.height
        doc.save(str(pdf) + ".c", garbage=1, deflate=True, no_new_id=True)
        doc.close()
        Path(str(pdf) + ".c").replace(pdf)
    else:
        doc.close()
    return W * check.BP, H * check.BP


def render(spec_path, req: Request, methods=None, strict=True) -> dict:
    """Draw spec for one slot and save <req.base>.pdf + .json. Returns the sidecar dict."""
    t0 = time.time()
    spec_path = Path(spec_path)
    mod = load_module(spec_path)
    if not hasattr(mod, "plot"):
        raise FigureRuleError(f"{spec_path} has no plot(fig, ax, s)")
    s = Style(req.w, req.h, req.f, req.family, req.compact, methods if methods is not None
              else load_methods(spec_path.parent))
    H = req.h or getattr(mod, "ASPECT", 0.62) * req.w
    w_in, h_in = req.w / PT_PER_IN, H / PT_PER_IN
    pdf = Path(req.base + ".pdf")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(s.rc):
        fig, ax = _subplots(mod, s, w_in, h_in)
        try:
            mod.plot(fig, ax, s)
            _fit(fig, w_in, h_in)
            probs = check.check_figure(fig, s)
            if probs and strict:
                raise FigureRuleError(f"{spec_path.name} at {req.w:g} pt breaks FIGURE RULES:\n  - "
                                      + "\n  - ".join(probs))
            tmp = pdf.with_suffix(".tmp.pdf")
            for _ in range(8):                       # verify on the saved file, correct if needed
                fig.savefig(tmp, bbox_inches="tight", pad_inches=0, metadata={"CreationDate": None})
                W, Hs = crop_to_ink(tmp)
                if abs(W - req.w) <= SAVE_TOL and abs(Hs - H) <= SAVE_TOL:
                    break
                cw, ch = fig.get_size_inches()
                fig.set_size_inches(cw + (req.w - W) / PT_PER_IN, ch + (H - Hs) / PT_PER_IN)
        finally:
            plt.close(fig)
    pprobs, info = check.check_pdf(tmp, w=req.w, h=H, f=req.f)
    if pprobs and strict:
        tmp.unlink()
        raise FigureRuleError(f"{pdf.name}: " + "; ".join(pprobs))
    tmp.replace(pdf)
    meta = dict(name=req.name, spec=str(spec_path), spec_hash=spec_hash(spec_path),
                style_version=STYLE_VERSION, request=dict(req.key(), h=round(req.h, 2)),
                size_pt=[info["width"], info["height"]], min_text_pt=info["min_text"],
                warnings=probs + pprobs, jobs=req.jobs)
    # No dates or timings in the files: the same inputs give the same bytes on every branch.
    pdf.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return dict(meta, seconds=round(time.time() - t0, 2))


def is_stale(req: Request, spec_path: Path) -> bool:
    pdf, meta = Path(req.base + ".pdf"), Path(req.base + ".json")
    if not pdf.exists() or not meta.exists():
        return True
    try:
        m = json.loads(meta.read_text())
    except ValueError:
        return True
    return (m.get("spec_hash") != spec_hash(spec_path) or m.get("style_version") != STYLE_VERSION
            or m.get("request") != dict(req.key(), h=round(req.h, 2)))


def refresh_fallbacks(reqs) -> None:
    """<dir>/<name>.pdf = copy of the widest variant on disk (used by LaTeX when its own variant is missing).

    Chosen among all variant files, not only this build's requests, so building one entry changes it only when it draws a new widest size.
    Serif variants win over sans ones; ties go to the file name, so the choice is stable across machines.
    """
    import re
    for d, name in sorted({(str(Path(r.base).parent), r.name) for r in reqs}):
        cands = []
        for f in Path(d).glob(f"{name}_w*.pdf"):
            m = re.fullmatch(rf"{re.escape(name)}_w(\d+)(?:_h\d+)?_f\d+(_sans)?", f.stem)
            if m:
                cands.append((m.group(2) is None, int(m.group(1)), f.name, f))
        if not cands:
            continue
        src, dst = max(cands)[3], Path(d) / f"{name}.pdf"
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copyfile(src, dst)
            print(f"fallback {dst} <- {src.name}")


def make(reqs, specs="figures/src", force=False, strict=True) -> tuple[list, int]:
    """Make every stale variant. Returns ([(name, W), ...] made, number of failures)."""
    specs = Path(specs)
    made, failed, methods = [], 0, None
    for r in sorted(reqs, key=lambda r: (r.name, r.w)):
        sp = specs / f"{r.name}.py"
        out = Path(r.base).name + ".pdf"
        if not sp.exists():
            print(f"FAIL {out}: no spec {sp} for this slot (jobs {','.join(r.jobs)})")
            failed += 1
            continue
        if not force and not is_stale(r, sp):
            print(f"ok   {out} (up to date)")
            continue
        try:
            if methods is None:
                methods = load_methods(specs)
            m = render(sp, r, methods, strict)
            print(f"made {out} {m['size_pt'][0]:.2f}x{m['size_pt'][1]:.2f} pt "
                  f"(text >= {m['min_text_pt']} pt, {m['seconds']:.1f} s)")
            for wmsg in m["warnings"]:
                print(f"     warning: {wmsg}")
            made.append((r.name, r.w))
        except Exception as e:      # report and continue with the other figures
            print(f"FAIL {out}: {e}")
            failed += 1
    refresh_fallbacks(reqs)
    return made, failed


def main(args) -> int:
    reqs = collect(args.builds)
    if not reqs:
        print(f"autofig: no requests found in {', '.join(args.builds)} (compile the paper first: "
              "autofig.sty writes <job>.afg)")
        return 0
    t0 = time.time()
    made, failed = make(reqs, args.specs, args.force, not args.no_strict)
    print(f"autofig: {len(reqs)} slots, {len(made)} made, {failed} failed ({time.time() - t0:.1f} s)")
    return 1 if failed else 0
