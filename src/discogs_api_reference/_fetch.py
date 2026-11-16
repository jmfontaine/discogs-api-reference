"""Download the Discogs API reference page."""

from __future__ import annotations

from typing import TYPE_CHECKING

from curl_cffi import requests

import discogs_api_reference

if TYPE_CHECKING:
    from curl_cffi.requests import Response

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
# Cloudflare answers a rejected handshake with one of these and its challenge page.
REJECTION_STATUSES = frozenset({403, 503})


class FetchError(Exception):
    """The reference page could not be downloaded."""


def _is_rejection(response: Response) -> bool:
    return (
        response.status_code in REJECTION_STATUSES
        or "Just a moment" in response.text[:512]
    )


def fetch_html() -> str:
    """Download the reference page.

    Only a Cloudflare rejection moves on to the next browser handshake; any
    other failure, a redirect included, ends the run, so the tool never
    requests another address.
    """
    rejections: list[str] = []
    for handshake in BROWSER_HANDSHAKES:
        try:
            response = requests.get(
                DOCS_URL,
                allow_redirects=False,
                headers={"User-Agent": USER_AGENT},
                impersonate=handshake,
                timeout=60,
            )
        except requests.RequestsError as error:
            msg = f"could not download {DOCS_URL}: {error}"
            raise FetchError(msg) from error
        if _is_rejection(response):
            rejections.append(f"{handshake}: HTTP {response.status_code}")
            continue
        if response.status_code != 200:
            msg = f"could not download {DOCS_URL}: HTTP {response.status_code}"
            raise FetchError(msg)
        return response.text
    msg = (
        f"Cloudflare rejected every browser handshake for {DOCS_URL} "
        f"({'; '.join(rejections)}). Save the page from a browser and pass it "
        "with --from-html"
    )
    raise FetchError(msg)
