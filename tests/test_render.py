from __future__ import annotations

import pytest
from reference_html import page, reference_html

from discogs_api_reference._render import RenderError, render_pages


def test_renders_one_file_per_page(html: str) -> None:
    pages = render_pages(html)

    assert sorted(pages) == ["Authentication.md", "Database.md", "Home.md"]
    database = pages["Database.md"].splitlines()
    # Consumers find endpoints by these lines: a route alone between backticks,
    # and a response marker on one line, as the SDK's coverage check does.
    assert "`/things/{thing_id}`" in database
    assert "- **Response `200`**" in database
    heading = database.index("#### Get Thing")
    assert database[heading - 2] == '<a id="database-thing-get"></a>'
    assert "Toggle" not in pages["Database.md"]


def test_keeps_cross_page_links_working(html: str) -> None:
    home = render_pages(html)["Home.md"]

    assert "[Get Thing](Database.md#database-thing-get)" in home
    assert "api@example.com" in home


def test_rejects_html_that_is_not_the_reference() -> None:
    challenge = "<html><head><title>Just a moment...</title></head></html>"

    with pytest.raises(RenderError, match="fewer than two"):
        render_pages(challenge)


def test_rejects_a_title_that_is_not_a_safe_file_name() -> None:
    html = reference_html(
        page("home", "Home"),
        page("authentication", "../Authentication"),
        page("database", "Database", "<code>/x</code>"),
    )

    with pytest.raises(RenderError, match="unsafe"):
        render_pages(html)


def test_rejects_a_link_to_a_missing_anchor() -> None:
    html = reference_html(
        page("home", "Home", '<a href="#page:database,header:gone">Gone</a>'),
        page("authentication", "Authentication"),
        page("database", "Database", "<p><code>/x</code></p>"),
    )

    with pytest.raises(RenderError, match=r"Database\.md#gone"):
        render_pages(html)
