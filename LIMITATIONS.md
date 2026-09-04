# Limitations

What a session can and cannot determine about itself.

This plugin's instructions depend on a session knowing things about its own
environment: which surface will render the turn mark, which repository it is in,
what its own title is. Some of those are determinable and some are not. This
file records which is which, and names the wrong inferences that have been drawn
from each, so they are not drawn again.

Every entry below was tested on 2026-09-04 in a desktop session on
Claude-Colophon, except where it names another date.

## Determinable

**Never claim the environment offers nothing to determine these from.** Each
entry in this section has been asserted impossible at least once and then shown
to be determinable, and the rendering question three separate times — once by
opening chats in different interfaces to demonstrate it. A session that cannot
find the signal has not looked; it has not discovered a limit. The standing rule
is in `~/.claude/CLAUDE.md` under *Identicon rendering*.

**Which rendering to emit.** The presence of `mcp__ccd*` tools means a
desktop-hosted pane that renders markdown images, so emit the PNG. Their absence
means a console or headless run, so emit the sextant plus the tricolour. The
tool check costs nothing. `CLAUDE_CODE_ENTRYPOINT` (`cli` against
`claude-desktop`) and `TERM` corroborate it at the cost of a command.

**Where the session executes.** `CLAUDE_CODE_HOST_SESSION_ID` prefixed `local_`,
`entrypoint: claude-desktop` and `kind: interactive` in
`~/.claude/sessions/<pid>.json`, a running pid, and a unix socket under
`/run/user/<uid>/cc-socks/` together say the session runs on this machine.

**This repository's tricolour.** Read `renders.tricolour` from
`.identicon/settings.json`, or read the titles of sibling sessions from
`list_sessions`. The second is a tool call rather than a file read and is the
better source: it reflects what the session list actually shows.

**The session's own CCD id.** `CLAUDE_CODE_HOST_SESSION_ID` is the `sessionId`
that the `mcp__ccd_session_mgmt__*` tools take. It is not the same as
`CLAUDE_CODE_SESSION_ID`, which names the transcript file. A session has both.

## Not determinable

**Whether the session is under Remote Control.** Nothing tested reports it. Two
signals look as though they do and do not:

- `ListAgents` lists cloud and Remote Control peers *when Remote Control is
  connected*. It lists peers the session can address outbound. A session being
  driven by Remote Control does not appear to itself as a peer, and neither does
  its controller. No Remote Control rows is not no Remote Control.
- `bridgeSessionId` in `~/.claude/sessions/<pid>.json` binds a session to a
  claude.ai counterpart for the remote title. A session was driven by Remote
  Control on 2026-09-04 with no such field present.

A session asserted it was not remote-controlled while a person was typing into
it by Remote Control. Do not make that claim. Execution locality and input
locality are different questions, and only the first has an answer.

**The session's own title, by tool.** `set_session_title` reports the previous
title, not the resulting one. `list_sessions` excludes the current session.
`get_session` refuses it — by the literal `"self"`, which returns "not found",
and by its real CCD id, which returns an explicit refusal. Reading
`custom-title.json` or the transcript's `aiTitle` returns the value that was
written, from the same layer that wrote it. That is storage, not the round trip.

**The session's own metadata, from context.** `get_session`'s refusal suggests
using "your own session context for this one". The model's context carries the
working directory, the git state, the model name, the transcript id and the
loaded tools. It carries no title, no session kind, and no `isRemote`. The hint
points at nothing.

## Uncalibrated

**`isRemote`.** `get_session` returns this field for a peer; `list_sessions`
rows omit it. It may mean cloud-hosted rather than Remote Control attached.
Every session queryable on 2026-09-04 read `false`, including during a session
driven by Remote Control, so there is no positive example to tell the two
readings apart. Do not report it as a Remote Control indicator until a session
known to be remote-controlled has been seen to read `true`.

## The shape of the recurring error

Each wrong claim above was a contrapositive that the source never offered. A
tool documents what it shows *when* a condition holds; that does not license a
claim about the condition *not* holding. `get_session` refuses the current
session; that did not license the claim that `set_session_title` refuses it too,
and for weeks it was claimed that a session could not rename itself. It can.

Before asserting a negative about the session, name the tool that would have
shown the positive, and check that it was actually called.
