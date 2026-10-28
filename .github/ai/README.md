# AI assistants

| File | Content |
|---|---|
| `AGENTS.md` | the rules an assistant follows in this paper |
| `PAPERKIT_FOR_AI.md` | all commands and setup steps, for any AI chat |
| `editmarks.cfg` | declares the editor `ai`, shown in violet, for the assistant's edits |
| `skills/paper/SKILL.md` | step-by-step instructions to set up, edit, draw figures, review and release |

## Start

| Assistant | First step |
|---|---|
| Claude Code, Codex | open the paper folder; first message: "Read .github/ai/AGENTS.md" |
| any AI chat | upload `PAPERKIT_FOR_AI.md`, then paste each answer into the file it names |
| on a GitHub pull request | write `@claude` or `@codex review`, followed by "Read .github/ai/AGENTS.md"; you merge its fixes |

To install the skill for Claude Code on your machine:

```bash
mkdir -p ~/.claude/skills && cp -R .github/ai/skills/paper ~/.claude/skills/
```

Permissions to allow in Claude Code: `Edit`, `Write`, `Bash(git:*)`, `Bash(make:*)`, `Bash(bash .github/tools/*)`, `Bash(latexmk:*)`, `Bash(gh:*)`.

A first request could be: "Set up this template for my paper: title ..., authors ..., versions ..., templates ...".
The assistant fills in the `EDIT HERE` parts of `setup.tex` and `versions/`, then builds.

## Edits by the assistant

The assistant marks each change as `\added{ai}{...}` or `\replaced{ai}{new}{old}`.
The review copy shows these changes in violet. In the submitted PDFs they are accepted.
To accept them in the review copy too, put `\acceptedits{ai}` after `\begin{document}`.
It commits with short plain messages and pushes only when you ask: small changes to `main`,
larger ones to a branch named after the topic, with a pull request.
