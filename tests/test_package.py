import importlib.metadata
import pathlib
import re
import subprocess
import sys

import pytest

import colourings


def test_version_matches_installed_metadata():
    """The version is declared in pyproject.toml and read back from there."""
    assert colourings.__version__ == importlib.metadata.version("colourings")


def test_version_is_resolved_lazily():
    """Reading the version must not be a cost every import pays.

    ``importlib.metadata`` takes longer to import than the whole of this
    package, so ``__init__`` defers it until someone asks for the version.
    """
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys\n"
            "before = 'importlib.metadata' in sys.modules\n"
            "import colourings\n"
            "print(before, 'importlib.metadata' in sys.modules)\n",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    before, after = result.stdout.split()
    if before == "True":
        pytest.skip("importlib.metadata was already loaded at interpreter startup")
    assert after == "False"


def test_unknown_package_attribute_raises():
    with pytest.raises(
        AttributeError, match="module 'colourings' has no attribute 'nope'"
    ):
        _ = colourings.nope


def test_missing_install_raises_an_import_error():
    """A caller can catch the uninstalled case as ImportError, as docs do."""
    assert issubclass(importlib.metadata.PackageNotFoundError, ImportError)


def test_every_exported_name_resolves():
    """A typo in ``__all__`` is invisible until someone writes ``import *``."""
    missing = [name for name in colourings.__all__ if not hasattr(colourings, name)]
    assert missing == []


def test_all_is_sorted_and_unique():
    """Kept sorted so additions land in one obvious place."""
    assert colourings.__all__ == sorted(set(colourings.__all__))


def test_the_public_surface_is_deliberate():
    """The conversion layer, the shape predicates and the CSS parser stay in
    their own modules. This pins that, so widening the top level is a decision
    rather than a drift."""
    assert set(colourings.__all__) == {
        "AmbiguousColorError",
        "Color",
        "ColorError",
        "Colour",
        "HSL_equivalence",
        "InvalidColorError",
        "RGB_color_picker",
        "RGB_equivalence",
        "UnknownColorError",
        "clear_caches",
        "color_scale",
        "colour_scale",
        "identify_color",
        "in_srgb_gamut",
        "make_color_factory",
    }


PYPROJECT = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
LICENSE = PYPROJECT.parent / "LICENSE.txt"
WORKFLOW = PYPROJECT.parent / ".github" / "workflows" / "workflow.yml"


@pytest.mark.skipif(not PYPROJECT.exists(), reason="running without the source tree")
def test_the_declared_licence_matches_the_licence_file():
    """Two files have to agree and nothing else makes them.

    Read as text rather than through importlib.metadata, which reports what
    was installed: that lags pyproject.toml until the package is rebuilt, so a
    change here would pass locally and only fail once someone reinstalled.
    The built metadata is checked in CI instead, where the build is fresh.
    """
    assert 'license = "BSD-3-Clause"' in PYPROJECT.read_text(encoding="utf-8")
    assert LICENSE.read_text(encoding="utf-8").startswith("BSD-3-Clause")


@pytest.mark.skipif(not PYPROJECT.exists(), reason="running without the source tree")
def test_the_typed_classifier_and_the_marker_agree():
    """py.typed is only useful if the index is told about it, and the
    classifier is only true if the marker actually ships."""
    assert '"Typing :: Typed"' in PYPROJECT.read_text(encoding="utf-8")
    assert (pathlib.Path(colourings.__file__).parent / "py.typed").exists()


def _declared_versions():
    """The Python versions pyproject.toml claims, from the classifiers."""
    return set(
        re.findall(
            r'"Programming Language :: Python :: (\d+\.\d+)"',
            PYPROJECT.read_text(encoding="utf-8"),
        )
    )


def _tested_versions():
    """The Python versions the test matrix actually runs.

    Scoped to the ``test`` job's own block, since the other jobs pin a single
    version of their own. Read with a regex rather than a YAML parser: this
    package has no runtime dependencies and a test-only PyYAML would be the
    first, for one list of strings.
    """
    text = WORKFLOW.read_text(encoding="utf-8")
    block = text[text.index("\n  test:\n") : text.index("\n  quality:\n")]
    return set(re.findall(r"'(\d+\.\d+)'", block))


@pytest.mark.skipif(
    not (PYPROJECT.exists() and WORKFLOW.exists()),
    reason="running without the source tree",
)
def test_the_versions_tested_are_the_versions_claimed():
    """Two lists that have to agree, and nothing else makes them.

    A version in the classifiers but not the matrix is a promise to the index
    that nothing checks. A version in the matrix but not the classifiers
    installs fine and then tells pip it is unsupported. Both are silent, and
    both have to be edited by hand, so they are pinned to each other here.
    """
    assert _declared_versions() == _tested_versions()


@pytest.mark.skipif(not PYPROJECT.exists(), reason="running without the source tree")
def test_requires_python_matches_the_oldest_version_claimed():
    """The floor is written twice -- once as a bound, once as a classifier."""
    oldest = min(_declared_versions(), key=lambda v: tuple(map(int, v.split("."))))
    assert f'requires-python = ">={oldest}"' in PYPROJECT.read_text(encoding="utf-8")
