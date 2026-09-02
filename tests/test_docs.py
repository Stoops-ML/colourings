"""Run the examples in the README and the docs, and check what they claim.

``--doctest-modules`` covers every ``>>>`` in the package, but the prose
documentation writes its expected values in comments -- for a reader rather
than for a doctest runner -- and nothing checked them.

This has caught real breakage. Two README examples were wrong when the README
half of this was added: one block raised ``NameError``, and one carried a blend
result written from expectation rather than from running it. The docs, which
were not covered until they were, claimed ``Color(pick_for="user:123").web``
was ``#010000`` -- a pre-2.0 value left behind when ``pick_for`` was changed to
pick the same colour in every process.

Both markdown fences and reStructuredText ``code-block`` directives are read,
so a page keeps its examples checked wherever it lives. Each document gets its
own namespace and its blocks run in order, because that is how a page is read:
a later block uses what an earlier one imported. ``tkinter.Tk`` is patched,
since one page calls :meth:`~colourings.colour.Color.preview` and an unpatched
window blocks until somebody closes it.

A trailing comment on a line of code means "this is what that produces", in one
of three forms:

- the value exactly, as ``repr`` gives it, or as ``print`` writes it;
- the value with ``...`` standing in for digits that were elided;
- a number rounded to as many decimal places as the comment shows.

Any of them may be followed by a comma or a dash and a remark. Prose that is
not an expected value goes on its own line above the code, where this ignores
it. A statement that prints something and is followed by whole-line comments
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

ROOT = pathlib.Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
DOCS = ROOT / "docs"

## A markdown fence with whatever prefix its surroundings give it: `> ` in a
## blockquote, spaces in a list item, nothing at the top level. The prefix is
## stripped from every body line, or the body is not valid Python.
##
## Anchoring at the line start alone silently skipped indented fences, so a
## broken example inside a list item passed -- found by adding one.
_FENCE = re.compile(
    r"^(?P<prefix>[ \t]*(?:> ?)?)```python\n(?P<body>.*?)^(?P=prefix)```",
    re.S | re.M,
)
_DIRECTIVE = re.compile(r"^(?P<indent>[ \t]*)\.\. code-block:: python\s*$")
## Directive options -- `:linenos:`, `:emphasize-lines:` -- sit between the
## directive and its body.
_OPTION = re.compile(r"^[ \t]*:[\w-]+:")
_ELISION = "..."
## What separates a value from a remark about it.
_REMARK = re.compile(r", | -- ")


def _markdown_blocks(text):
    """Every fenced python block, as ``(first line number, source)``."""
    for match in _FENCE.finditer(text):
        prefix, body = match.group("prefix"), match.group("body")
        if prefix:
            body = "".join(
                line[len(prefix) :] if line.startswith(prefix) else line.lstrip()
                for line in body.splitlines(keepends=True)
            )
        yield text.count("\n", 0, match.start()) + 1, body


def _rst_blocks(text):
    """Every ``code-block:: python`` body, as ``(first line number, source)``.

    Parsed line by line rather than by regex. An indented literal block ends
    at the first non-blank line indented no further than its directive, which
    is a rule about the lines around it and not a pattern within them.
    """
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        match = _DIRECTIVE.match(lines[index].rstrip("\n"))
        if match is None:
            index += 1
            continue
        opening = len(match.group("indent"))
        index += 1
        while index < len(lines) and (
            _OPTION.match(lines[index]) or not lines[index].strip()
        ):
            index += 1
        body, start = [], index
        while index < len(lines):
            line = lines[index]
            if line.strip() and len(line) - len(line.lstrip()) <= opening:
                break
            body.append(line)
            index += 1
        while body and not body[-1].strip():
            body.pop()
        if not body:
            continue
        pad = min(len(x) - len(x.lstrip()) for x in body if x.strip())
        yield start + 1, "".join(line[pad:] if line.strip() else "\n" for line in body)


def _blocks(path, text):
    reader = _rst_blocks if path.suffix == ".rst" else _markdown_blocks
    return reader(text)


def _documents():
    """Every file whose examples are checked, README first."""
    return [README, *sorted(DOCS.glob("*.rst"))]


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
## a quote, a bracket, `True`/`False`/`None`, a repr like `HSL(...)`, or a bare
## hex colour. Anything else labels the *input*:
## `Color("rgb(255, 0, 0)")  # legacy commas` names the syntax, and the value
## is the same either way. The cost is that an expectation phrased as prose is
## skipped silently, which the count guard below covers.
##
## The hex alternative was missing at first, so `print(c.hex)  # #00f` was
## skipped in silence -- and a bare hex is the value in this package most
## easily written from expectation rather than from running it. Adding it found
## a docs example still claiming a pre-2.0 `pick_for` colour.
_VALUE_LIKE = re.compile(
    r"""[-+]?\d|['"<\[({]|(?:True|False|None)|\w+\(|\#[0-9a-fA-F]{3,8}\b"""
)


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

    A remark may follow the value, after a comma or a dash; both are used.
    Values contain commas of their own -- ``HSL(hue=0.0, saturation=100.0,
    ...)`` -- so rather than guessing where the value ends, every cut is tried.
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


def _walk_document(path):
    """Execute one document. Returns what did not run and what did not match."""
    name = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    namespace = {}
    errors, mismatches, checked = [], [], 0

    for start, body in _blocks(path, text):
        lines = body.splitlines()
        trailing = _trailing_comments(body)
        try:
            statements = ast.parse(body).body
        except SyntaxError as exc:
            errors.append(f"{name}:{start} does not parse: {exc}")
            continue
        for statement in statements:
            line = start + statement.end_lineno - 1
            printed = io.StringIO()
            try:
                with contextlib.redirect_stdout(printed):
                    exec(  # noqa: S102 -- the documentation is the input by design
                        compile(ast.Module([statement], []), name, "exec"),
                        namespace,
                    )
            ## Any failure at all is a failure of the documentation.
            except Exception as exc:
                errors.append(f"{name}:{line} raised {type(exc).__name__}: {exc}")
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
                        compile(ast.Expression(statement.value), name, "eval"),
                        namespace,
                    )
                )
                checked += 1
                if not _claims(comment, actual):
                    mismatches.append(
                        f"{name}:{line} says {comment!r}, produces {actual!r}"
                    )
            elif output:
                following = _following_comments(lines, statement)
                if following:
                    flat = " ".join(output.split())
                    ## One comment holding the whole output, or a comment per
                    ## line of it. A statement printing five error messages
                    ## would otherwise need all five on one unreadable line.
                    claims = [" ".join(c.split()) for c in following]
                    checked += 1
                    if flat not in claims and " ".join(claims) != flat:
                        mismatches.append(
                            f"{name}:{line} prints {flat!r}, claimed {following!r}"
                        )
    return errors, mismatches, checked


@pytest.fixture(scope="module")
def walked():
    """Every document, executed once."""
    with mock.patch("tkinter.Tk"):
        return {path: _walk_document(path) for path in _documents()}


def test_every_documented_example_runs(walked):
    """A block that does not run is the failure this was written for: the
    NameError it found had been in the README through several releases."""
    errors = [error for result in walked.values() for error in result[0]]
    assert not errors, "\n".join(errors)


def test_the_documented_output_is_what_it_claims(walked):
    mismatches = [bad for result in walked.values() for bad in result[1]]
    assert not mismatches, "\n".join(mismatches)


def test_enough_of_the_documentation_is_actually_checked(walked):
    """Guard the guard. Every rule here is permissive by design -- it has to
    be, to read comments written for a person -- so the risk is a change that
    quietly stops recognising anything. This pins the count."""
    checked = sum(result[2] for result in walked.values())
    assert checked >= 170


def test_every_document_carries_examples_that_are_checked(walked):
    """A page whose examples all stopped being recognised would pass every
    test above in silence. Pages that are pure prose or autodoc are named,
    so that adding one is a decision rather than an omission."""
    PROSE_ONLY = {"docs/api.rst", "docs/changelog.rst"}
    unchecked = sorted(
        path.relative_to(ROOT).as_posix()
        for path, (_, _, checked) in walked.items()
        if not checked
    )
    assert unchecked == sorted(PROSE_ONLY), unchecked


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
    found = list(_markdown_blocks(document))
    assert len(found) == 1, label
    assert found[0][1] == source, label


def test_a_directive_block_ends_where_its_indentation_does():
    """The rst counterpart, and the case a regex got wrong: the block runs to
    the first line indented no further than the directive, and the prose that
    follows is not part of it."""
    document = (
        "Heading\n=======\n\n"
        ".. code-block:: python\n"
        "   :linenos:\n"
        "\n"
        '   Color("red")\n'
        "\n"
        '   Color("blue")\n'
        "\n"
        "Prose that follows.\n"
    )
    found = list(_rst_blocks(document))
    assert len(found) == 1
    assert found[0][1] == 'Color("red")\n\nColor("blue")\n'
    assert found[0][0] == 7


def test_a_nested_directive_block_keeps_its_own_indentation():
    """A code-block inside an admonition is indented, and dedenting to the
    directive rather than to the body would leave the source unparseable."""
    document = (
        ".. note::\n"
        "\n"
        "   .. code-block:: python\n"
        "\n"
        "      if True:\n"
        '          Color("red")\n'
    )
    found = list(_rst_blocks(document))
    assert len(found) == 1
    assert found[0][1] == 'if True:\n    Color("red")\n'


def test_only_python_blocks_are_collected():
    """``installation`` documents shell commands, which are not Python and
    must not be executed as though they were."""
    document = ".. code-block:: bash\n\n   pip install colourings\n"
    assert list(_rst_blocks(document)) == []


def test_the_documentation_has_the_blocks_this_expects():
    """The other half of the same guard: a pattern that stopped matching would
    leave every test above passing on nothing."""
    counts = {
        path.relative_to(ROOT).as_posix(): len(
            list(_blocks(path, path.read_text(encoding="utf-8")))
        )
        for path in _documents()
    }
    assert counts["README.md"] >= 1
    assert sum(counts.values()) >= 90
