"""Run the README's examples, and check the outputs they claim.

``--doctest-modules`` covers every ``>>>`` in the package, but the README's
examples are fenced blocks with their expected values in comments -- written
for a reader rather than for a doctest runner -- and nothing checked them.

Two were wrong when this was added. One block raised ``NameError``, because the
last value of a printed scale had wrapped onto its own line and lost its ``#``,
leaving a bare name in the code. Another carried a blend result that had been
written from expectation rather than from running it.

The blocks execute in order in one shared namespace, because that is how they
are written to be read: a later block uses the ``Color`` an earlier one
imported. ``tkinter.Tk`` is patched, since one block calls
:meth:`~colourings.colour.Color.preview` and an unpatched window blocks until
somebody closes it.

A trailing comment on a line of code means "this is what that produces", and
one of these three forms:

- the value exactly, as ``repr`` gives it, or as ``print`` writes it;
- the value with ``...`` standing in for digits that were elided;
- a number rounded to as many decimal places as the comment shows.

Any of them may be followed by a comma and a remark. Prose that is not an
expected value goes on its own line above the code, where this ignores it.

A statement that prints something and is followed by whole-line comments
matches when any one of them is that output with its whitespace flattened,
which is how the multi-line ones are written.
"""

import ast
import contextlib
import io
import pathlib
import re
import tokenize
from unittest import mock

import pytest

README = pathlib.Path(__file__).resolve().parent.parent / "README.md"

## A fence with whatever prefix its surroundings give it: `> ` in a
## blockquote, spaces in a list item, nothing at the top level. The prefix is
## stripped from every body line, or the body is not valid Python.
##
## Anchoring at the line start alone silently skipped indented fences, so a
## broken example inside a list item passed -- found by adding one.
_FENCE = re.compile(
    r"^(?P<prefix>[ \t]*(?:> ?)?)```python\n(?P<body>.*?)^(?P=prefix)```",
    re.S | re.M,
)
_ELISION = "..."
## What separates a value from a remark about it.
_REMARK = re.compile(r", | -- ")


def _blocks(text):
    """Every python block, as ``(first line number, source)``."""
    for match in _FENCE.finditer(text):
        prefix, body = match.group("prefix"), match.group("body")
        if prefix:
            body = "".join(
                line[len(prefix) :] if line.startswith(prefix) else line.lstrip()
                for line in body.splitlines(keepends=True)
            )
        yield text.count("\n", 0, match.start()) + 1, body


def _trailing_comments(body):
    """Line number to comment text, for comments that follow code.

    Tokenized rather than matched: ``Color("#ff0000")`` has a ``#`` inside a
    string literal, and a regex takes that for the start of a comment.
    """
    found = {}
    for token in tokenize.generate_tokens(io.StringIO(body).readline):
        if token.type == tokenize.COMMENT and token.start[1] > 0:
            found[token.start[0]] = token.string.lstrip("#").strip()
    return found


def _decimals(text):
    """How many decimal places a number is written to, or None."""
    match = re.fullmatch(r"[+-]?\d+\.(\d+)", text)
    return len(match.group(1)) if match else None


## A trailing comment is an expected value when it begins like one: a number,
## a quote, a bracket, `True`/`False`/`None`, or a repr like `HSL(...)`.
## Anything else labels the *input*, of which the README has a dozen --
## `Color("rgb(255, 0, 0)")  # legacy commas` names the syntax, and the value
## is `<Color red>` either way. The cost is that an expectation phrased as
## prose is skipped silently, which the count guard below covers.
_VALUE_LIKE = re.compile(r"""[-+]?\d|['"<\[({]|(?:True|False|None)|\w+\(""")


def _looks_like_a_value(comment):
    return _VALUE_LIKE.match(comment) is not None


def _claims_exactly(comment, actual):
    """Whether ``comment`` is ``actual``, allowing elision and rounding."""
    if comment == actual:
        return True
    if _ELISION in comment:
        pattern = ".*?".join(re.escape(part) for part in comment.split(_ELISION))
        if re.fullmatch(pattern, actual):
            return True
    ## A number rounded to the precision it shows.
    places = _decimals(comment)
    if places is not None:
        try:
            return round(float(actual), places) == float(comment)
        except ValueError:
            return False
    return False


def _claims(comment, actual):
    """Whether ``comment`` claims ``actual``.

    A remark may follow the value, after a comma or a dash; the README uses
    both. Values contain commas of their own --
    ``HSL(hue=0.0, saturation=100.0, ...)`` -- so rather than guessing where
    the value ends, every cut is tried.
    """
    candidates = [comment]
    candidates += [comment[: m.start()] for m in _REMARK.finditer(comment)]
    return any(_claims_exactly(candidate, actual) for candidate in candidates)


def _following_comments(lines, statement):
    """The whole-line comments immediately after a statement."""
    out = []
    index = statement.end_lineno
    while index < len(lines) and lines[index].lstrip().startswith("#"):
        out.append(lines[index].lstrip().lstrip("#").strip())
        index += 1
    return out


def _walk():
    """Execute the README and return what did not run and what did not match."""
    text = README.read_text(encoding="utf-8")
    namespace = {}
    errors, mismatches, checked = [], [], 0

    with mock.patch("tkinter.Tk"):
        for start, body in _blocks(text):
            lines = body.splitlines()
            trailing = _trailing_comments(body)
            try:
                statements = ast.parse(body).body
            except SyntaxError as exc:
                errors.append(f"README.md:{start} does not parse: {exc}")
                continue
            for statement in statements:
                line = start + statement.end_lineno - 1
                printed = io.StringIO()
                try:
                    with contextlib.redirect_stdout(printed):
                        exec(  # noqa: S102 -- the README is the input by design
                            compile(ast.Module([statement], []), str(README), "exec"),
                            namespace,
                        )
                ## Any failure at all is a failure of the README.
                except Exception as exc:
                    errors.append(
                        f"README.md:{line} raised {type(exc).__name__}: {exc}"
                    )
                    continue

                output = printed.getvalue().strip()
                comment = trailing.get(statement.end_lineno)
                if (
                    comment is not None
                    and isinstance(statement, ast.Expr)
                    and _looks_like_a_value(comment)
                ):
                    actual = output or repr(
                        eval(  # noqa: S307 -- ditto
                            compile(
                                ast.Expression(statement.value), str(README), "eval"
                            ),
                            namespace,
                        )
                    )
                    checked += 1
                    if not _claims(comment, actual):
                        mismatches.append(
                            f"README.md:{line} says {comment!r}, produces {actual!r}"
                        )
                elif output:
                    following = _following_comments(lines, statement)
                    if following:
                        flat = " ".join(output.split())
                        checked += 1
                        if not any(" ".join(c.split()) == flat for c in following):
                            mismatches.append(
                                f"README.md:{line} prints {flat!r}, "
                                f"claimed {following!r}"
                            )
    return errors, mismatches, checked


@pytest.fixture(scope="module")
def readme():
    return _walk()


def test_every_readme_block_runs(readme):
    """A block that does not run is the failure this was written for: the
    NameError it found had been in the README through several releases."""
    errors, _, _ = readme
    assert not errors, "\n".join(errors)


def test_the_readme_output_is_what_it_claims(readme):
    _, mismatches, _ = readme
    assert not mismatches, "\n".join(mismatches)


def test_enough_of_the_readme_is_actually_checked(readme):
    """Guard the guard. Every rule here is permissive by design -- it has to
    be, to read comments written for a person -- so the risk is a change that
    quietly stops recognising anything. This pins the count."""
    _, _, checked = readme
    assert checked >= 60


@pytest.mark.parametrize(
    ("prefix", "label"),
    [("", "top level"), ("> ", "blockquote"), ("  ", "list item")],
)
def test_a_fenced_block_is_found_whatever_prefixes_it(prefix, label):
    """Checked directly rather than through the README, which need not always
    contain one of each -- and did not, which is how an indented fence went
    uncollected in the first place."""
    source = 'Color("red")  # <Color red>\n'
    fence = "```python"
    document = f"text\n\n{prefix}{fence}\n{prefix}{source}{prefix}```\n"
    found = list(_blocks(document))
    assert len(found) == 1, label
    assert found[0][1] == source, label


def test_the_readme_has_the_blocks_this_expects():
    """The other half of the same guard: a fence pattern that stopped matching
    would leave every test above passing on nothing."""
    text = README.read_text(encoding="utf-8")
    found = list(_blocks(text))
    assert len(found) >= 45
    ## At least one lives inside a blockquote, which needs its prefix removed.
    assert any(
        "```python" in line for line in text.splitlines() if line.startswith(">")
    )
