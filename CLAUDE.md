## Name the thing

Never write "the plugin", "the skill", "the script" or "the tool". Here every
one of those has more than one referent -- three projects, two skills, three
scripts -- so a bare generic noun costs the reader a lookup, and sometimes
hands them the wrong object without either of you noticing.

Write the name: Claude Colophon, Repository Identicon, `repo-identicon.py`,
`text-identicon.py`, `session-tricolour.py`, `.identicon/`. Where a full name
is heavier than the sentence needs, one adjective in front of the noun does the
same work -- the *identicon* generator, the *tagging* section, the *vendored*
renderer -- because the adjective is the half that disambiguates.

Prose, comments, commit messages and replies alike.

## Tag this session with this repository's tricolour

At the end of your first turn in this repository, and on any later turn where
you notice it missing, make this session's name begin with this repository's
three coloured squares, so that a list of sessions can be told apart without
being read.

The squares are the whole of
`.identicon/repository-identicon.tricolour` if that file exists,
and otherwise the last three characters of the last line of
`.identicon/repository-identicon.txt`.
Read them from there. Do not work them out from the colour, the remote, or
anything else: one repository, one mark, one thing that produces it.

Then, if this client gives you a tool that can rename a session:

- ask it for this session's current name;
- if that name already starts with those three squares, do nothing;
- otherwise set the name to the three squares, a space, and the name as it was
  -- replacing any three squares already on the front.

A prefix rather than a suffix, because a list of session names truncates on the
right, which is where a suffix would be.

**Not at the start of a session.** The name is generated from the first prompt
a few seconds in, and anything set before that is overwritten.

If this client has no such tool, or refuses to rename this session, do nothing
and say nothing -- this is a convenience about legibility and must not become
the noisiest thing in the transcript. If it can rename other sessions but not
this one, this one can be named by another session, which must be *given* these
three squares rather than working them out for itself.

To stop this, remove this section: its presence is the switch.

## Sign every response with this repository's identicon

Emit this line, verbatim, as the last line of every response in this
repository. Nothing after it.

**Also emit it immediately before asking the user anything** -- as the last
line of the text preceding a question, including before a tool call that puts
a question to them. A turn that ends in a question may never reach a turn-end
at all, so it is both the turn most likely to lose the mark and the one where
the reader most needs it: they are being asked to stop and decide, and which
project is asking is part of the question.

![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAARCAYAAAA7bUf6AAAAKklEQVR42mNgGAVYwU21Hf+xYZLUDB5DcCkmRnwQGoLLv8TgQWjIKEABABk3DHJzxKS5AAAAAElFTkSuQmCC)

It is a PNG of this repository's identicon: a 5x5 grid inside a one-pixel
border, derived from the repository's identity rather than from its path, so it
is the same in every checkout on every machine.

The pixel size is deliberately not written down here. A re-run refreshes the
image above but leaves this prose alone -- as it must, so that a repository
which has rewritten the explanation keeps its wording -- and a number nothing
refreshes is a number that goes stale. `.identicon/icon.png` is the record.

`.identicon/` holds the same mark in every form a consumer might want, each
usable with no parsing at all:

| file | for |
|---|---|
| `.identicon/repository-identicon.png` | a README, or anywhere that refuses SVG |
| `.identicon/repository-identicon.svg` | a README on a forge that renders it; anything scalable |
| `.identicon/repository-identicon.colour` | `#rrggbb`, for a prompt, a badge, or a theme |

Each name repeats the directory on purpose, so that a file still says what it is
once it has been copied somewhere else.

The literal above is base64 of the PNG, which is the one form a file cannot
provide: a `data:` URI carries its bytes and cannot reference a path.

Do not edit any of them by hand, including the literal above -- regenerate the
whole set with `/repo-identicon`.

**Why this is an instruction rather than a hook**, given that an instruction
depends on compliance and a hook does not: no hook output field can display an
image. A hook's `systemMessage` arrives as plain text, one event-name prefix
per line. The only channel in a GUI chat client that renders markdown is an
assistant message, and only the model writes those. So the deterministic
mechanism cannot render, and the mechanism that renders cannot be made
deterministic. This is the second of the two, chosen knowingly.
