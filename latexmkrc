# latexmkrc - latexmk reads it from the top folder, on a laptop and on Overleaf. The paper compiles with pdfLaTeX, Overleaf's default.
# It adds .github/ to the TeX search path (packages, classes, layout.tex) and the top folder to the BibTeX path (refs/).
# The absolute paths still work when latexmk changes into versions/ (latexmk -cd, as Overleaf does).
# The zip for Overleaf's Upload Project has .github/tex as github/tex, because the upload drops folders that start with a dot.
ensure_path('TEXINPUTS', './.github//', Cwd::getcwd() . '/.github//', './github//', Cwd::getcwd() . '/github//');   # // also searches subfolders, except those that start with a dot, such as .github/.venv
ensure_path('BIBINPUTS', Cwd::getcwd() . '/');
$pdf_mode = 1;
$bibtex_use = 2;
@default_files = ('main.tex');   # plain `latexmk` builds main.tex only, not every .tex file in the folder
# Output folder: .github/build/<name>/, the folder make -f .github/Makefile uses, so nothing lands in the top folder.
# An -outdir on the command line overrides it (Overleaf and .github/tools/build.sh pass one).
# With several files on one command line, all of them go to .github/build/.
my @names = map { m{([^/\\]+)\.tex$} ? $1 : () } @ARGV;
$out_dir = Cwd::getcwd() . '/.github/build' . (@names == 1 ? "/$names[0]" : (@names ? '' : '/main'));
