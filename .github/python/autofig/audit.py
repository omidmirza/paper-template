"""Render-in-document check (rule 8): the smallest text inside every figure of a compiled PDF.

CLI: python -m autofig audit paper.pdf [--body 10] [--json out.json]
Figures are the placed images and form XObjects (\\includegraphics of a PDF); each file name comes from
/PTEX.FileName. Exit status 1 if any figure has text below the body size (scripts: below 0.69 of it).
Without --body, the body size is the most common text size outside the figures.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from .check import BP, SCRIPT, TOL, _center_in, text_sizes

_TOK = re.compile(rb"\s*(?:(%[^\r\n]*)|(\()|(<<|>>)|(<[0-9A-Fa-f\s]*>)|(/[^\s/\[\]()<>{}%]*)|"
                  rb"([-+]?(?:\d+\.?\d*|\.\d+))|([\[\]{}])|([A-Za-z'\"*][A-Za-z0-9'\"*]*))")


def _tokens(data: bytes):
    """Minimal PDF content-stream tokenizer: yields ('num', v) | ('name', s) | ('op', s)."""
    i, n = 0, len(data)
    while i < n:
        m = _TOK.match(data, i)
        if not m:
            i += 1
            continue
        i = m.end()
        if m.group(2):                       # literal string: skip, honouring escapes and nesting
            depth = 1
            while i < n and depth:
                c = data[i:i + 1]
                if c == b"\\":
                    i += 1
                elif c == b"(":
                    depth += 1
                elif c == b")":
                    depth -= 1
                i += 1
        elif m.group(5):
            yield "name", m.group(5)[1:].decode("latin-1")
        elif m.group(6):
            yield "num", float(m.group(6))
        elif m.group(8):
            yield "op", m.group(8).decode("latin-1")


def _mul(a, b):
    """Product of PDF matrices [a b c d e f]: a then b."""
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3], a[2] * b[0] + a[3] * b[2],
            a[2] * b[1] + a[3] * b[3], a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def _box(m, x0, y0, x1, y1):
    pts = [(x * m[0] + y * m[2] + m[4], x * m[1] + y * m[3] + m[5]) for x in (x0, x1) for y in (y0, y1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def figure_regions(doc, page):
    """[(rect in pymupdf coords, file name), ...] for every image / form XObject drawn by the page."""
    import pymupdf
    xobj = {}
    for xref, name, invoker, _bb in page.get_xobjects():
        if invoker == 0:
            xobj[name] = ("form", xref)
    for im in page.get_images(full=True):
        xobj[im[7]] = ("image", im[0])
    out, ctm, stack, nums, last = [], [1, 0, 0, 1, 0, 0], [], [], None
    for kind, v in _tokens(page.read_contents()):
        if kind == "num":
            nums.append(v)
            continue
        if kind == "name":
            last = v
            continue
        if v == "q":
            stack.append(ctm)
        elif v == "Q" and stack:
            ctm = stack.pop()
        elif v == "cm" and len(nums) >= 6:
            ctm = _mul(nums[-6:], ctm)
        elif v == "Do" and last in xobj:
            typ, xref = xobj[last]
            if typ == "image":
                r = _box(ctm, 0, 0, 1, 1)
            else:
                bb = [float(x) for x in re.findall(r"[-\d.]+", doc.xref_get_key(xref, "BBox")[1])]
                mt = doc.xref_get_key(xref, "Matrix")
                m = [float(x) for x in re.findall(r"[-\d.]+", mt[1])] if mt[0] == "array" else [1, 0, 0, 1, 0, 0]
                r = _box(_mul(m, ctm), *bb)
            fn = doc.xref_get_key(xref, "PTEX.FileName")[1].strip("()") or f"{typ} {last}"
            rect = pymupdf.Rect(r[0], r[1], r[2], r[3]) * page.transformation_matrix
            out.append((rect, fn))
        nums = []
    return out


def body_size(doc, regions_by_page) -> float:
    """Most common span size (TeX pt, by characters) outside figures."""
    c = Counter()
    for page in doc:
        regs = regions_by_page[page.number]
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for sp in line["spans"]:
                    if sp["text"].strip() and not any(_center_in(sp["bbox"], r) for r, _ in regs):
                        c[round(sp["size"] * BP, 2)] += len(sp["text"].strip())
    return c.most_common(1)[0][0] if c else 10.0


def audit(pdf, body=None, min_area=400.0):
    import pymupdf
    rows = []
    with pymupdf.open(pdf) as doc:
        regs = {p.number: [(r, f) for r, f in figure_regions(doc, p) if r.width * r.height >= min_area]
                for p in doc}
        detected = body_size(doc, regs)
        body = body or detected
        for p in doc:
            for r, fn in regs[p.number]:
                base, script = text_sizes(p, r)
                ok = (base is None or base >= body - TOL) and (script is None or script >= SCRIPT * body - TOL)
                rows.append(dict(page=p.number + 1, file=fn, width=round(r.width * BP, 1),
                                 height=round(r.height * BP, 1), min_text=base and round(base, 2),
                                 min_script=script and round(script, 2), ok=ok))
    return rows, body, detected


def main(args) -> int:
    rows, body, detected = audit(args.pdf, args.body)
    print(f"audit {args.pdf}: body {body:g} pt (detected {detected:g} pt), {len(rows)} figure(s)")
    for r in rows:
        txt = "no text" if r["min_text"] is None else f"min text {r['min_text']:.2f} pt" + (
            f", scripts {r['min_script']:.2f} pt" if r["min_script"] else "")
        flag = "ok  " if r["ok"] else "FAIL"
        print(f"{flag} p{r['page']} {r['file']} {r['width']:.1f}x{r['height']:.1f} pt: {txt}")
    if args.json:
        Path(args.json).write_text(json.dumps(dict(pdf=str(args.pdf), body=body, figures=rows), indent=1))
    return 0 if all(r["ok"] for r in rows) else 1
