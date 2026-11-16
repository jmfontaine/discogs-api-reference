"""Download the Discogs API reference page."""

from __future__ import annotations

from curl_cffi import requests

import discogs_api_reference

DOCS_URL = "https://www.discogs.com/developers"
USER_AGENT = (
    f"discogs-api-reference/{discogs_api_reference.__version__} "
    "(+https://github.com/jmfontaine/discogs-api-reference)"
)
# KLUDGE: Cloudflare rejects every client whose TLS handshake does not look like
# a browser's, on every discogs.com page, so httpx, urllib and curl get a 403.
# curl_cffi replays a browser's handshake; the User-Agent still names this tool.
# Replace it if Discogs publishes the reference in a machine-readable form or
# lets identified tools through.
BROWSER_HANDSHAKES = ("chrome", "safari", "firefox")


class FetchError(Exception):
    """The reference page could not be downloaded."""


def fetch_html() -> str:
    """Download the reference page, trying each browser handshake in turn."""
    failures: list[str] = []
    for handshake in BROWSER_HANDSHAKES:
        try:
            response = requests.get(
                DOCS_URL,
                headers={"User-Agent": USER_AGENT},
                impersonate=handshake,
                timeout=60,
            )
        except requests.RequestsError as error:
            failures.append(f"{handshake}: {error}")
            continue
        if response.status_code == 200 and "Just a moment" not in response.text[:512]:
            return response.text
        failures.append(f"{handshake}: HTTP {response.status_code}")
    msg = (
        f"could not download {DOCS_URL} ({'; '.join(failures)}). "
        "Save the page from a browser and pass it with --from-html."
    )
    raise FetchError(msg)
