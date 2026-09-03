# Repository scope

What this repository may contain, and what has to arrive from
Repository-Identicon instead.

![Which project writes what, and the one path from a repository to a webpage](repository-stack.svg)

This repository is a consumer. Repository-Identicon specifies the derivation and
every rendering produced from it, and `skills/repo-identicon/repo-identicon.py`
runs its generator rather than carrying a copy of either. A rendering written
here is one the standard does not describe. Add it there, and re-run the
generator.

The green path in the figure ends at a webpage without passing through Claude
Colophon: a forge reads `.identicon/repository-identicon.svg` out of the
repository and renders it. A rendering written here rather than by the generator
never appears in `.identicon/`, so it never reaches that path.

## The 4x raster

`.identicon/repository-identicon@4x.png` was removed on 2026-09-03.

The requirement it served stands. A native toolkit selects an asset per scale
factor, and a mark of 7 to 27 pixels is too small for a native icon slot. What
was wrong was the route: a 4x raster is a rendering, so Repository-Identicon
specifies it in `SPEC.md`, its reference implementation writes it first, and it
reaches this repository by re-vendoring.

The argument was made once already, on the cloud branch
`claude/code-scope-validation-env7yq`, which added the raster in one commit
(`3bdfa46`) and reverted it in the next (`2f1d59d`). That branch was never
merged, so the argument was lost, and the file was committed here again on
2026-08-30 in `e168249`. This document exists so the decision does not have to
be made a third time.

One claim in the original revert is now false: it said this repository has no
tests. `tests/test_repo_identicon.py` and `tests/test_tricolour.py` exist. The
rest of the argument does not depend on it.

`docs/turn-mark-rendering.md` reaches the same conclusion from a different
direction — that an SVG `viewBox` ratio sets apparent size, so pixel dimensions
were never the only control, and the large rasters were a workaround for a
constraint that does not exist.

## What was left in place

`repository-identicon-128.png` and `-256.png` are the same class of artifact.
`skills/repo-identicon/repo-identicon.py` generates `.png` and `.svg` only, so a
re-run of `/repo-identicon` produces none of the three; all of them arrived in
`e168249` as part of vendoring the mark. They were kept on 2026-09-03 because
only `@4x.png` was in scope. Whether they stay is undecided.
