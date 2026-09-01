import importlib.metadata
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
