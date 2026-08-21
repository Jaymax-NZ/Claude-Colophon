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
