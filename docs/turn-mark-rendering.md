# Rendering the turn mark

**Superseded by [transcript-svg-spec.md](transcript-svg-spec.md), and two of
this document's central claims were wrong.** They are recorded here rather than
deleted, because they circulated: they reached `main` on 2026-09-02, went into
project memory, and were used to argue that parts of this repository rested on a
false premise.

## What was wrong

**"A relative path renders."** This document said
`![](.identicon/repository-identicon.svg)` displayed in a desktop pane, and
called the sentence it contradicted — that a `data:` URI carries its bytes and
cannot reference a path — the justification for the whole base64 apparatus.

A repository-relative path renders as **a link**, on the desktop and on Android
alike. Paths cannot work in principle: the transcript is not served from the
repository, and the container's filesystem is reachable from nothing but the
container, which is discarded when the session ends. The original sentence was
correct.

**"Base64 is only needed for PNG."** This document said SVG travels
percent-encoded, shorter and legible, and that base64 had no remaining
justification for the format.

Percent-escaped payloads **fail on Android**, in both minimal and total
spellings, as does raw unescaped SVG. Android requires
`data:image/svg+xml;base64,` with the token lowercase and the payload padded —
neither of which RFC 2397 demands. Base64 is required, not vestigial.

## What survives

The sizing finding holds, and the spec states it as a law:
`rendered size = column width × (mark units / viewBox width)`. Pixels were never
the only control. So does the observation that card-style rendering is
channel-dependent rather than a pure size threshold.

## Why it went wrong

Every claim here was measured on a desktop pane and generalised to clients that
were never tested. The spec names the habit that prevents it: a blanket answer
hides a client difference, so ask per variant and per client, and vary one
property at a time.

That matters beyond this document, because the failure is asymmetric. Every
deviation in the encoding table passes on a desktop and fails on a phone — so a
change made and checked on a desktop looks correct and silently breaks the
client it matters most for.
