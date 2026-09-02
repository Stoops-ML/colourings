# Contributing to colourings

Thanks for taking the time. This file describes what CI will check, so that
nothing about a review is a surprise.

If you are reporting a security problem, do not open an issue — see
[SECURITY.md](SECURITY.md).

## Getting set up

The package has no runtime dependencies; everything below is development
tooling, declared in `[dependency-groups] dev` in `pyproject.toml`.

```sh
git clone https://github.com/Stoops-ML/colourings
cd colourings
python -m pip install -e . --group dev
```

`uv sync` works too, and is what the lock file is for. CI installs with pip,
so the command above is the one guaranteed to match it.

## Running what CI runs

Every check below is a CI job. Running them locally is the whole story — there
is nothing CI does that you cannot reproduce.

```sh
python -m pytest                       # tests, including doctests
python -m pytest --cov colourings      # tests, with the 100% coverage gate
python -m ruff check                   # lint
python -m ruff format --diff           # formatting, without rewriting anything
python -m ty check                     # types
python -m sphinx -W -b html docs docs/_build/html   # docs, warnings fatal
zizmor .github/                        # workflow and Dependabot audit
python -m build .                      # build the wheel and the sdist
python -m twine check --strict dist/*  # metadata, as the index will read it
```

`python -m ruff format` (no `--diff`) applies the formatting rather than
reporting it.

Property tests run under Hypothesis at its default hundred examples per test,
which is what CI does and is a couple of seconds. Before a release, or after
touching a conversion, run twenty times as many:

```sh
python -m pytest --hypothesis-profile=deep
```

A failure prints the shrunk input that reproduces it, and Hypothesis remembers
that input in `.hypothesis/` — so once it has found a counter-example, the
plain `pytest` run reproduces it too, until it passes.

Two pytest settings are worth knowing about, both in `pyproject.toml`:

- `filterwarnings = ["error"]` — a warning fails the suite. If a change makes
  Python warn, that is a result, not noise.
- `--doctest-modules` — every example in a docstring is executed. An example
  that prints something must print exactly that.

## What a change needs

- **A test.** New behaviour needs a test that fails without the change. Fixed
  behaviour needs a test that reproduces the bug first. Coverage is gated at
  100% of statements and branches, so an untested line will fail CI, but the
  gate is a floor rather than the goal: a test that only executes a line
  without asserting anything about it passes the gate and catches nothing.

  `pytest.raises` needs a `match=`, and ruff's `PT011` enforces it. Every
  error this package raises derives from `ValueError`, so a bare
  `pytest.raises(ValueError)` also passes on a `ValueError` raised by a typo
  in the test itself. A distinctive fragment of the message is enough; drop a
  trailing full stop rather than escaping it.

  There are three kinds of test here and they are not interchangeable.
  `tests/test_*.py` pin specific behaviour. `tests/test_properties.py` sweeps a
  sample chosen deliberately — the gamut surface, a coarse interior grid, and
  every named colour — because that is where a whole class of bug was found
  once. `tests/test_hypothesis.py` states properties over generated input and
  lets Hypothesis look for the counter-example. A new invariant usually belongs
  in the third; a specific colour that once went wrong belongs in the first.
- **Docstrings in numpydoc style**, with `Parameters`, `Returns` and `Raises`
  sections. Sphinx is configured for numpydoc only
  (`napoleon_google_docstring = False`), so a Google-style docstring will be
  rendered as a paragraph of prose.
- **Documentation, when the change is visible from outside.** `README.md` is
  the reference for behaviour; `docs/` is generated from the docstrings.
- **A conventional-commit message.** `feat:`, `fix:`, `docs:`, `ci:`,
  `build:`, `style:`, `refactor:`, `test:`, `perf:` or `chore:`, with a `!`
  or a `BREAKING CHANGE:` trailer for anything that breaks. This is not
  decoration: commitizen builds the changelog and derives the next version
  number from these prefixes, so a commit with an unrecognised prefix is
  dropped from the changelog silently.

Say *why* in the commit message, not just what — the diff already says what.

## Colour science, constants and correctness

Much of this package is arithmetic against published standards, where a wrong
constant produces plausible output rather than an error. That is the failure
mode this project takes most seriously, and it shapes two rules:

- **Verify against the standard, or against a property, rather than against
  what the code currently prints.** A test recording today's output only pins
  the bug in place. Symmetry, round-trip identity, monotonicity and known
  anchors (black against white is a contrast ratio of exactly 21) all survive
  a refactor and catch a wrong constant.
- **If a constant cannot be confirmed, the function raises instead.** Several
  features are deliberately absent for this reason. Adding one means bringing
  the reference with it — cite the standard, the paper or the specification in
  the pull request.

## Style

- Ruff decides formatting and import order. Do not hand-format around it.
- Comments explain *why*. The code says what it does; a comment restating that
  is noise, and will be removed.
- Public API surface is deliberate. The top-level exports are pinned by a test,
  so widening them is a decision rather than a drift.

## Reporting a bug

Open an issue with the version of `colourings`, your Python version and
platform, and the smallest snippet that reproduces the problem. For anything
involving a colour value, include both the input and the output you got, and
say what you expected instead — "the colour is wrong" is hard to act on, and
"`Color('#336699').lab` returns L=41.6, I expect 41.2 per CIE 15:2004" is not.
