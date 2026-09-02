## What this changes

<!-- What the change does, and why it is worth making. The diff already shows
     how. -->

## How it was verified

<!-- Not "tests pass" -- CI reports that. What did you check, and what would
     have caught it if it were wrong?

     For anything touching colour arithmetic, say what the expected values
     were checked against: a published standard, a reference implementation,
     or a property such as symmetry or round-trip identity. Recording the
     output the code currently produces only pins a bug in place. -->

## Checklist

- [ ] Tests cover the change, and fail without it
- [ ] `python -m pytest --cov colourings` passes, still at 100%
- [ ] `python -m ruff check` and `python -m ruff format --diff` are clean
- [ ] `python -m ty check` is clean
- [ ] Docstrings are numpydoc style, and `README.md` is updated if the change
      is visible from outside
- [ ] Commits are conventional commits, with `!` or `BREAKING CHANGE:` if this
      breaks anything

## Breaking changes

<!-- What breaks, what the old code looked like, and what it should become.
     Delete this section if nothing breaks. -->
