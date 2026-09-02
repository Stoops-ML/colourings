# Security policy

## Reporting a vulnerability

**Please do not open a public issue.**

Report privately through GitHub, using
[Report a vulnerability](https://github.com/Stoops-ML/colourings/security/advisories/new)
on the repository's Security tab. That opens a draft advisory visible only to
you and the maintainers, and it is the preferred route because the fix, the
advisory and the CVE can all be prepared in one place before anything is
public.

If that page is unavailable, email the address in the package metadata
(`danielstoops25@gmail.com`) with `colourings` in the subject line.

Please include the version of `colourings`, the Python version and platform, and
the smallest input that reproduces the problem. A proof of concept is welcome
but is not required to file a report.

You should get an acknowledgement within a week. `colourings` is maintained by
one person in their own time, so a fix may take longer than that; you will be
told where it stands rather than left waiting.

## Supported versions

Fixes are released for the latest published version only. There are no
maintenance branches for older releases: `colourings` has no runtime
dependencies, so upgrading to the current version is not usually disruptive.
Breaking changes are confined to major versions and are listed in the release
notes.

| Version | Supported |
| ------- | --------- |
| Latest release on PyPI | ✅ |
| Anything older | ❌ |

## What counts as a vulnerability here

`colourings` converts and manipulates colour values. It performs no I/O, opens
no network connections, deserialises nothing, and executes nothing it is given.
It has no runtime dependencies. That rules out most of what usually reaches a
Python library, and it is worth being specific about what remains:

- **Denial of service through a crafted input.** The CSS parser
  (`colourings.css`) and the hex-shape predicates are regular expressions
  applied to caller-supplied strings. They are written without nested
  quantifiers, so catastrophic backtracking should not be reachable — an input
  that takes superlinear time to parse is a bug worth reporting.
- **Unbounded memory growth.** Conversions are memoised. The caches are bounded
  (`lru_cache(maxsize=1024)`), and `clear_caches()` empties them; an input that
  makes memory grow without bound is a bug worth reporting.
- **The release process.** The published wheel and sdist, the signing and
  provenance of a PyPI release, and this repository's GitHub Actions workflows
  are all in scope. So is anything that would let a third party publish under
  this project's name.

Out of scope, because they are what the library is for: raising `ValueError` on
malformed input, returning a colour you disagree with, and any result of
passing a value the type annotations do not permit.

## Anything already public

If a problem is already public — an open issue, a post, an advisory elsewhere —
there is nothing to keep private. Say so in the report and link it, and it will
be handled in the open.
