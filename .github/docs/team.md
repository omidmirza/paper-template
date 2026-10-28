# Co-authors

## Add people

One line per person in `setup.tex`:

```latex
\DeclareEditor{anna}{AK}             \editorname{anna}{Anna Keller}
\DeclareEditor[RoyalBlue]{ben}{BO}   \editorname{ben}{Ben Osei}     % with a colour of your choice
```

1. Replace `author1` to `author3` with your co-authors.
2. Change or delete the two example lines in `sections/intro.tex`.
   Otherwise the build stops with `Undeclared editor 'author1'`.

The first 13 people get colours from the colour-blind-safe Okabe-Ito and Paul Tol palettes, in turn. From the 14th person on the colours repeat, so give those people a colour of their own.

## Mark edits

Anna writes `\added{anna}{...}` or `\replaced{anna}{new}{old}`. The review copy shows the change in her colour.
[edits.md](edits.md) and [toggle_helper.tex](../../toggle_helper.tex) list every command.

## Work on a branch

A branch keeps your changes apart from `main` until you merge them with a pull request.

```bash
git switch -c anna/intro       # one branch per person and topic
make -f .github/Makefile       # build after editing
git add -A && git commit -m "Intro: shorter motivation"
git push -u origin anna/intro  # then open a pull request on GitHub
```

On each push, GitHub builds every version. The run's summary has one row per version, and the PDFs are under Artifacts.
Merge when every row says `ok`.

Overleaf syncs `main` only, so co-authors on Overleaf write on `main`.
After a merge, press "Pull GitHub changes into Overleaf".

## Conflicts

Git reports a conflict when two people change the same lines. Resolve it on a laptop:

```bash
git pull origin main
# fix the text files; for the drawn figures and labels, keep your side:
git checkout --ours figures/auto refs/extended_labels.tex
make -f .github/Makefile
git add -A && git commit --no-edit && git push
```

The Conflicts section of [git_overleaf.md](git_overleaf.md) shows how to fix a text file.

For fewer conflicts, write one sentence per line and keep one file per section in `sections/`. If two people added a line at the same place in `setup.tex`, keep both lines.

If GitHub warns that the figures are out of date, run `make -f .github/Makefile` and commit `figures/auto`.
`bash .github/tools/setup_git.sh` installs a check that refuses commits with conflict markers or build files.

## Add a version

For a new version, such as a thesis chapter, see the thesis row in [versions.md](versions.md).
