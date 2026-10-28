#!/usr/bin/env bash
# diff.sh - make a PDF that marks the changes between two git versions of the paper (latexdiff).
# Usage: bash .github/tools/diff.sh <old-ref> [<new-ref>] [entry.tex]      for example: bash .github/tools/diff.sh v1-arxiv
#   new-ref defaults to the working tree; entry to versions/*arxiv*.tex, else versions/*extended*.tex,
#   else the first file in versions/, else main.tex.
#   Both sides are flattened into one file each and compared with latexdiff.
#   The marked file is compiled in .github/build/diff_<old>_<new>/ with the files of the new version;
#   files that only the old version has are taken from the old one.
#   Output: .github/pdf/diff_<old>_<new>.pdf

set -euo pipefail
PK_NAME=diff
. "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in -h|--help) pk_usage; exit 0 ;; -*) die "unknown option $1" ;; *) ARGS+=("$1") ;; esac; shift
done
[ ${#ARGS[@]} -ge 1 ] || { pk_usage; die "missing <old-ref> (a tag, branch or commit; see: git tag; git log --oneline)"; }
OLD="${ARGS[0]}"; NEW=""; ENTRY=""
for a in "${ARGS[@]:1}" ""; do [ -n "$a" ] || continue; case "$a" in *.tex) ENTRY="$a" ;; *) NEW="$a" ;; esac; done

ROOT="$(pk_find_root)"; cd "$ROOT"
command -v latexdiff >/dev/null || die "latexdiff not found (part of TeX Live)"
git rev-parse --git-dir >/dev/null 2>&1 || die "not a git repository"
REL="$(git rev-parse --show-prefix)"; REL="${REL%/}"          # paper root inside the repo ("" = top)
git rev-parse -q --verify "$OLD^{commit}" >/dev/null || die "unknown ref $OLD"
[ -z "$NEW" ] || git rev-parse -q --verify "$NEW^{commit}" >/dev/null || die "unknown ref $NEW"
if [ -z "$ENTRY" ]; then
  for pat in 'versions/*arxiv*.tex' 'versions/*extended*.tex' 'versions/*.tex' 'main.tex'; do
    for f in $pat; do [ -f "$f" ] && { ENTRY="$f"; break 2; }; done
  done
fi
[ -f "$ENTRY" ] || die "entry not found: $ENTRY"

safe() {  # file-name-safe ref; full commit ids shortened to 7 characters
  case "$1" in *[!0-9a-f]*|'') printf '%s' "$1" | tr -c 'A-Za-z0-9._-' '-' ;; *) printf '%s' "$1" | cut -c1-7 ;; esac; }
NAME="diff_$(safe "$OLD")_$(safe "${NEW:-working}")"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/paperkit-diff.XXXXXX")"; trap 'rm -rf "$TMP"' EXIT

tree_of() {  # tree_of <ref> <dir>: export the paper root of <ref> into <dir>
  mkdir -p "$2"; (cd "$(git rev-parse --show-toplevel)" && git archive --format=tar "$1") | tar -x -C "$2"
  printf '%s\n' "$2${REL:+/$REL}"
}
OLDROOT="$(tree_of "$OLD" "$TMP/old")"
[ -f "$OLDROOT/$ENTRY" ] || die "$ENTRY does not exist in $OLD"
(cd "$OLDROOT" && pk_flatten "$ENTRY") > "$TMP/old.tex"
if [ -n "$NEW" ]; then
  NEWROOT="$(tree_of "$NEW" "$TMP/new")"
  (cd "$NEWROOT" && pk_flatten "$ENTRY") > "$TMP/new.tex"
else
  NEWROOT="$ROOT"; pk_flatten "$ENTRY" > "$TMP/new.tex"
fi

OUT=".github/build/$NAME"; mkdir -p "$OUT" .github/pdf
latexdiff --type=UNDERLINE --math-markup=coarse --append-textcmd="added,onlyin,exceptin,pending" "$TMP/old.tex" "$TMP/new.tex" > "$OUT/$NAME.tex" 2>"$OUT/latexdiff.err" \
  || { tail -n 5 "$OUT/latexdiff.err" >&2; die "latexdiff failed"; }
log "latexdiff $OLD -> ${NEW:-working tree} ($ENTRY)"

# Compile from the new root (its figures, .bib, .sty); the old tree is the fallback for removed files.
# TeX reads \includegraphics paths from the folder latexmk runs in, so the marked file can stay in $OUT.
SRC="$OUT/$NAME.tex"
mkdir -p "$NEWROOT/$OUT"; [ "$NEWROOT" = "$ROOT" ] || cp "$SRC" "$NEWROOT/$SRC"
if (cd "$NEWROOT" && TEXINPUTS=".:$OLDROOT/:${TEXINPUTS:-}" BIBINPUTS=".:$OLDROOT/:${BIBINPUTS:-}" \
      latexmk -pdf -interaction=nonstopmode -file-line-error -outdir="$OUT" -jobname="$NAME" "$SRC" \
      >"$NEWROOT/$OUT/latexmk.out" 2>&1); then ok=1; else ok=0; fi
[ "$NEWROOT" = "$ROOT" ] || cp "$NEWROOT/$OUT/"* "$OUT/" 2>/dev/null || true
if [ -f "$OUT/$NAME.pdf" ]; then cp "$OUT/$NAME.pdf" ".github/pdf/$NAME.pdf"; fi
if [ "$ok" = 1 ]; then
  log "done: .github/pdf/$NAME.pdf ($(pdfinfo ".github/pdf/$NAME.pdf" 2>/dev/null | awk '/^Pages:/{print $2}') pages)"
else
  grep -m6 -E '^(! |.*:[0-9]+: )' "$OUT/$NAME.log" >&2 || tail -n 15 "$OUT/latexmk.out" >&2
  [ -f ".github/pdf/$NAME.pdf" ] && die "compiled with errors (above); check .github/pdf/$NAME.pdf"
  die "diff did not compile; the marked source is $OUT/$NAME.tex"
fi
