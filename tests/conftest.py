from __future__ import annotations

import pytest
from reference_html import ENDPOINT, cf_email, page, reference_html


@pytest.fixture
def html() -> str:
    email = cf_email("api@example.com")
    home = page(
        "home",
        "Home",
        '<p>See <a href="#page:database,header:database-thing-get">Get Thing</a>'
        f' or write to <a class="__cf_email__" data-cfemail="{email}">'
        "[email protected]</a>.</p>",
    )
    return reference_html(
        home,
        page("authentication", "Authentication", "<p>Use a token.</p>"),
        page("database", "Database", ENDPOINT),
    )
