# .github/tools/_common.sh - functions for the scripts in .github/tools, which source this file; it is not run on its own.
# Finds the paper folder (PAPERKIT_ROOT, else the nearest folder with main.tex), the Python
# (PAPERKIT_PYTHON, else <paper>/.github/.venv/bin/python, else python3) and the figure engine
# (PAPERKIT_PYTHONPATH, else <paper>/.github/python). Also flattens the paper for release.sh and diff.sh.
# Works with bash 3.2 (macOS) and on Linux.

PK_TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log()  { printf '[%s] %s\n' "${PK_NAME:-paperkit}" "$*"; }
warn() { printf '[%s] WARNING: %s\n' "${PK_NAME:-paperkit}" "$*" >&2; }
die()  { printf '[%s] ERROR: %s\n' "${PK_NAME:-paperkit}" "$*" >&2; exit 1; }

# Print the usage text: the header comment of the calling script (from line 2 to the first blank line).
pk_usage() { sed -n '2,/^$/s/^# \{0,1\}//p' "$0"; }

# Paper root: PAPERKIT_ROOT, else walk up from $PWD, else walk up from the tools folder.
pk_find_root() {
  if [ -n "${PAPERKIT_ROOT:-}" ]; then
    [ -f "$PAPERKIT_ROOT/main.tex" ] || die "PAPERKIT_ROOT=$PAPERKIT_ROOT has no main.tex"
    (cd "$PAPERKIT_ROOT" && pwd); return 0
  fi
  local start d
  for start in "$PWD" "$PK_TOOLS"; do
    d="$start"
    while [ "$d" != "/" ] && [ -n "$d" ]; do
      if [ -f "$d/main.tex" ]; then printf '%s\n' "$d"; return 0; fi
      d="$(dirname "$d")"
    done
  done
  die "no paper root found (a folder with main.tex). cd into the paper or set PAPERKIT_ROOT."
}

# Sets PK_PY (python executable) and PK_KITPY (folder that contains the autofig package).
pk_find_python() {
  local root="$1"
  PK_PY="${PAPERKIT_PYTHON:-}"
  if [ -z "$PK_PY" ]; then
    if [ -x "$root/.github/.venv/bin/python" ]; then PK_PY="$root/.github/.venv/bin/python"; else PK_PY=python3; fi
  fi
  if [ -n "${PAPERKIT_PYTHONPATH:-}" ]; then PK_KITPY="$PAPERKIT_PYTHONPATH"
  elif [ -d "$root/.github/python/autofig" ]; then PK_KITPY="$root/.github/python"
  else PK_KITPY="$(cd "$PK_TOOLS/.." && pwd)/python"; fi
}

# Returns 0 if the figure engine can run; otherwise prints the reason and returns 1.
pk_autofig_ok() {
  command -v "$PK_PY" >/dev/null 2>&1 || { warn "Python '$PK_PY' not found (set PAPERKIT_PYTHON); figure step skipped"; return 1; }
  "$PK_PY" -c 'import matplotlib' >/dev/null 2>&1 || {
    warn "matplotlib missing for $PK_PY; figure step skipped (pip install -r .github/python/requirements.txt, or set PAPERKIT_PYTHON)"; return 1; }
  PYTHONPATH="$PK_KITPY${PYTHONPATH:+:$PYTHONPATH}" "$PK_PY" -c 'import autofig' >/dev/null 2>&1 || {
    warn "autofig package not found in $PK_KITPY; figure step skipped"; return 1; }
  return 0
}

# Run the figure engine: pk_autofig make|check|audit|... (from the current directory).
pk_autofig() { PYTHONPATH="$PK_KITPY${PYTHONPATH:+:$PYTHONPATH}" "$PK_PY" -m autofig "$@"; }

# Content fingerprint of a folder (file names + checksums) to detect changed figures.
pk_fingerprint() {
  [ -d "$1" ] || { echo none; return 0; }
  (cd "$1" && find . -type f | LC_ALL=C sort | while IFS= read -r f; do cksum "$f"; done) | cksum
}

pk_flatten_builtin() {  # \input{x} / \include{x} resolved from the paper root (then .github/tex), recursively
  perl -e '
    sub ex { my ($f, $d) = @_; die "input nesting too deep at $f\n" if $d > 20;
      my ($p) = grep { -f $_ } ($f, "$f.tex", ".github/tex/$f", ".github/tex/$f.tex"); $p //= $f;
      open(my $h, "<", $p) or do { warn "flattener: $f not found, \\input kept\n"; return "\\input{$f}" };
      my $o = "";
      while (my $l = <$h>) {   # split at the first unescaped %, expand \input/\include in the code part
        my ($code, $com) = $l =~ /^((?:[^\\%\n]|\\.)*)(.*)$/s;
        $code =~ s/\\(input|include)\{([^}]+)\}/($1 eq "include" ? "\\clearpage " : "") . ex($2, $d + 1)/ge;
        $o .= $code . $com; }
      # like TeX at the end of an \input file: drop final comment lines, then a final comment or newline
      1 while $o =~ s/(?:^|(?<=\n))[ \t]*%[^\n]*\n?\z//;
      $o =~ s/^((?:[^\\%\n]|\\.)*)%[^\n]*\n?\z/$1/m or $o =~ s/\n\z//;
      return $o; }
    print ex($ARGV[0], 0), "\n";' "$1"
}
pk_unresolved() {  # project files (root or .github/tex) still \input-ed in the flattened text (should be none)
  grep -oE '\\(input|include)\{[^}]+\}' "$1" | sed -E 's/.*\{(.*)\}/\1/' | while IFS= read -r f; do
    if [ -f "$f" ] || [ -f "$f.tex" ] || [ -f ".github/tex/$f" ] || [ -f ".github/tex/$f.tex" ]; then echo "$f"; fi; done
}
# Strip comments: drop comment lines, cut trailing comments down to "%", keep verbatim blocks, drop all after \end{document}.
pk_strip_comments() {
  perl -ne '
    BEGIN { $v = 0; $done = 0 } next if $done;
    if ($v) { print; $v = 0 if /\\end\{(verbatim|Verbatim|lstlisting|minted|comment)\*?\}/; next }
    next if /^\s*%/;
    s/^((?:[^\\%\n]|\\.)*?)%.*$/$1%/;
    s/^[ \t]+(\\(?:begin|end)\{)/$1/;   # comment.sty environments need \end{..} at line start
    print;
    $v = 1 if /\\begin\{(verbatim|Verbatim|lstlisting|minted|comment)\*?\}/ && !/\\end\{(verbatim|Verbatim|lstlisting|minted|comment)\*?\}/;
    $done = 1 if /^\s*\\end\{document\}/;' "$1"
}

# Flatten <entry> (run from its paper root) to stdout, comments stripped: latexpand if present and
# complete, else the built-in flattener. Sets PK_FLATTENER. PAPERKIT_NO_LATEXPAND=1 forces the fallback.
pk_flatten() {
  local tmp; tmp="$(mktemp "${TMPDIR:-/tmp}/paperkit-flat.XXXXXX")"
  PK_FLATTENER=builtin
  if command -v latexpand >/dev/null && [ -z "${PAPERKIT_NO_LATEXPAND:-}" ]; then
    latexpand --keep-comments "$1" 2>/dev/null | pk_strip_comments - > "$tmp" || true
    if [ -s "$tmp" ] && [ -z "$(pk_unresolved "$tmp")" ]; then PK_FLATTENER=latexpand
    else warn "latexpand left inputs unexpanded; using the built-in flattener"; fi
  fi
  [ "$PK_FLATTENER" = latexpand ] || pk_flatten_builtin "$1" | pk_strip_comments - > "$tmp"
  if [ -n "$(pk_unresolved "$tmp")" ]; then rm -f "$tmp"; die "unexpanded inputs after flattening $1"; fi
  cat "$tmp"; rm -f "$tmp"
}
