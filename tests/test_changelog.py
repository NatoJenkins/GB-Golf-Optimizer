"""Tests for the changelog parser and the /changelog route."""
import pytest


# ---------------------------------------------------------------------------
# Tests: gbgolf.changelog.get_latest_version
# ---------------------------------------------------------------------------

def test_get_latest_version_picks_topmost_entry(tmp_path):
    """Returns the version of the topmost ## [X.Y.Z] heading."""
    from gbgolf.changelog import get_latest_version

    f = tmp_path / "CHANGELOG.md"
    f.write_text(
        "# Changelog\n\n"
        "## [1.2.2] — 2026-04-29\n"
        "### Fixed\n- something\n\n"
        "## [1.2.1] — 2026-04-28\n"
        "### Added\n- something else\n",
        encoding="utf-8",
    )
    assert get_latest_version(str(f)) == "1.2.2"


def test_get_latest_version_handles_multiple_entries(tmp_path):
    """With many entries, returns only the topmost (newest)."""
    from gbgolf.changelog import get_latest_version

    f = tmp_path / "CHANGELOG.md"
    f.write_text(
        "## [3.0.0] — 2027-01-01\n\n"
        "## [2.5.1] — 2026-12-31\n\n"
        "## [2.0.0] — 2026-06-01\n",
        encoding="utf-8",
    )
    assert get_latest_version(str(f)) == "3.0.0"


def test_get_latest_version_missing_file_returns_unknown(tmp_path):
    """A missing file does not raise — returns 'unknown' so the app keeps serving."""
    from gbgolf.changelog import get_latest_version, UNKNOWN_VERSION

    missing = tmp_path / "does_not_exist.md"
    assert get_latest_version(str(missing)) == UNKNOWN_VERSION


def test_get_latest_version_no_version_headings_returns_unknown(tmp_path):
    """A file with no '## [X.Y.Z]' headings returns 'unknown' rather than raising."""
    from gbgolf.changelog import get_latest_version, UNKNOWN_VERSION

    f = tmp_path / "CHANGELOG.md"
    f.write_text("# Changelog\n\nNo version entries here yet.\n", encoding="utf-8")
    assert get_latest_version(str(f)) == UNKNOWN_VERSION


def test_get_latest_version_default_path_reads_repo_changelog():
    """With no argument, parses the project's actual CHANGELOG.md and returns 1.2.2."""
    from gbgolf.changelog import get_latest_version

    # Source of truth — should match the topmost entry in the committed CHANGELOG.md
    assert get_latest_version() == "1.2.2"


# ---------------------------------------------------------------------------
# Tests: /changelog route
# ---------------------------------------------------------------------------

@pytest.fixture
def client(app):
    return app.test_client()


def test_changelog_route_returns_200(client):
    """GET /changelog returns 200 and renders the page."""
    response = client.get("/changelog")
    assert response.status_code == 200


def test_changelog_route_contains_version(client):
    """Rendered changelog page includes the latest version string."""
    response = client.get("/changelog")
    html = response.data.decode("utf-8")
    assert "1.2.2" in html


def test_changelog_route_renders_markdown_to_html(client):
    """Markdown headings/lists render as HTML, not raw '##' or '-' tokens."""
    response = client.get("/changelog")
    html = response.data.decode("utf-8")

    # Keep-a-Changelog uses ## for version entries; rendered output must be an <h2>
    assert "<h2>" in html, "Expected rendered <h2> for the changelog version heading"
    # Not the raw markdown token
    assert "## [1.2.2]" not in html, "Raw markdown leaked into the rendered HTML"


# ---------------------------------------------------------------------------
# Tests: header injection on the optimizer home page
# ---------------------------------------------------------------------------

def test_optimizer_home_renders_version_in_header(client):
    """GET / shows the version string from the context processor in the page header."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "v1.2.2" in html, "Header should render the version as 'v1.2.2' (from CHANGELOG.md)"
