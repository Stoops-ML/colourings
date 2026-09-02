from __future__ import annotations

from datetime import datetime
from importlib import metadata

project = "colourings"
author = "Daniel Stoops"

## Read from the installed distribution rather than falling back to a
## placeholder. The fallback silently published "colourings 0.0.0" for as long
## as the version was unreadable; autodoc needs the package installed anyway,
## so a build that cannot find it should fail rather than mislabel itself.
release = metadata.version("colourings")
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "en"

html_theme = "furo"
html_title = f"{project} {release}"
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_class_signature = "mixed"
napoleon_google_docstring = False
napoleon_numpy_docstring = True

myst_enable_extensions = [
    "colon_fence",
]

copyright = f"{datetime.now().year}, {author}"
