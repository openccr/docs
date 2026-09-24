project = "openCCR Rebus Protocol"
author = "openCCR contributors"
copyright = "2026, openCCR contributors"

extensions = ["myst_parser"]
source_suffix = {".md": "markdown"}
root_doc = "index"

myst_heading_anchors = 6

html_title = "Rebus Protocol — openCCR"
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 5,
    "sticky_navigation": True,
    "titles_only": False,
}

html_static_path = ["_static"]
html_css_files = ["openccr.css"]

exclude_patterns = [
    "_build/**",
    ".venv-docs/**",
    ".worktrees/**",
    ".superpowers/**",
    ".claude/**",
    ".github/**",
    "docs/**",
    "superpowers/**",
    "ble/**",
    "README.md",
    "CONTRIBUTING.md",
    "SAFETY.md",
    "CLA.md",
    "LICENSE.md",
    "licenses/**",
]
