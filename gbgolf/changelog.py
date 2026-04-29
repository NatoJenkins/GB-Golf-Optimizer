"""Changelog parsing helpers.

Single source of truth for the application version: the topmost ``## [X.Y.Z]``
heading in ``CHANGELOG.md`` at the repo root. The Flask context processor in
``gbgolf.web.__init__`` injects the parsed version into every template.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

# CHANGELOG.md lives at the repo root, two levels above this file.
_CHANGELOG_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "CHANGELOG.md")
)

# Matches a Keep-a-Changelog version heading: "## [1.2.1]" or "## [1.2.0] — ..."
# Captures only the bracketed version token (digits and dots).
_VERSION_HEADING_RE = re.compile(r"^##\s*\[(\d+(?:\.\d+)*)\]")

UNKNOWN_VERSION = "unknown"


def get_latest_version(path: str | None = None) -> str:
    """Return the topmost version from ``CHANGELOG.md``.

    A missing or unparseable file falls back to ``"unknown"`` rather than
    raising — a broken changelog must not 500 the whole app.

    Args:
        path: Optional override for the changelog file location. When ``None``,
            uses ``CHANGELOG.md`` at the repo root.
    """
    p = path if path is not None else _CHANGELOG_PATH
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                m = _VERSION_HEADING_RE.match(line)
                if m:
                    return m.group(1)
    except OSError:
        return UNKNOWN_VERSION
    return UNKNOWN_VERSION


def read_changelog_text(path: str | None = None) -> str:
    """Return the raw markdown text of ``CHANGELOG.md`` for rendering.

    Returns an empty string if the file is missing — the route handler can
    decide whether to render a friendly empty-state or a fallback message.
    """
    p = path if path is not None else _CHANGELOG_PATH
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


__all__ = ["get_latest_version", "read_changelog_text", "UNKNOWN_VERSION"]
