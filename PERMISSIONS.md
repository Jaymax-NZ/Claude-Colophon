# Permissions

What this plugin causes Claude to run, and why. **Documentation only** — nothing
here is installed or requested automatically. It exists so you can decide before
approving, and so a prompt is never the first time you learn a tool wanted
something.

Permission rules live in your own `settings.json` and are yours to write. A
plugin cannot grant itself any of this, by design: if installing something could
authorise its own code, installation would be the entire attack surface.

## Summary

Two commands, both local, both read-only with respect to anything outside the
repository you point them at.

| when | what runs | needed? |
|---|---|---|
| once per repository | the installer script | yes, to install at all |
| once per session | a read of one environment variable | only as a tiebreak, see below |

Nothing here makes a network call. Nothing reads outside the repository being
worked on, except the plugin reading its own files.

## 1. The installer

```
Bash(<plugin path>/skills/repo-identicon/repo-identicon.py:*)
```

Run once per repository, when you invoke `/repo-identicon`. Writes `.identicon/`
and a section in `CLAUDE.md`, both at the repository root, and refuses any path
that resolves outside it. It shells out only to read-only git queries
(`rev-parse --show-toplevel`, `remote get-url`) and never mutates git state.

**The path is not fixed, so this rule cannot be published verbatim.** A plugin's
location on disk varies by how it was installed. Find yours with:

```bash
claude plugin details claude-colophon
```

If you would rather not allowlist it at all, approving the prompt once per
repository is a reasonable trade — it is genuinely a once-per-repository action.

## 2. The render-target probe

```
Bash(python3 -c *)
```

The mark exists in two forms, because the two clients cannot show the same
thing: a GUI chat client renders a markdown image, a terminal shows characters.
Choosing correctly means knowing which client is rendering the reply.

**In most sessions this needs no command at all.** The available tools already
answer it — a client that offers inline rendering, artifacts or a side panel is
a client that displays images, and one that offers none is not. The instruction
installed into your repository says to use that first, and to fall back to the
block form when it is unclear.

The probe is only for resolving genuine doubt:

```bash
python3 -c "import os; print(os.environ.get('CLAUDE_CODE_ENTRYPOINT','?'))"
```

It reads one environment variable and prints it. It is worth knowing that the
system prompt is **not** a reliable substitute: it describes output as markdown
"in a terminal" in every client, including GUI ones where that is false. That
line is why this probe exists rather than a simpler instruction to read the
prompt.

Do not allowlist this if you would rather not — the cost of declining is that
sessions default to the block form, which is legible everywhere and merely
plainer than it needs to be in a GUI.

## What is deliberately not here

- **No `SessionStart` hook.** It was designed and rejected. A hook would remove
  the probe, at the cost of running in every session in every repository,
  including those with no identicon, to answer a question most sessions can
  already answer for free.
- **No network permission.** The derivation is a hash of your git remote's
  *name*. Nothing is fetched, and nothing is reported anywhere.
- **No write access beyond the target repository**, enforced in the script
  rather than merely intended: every path is resolved and checked against the
  repository root before anything is written.

## Rule syntax

Current Claude Code writes prefix rules as `Bash(command:*)`. Older settings
files in the wild use `Bash(command *)`. If you are editing an existing file,
match whatever is already there rather than mixing both.
