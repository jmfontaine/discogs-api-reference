"""Convert the Discogs API reference page into one Markdown file per section."""

from __future__ import annotations

import re
from html import escape
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify

HEADER_LINE_RE = re.compile(r"^[A-Za-z][A-Za-z-]*: ")
ENDPOINT_ROUTE_RE = re.compile(r"^`/[^`\n]+`$", re.MULTILINE)
REQUIRED_PAGE_SLUGS = frozenset({"authentication", "database", "home"})
PAGE_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Upstream <h1> text names the output file, so it must be a safe single path
# component: no empty value, no separator, no leading dot, no traversal.
PAGE_TITLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '()&,-]*$")
MARKDOWN_FRAGMENT_RE = re.compile(r"\]\(([^)#]+\.md)#([^)]+)\)")
WHITESPACE_RE = re.compile(r"\s*\n\s*")


class RenderError(Exception):
    """The HTML is not a Discogs API reference this tool can convert."""


def _attribute(tag: Tag, name: str) -> str:
    value = tag.get(name)
    if value is None:
        return ""
    return value if isinstance(value, str) else " ".join(value)


def _decode_cf_email(encoded: str) -> str:
    """Undo Cloudflare's XOR email obfuscation."""
    key = int(encoded[:2], 16)
    return "".join(
        chr(int(encoded[index : index + 2], 16) ^ key)
        for index in range(2, len(encoded), 2)
    )


def _title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _page_filename(title: str) -> str:
    """Reject upstream page titles that are not safe path components."""
    if not PAGE_TITLE_RE.match(title):
        msg = f"unsafe documentation page title: {title!r}"
        raise RenderError(msg)
    return f"{title}.md"


def _rewrite_page_link(href: str) -> str:
    """Turn the site's JavaScript routes into relative Markdown links."""
    if not href.startswith("#page:"):
        return href
    page, separator, fragment = href.removeprefix("#page:").partition(",header:")
    if not page:
        return href
    anchor = f"#{fragment}" if separator else ""
    return f"{quote(f'{_title(page)}.md')}{anchor}"


def _language(pre: Tag) -> str:
    code = pre.find("code")
    if isinstance(code, Tag):
        for class_name in _attribute(code, "class").split():
            if class_name.startswith("language-"):
                language = class_name.removeprefix("language-")
                return "" if language == "no-highlight" else language
    text = pre.get_text().lstrip()
    if text.startswith(("{", "[")):
        return "json"
    return "http" if HEADER_LINE_RE.match(text) else ""


def _collapse_whitespace(node: Tag) -> None:
    """Fold source line breaks outside code blocks, as a browser does.

    The page's templates break inline content over several lines, which
    Markdown would otherwise keep as stray blank-looking lines and split
    markers such as ``**Response `200`**``.
    """
    for text in node.find_all(string=WHITESPACE_RE):
        if isinstance(text, NavigableString) and not text.find_parent("pre"):
            text.replace_with(WHITESPACE_RE.sub(" ", str(text)))


def _promote_action_names(node: Tag) -> None:
    """Turn each endpoint's screen-reader name into a heading above it."""
    for section in node.find_all("section", id=True):
        name = section.find("span", class_="sr-only-action-name")
        if not isinstance(name, Tag):
            continue
        heading = BeautifulSoup("", "html.parser").new_tag("h4")
        heading.string = name.get_text(strip=True)
        name.decompose()
        section.insert(0, heading)


def _prepare_page(node: Tag) -> None:
    """Remove site UI while preserving the reference content."""
    for element in node.select(
        "a.btn-default, a.permalink, button, div.clearfix, i.fa, "
        "[style*='display: none']"
    ):
        element.decompose()
    for divider in node.find_all("hr", recursive=False):
        divider.decompose()
    for line_break in node.select("pre br"):
        line_break.replace_with("\n")
    for link in node.find_all("a"):
        if "__cf_email__" in _attribute(link, "class").split():
            link.replace_with(_decode_cf_email(_attribute(link, "data-cfemail")))
        elif href := _attribute(link, "href"):
            link["href"] = _rewrite_page_link(href)
    _promote_action_names(node)
    _collapse_whitespace(node)


def _add_source_anchors(text: str, node: Tag) -> str:
    """Keep the source IDs that rewritten cross-page links point to."""
    anchors: dict[str, list[str]] = {}
    for heading in node.find_all(re.compile(r"^h[1-6]$")):
        if identifier := _attribute(heading, "id"):
            marker = f"{'#' * int(heading.name[1])} {heading.get_text(strip=True)}"
            anchors.setdefault(marker, []).append(identifier)
    for section in node.find_all("section", id=True):
        heading = section.find("h4", recursive=False)
        if isinstance(heading, Tag):
            marker = f"#### {heading.get_text(strip=True)}"
        else:
            method = section.find("a", class_="btn-xs")
            if not isinstance(method, Tag) or not _attribute(method, "href"):
                continue
            marker = f"[{method.get_text(strip=True)}]({_attribute(method, 'href')})"
        anchors.setdefault(marker, []).append(_attribute(section, "id"))

    output: list[str] = []
    for line in text.splitlines():
        if identifiers := anchors.get(line):
            output.extend(
                (f'<a id="{escape(identifiers.pop(0), quote=True)}"></a>', "")
            )
        output.append(line)
    return "\n".join(output)


def _page_nodes(soup: BeautifulSoup) -> list[tuple[str, Tag]]:
    """Validate and return each top-level page container with its title."""
    pages: list[tuple[str, Tag]] = []
    slugs: set[str] = set()
    titles: set[str] = set()
    for node in soup.select("div.page-section[data-page]"):
        if node.find_parent("div", class_="page-section"):
            continue
        slug = _attribute(node, "data-page")
        heading = node.find("h1")
        if not PAGE_SLUG_RE.match(slug) or not isinstance(heading, Tag):
            msg = f"a documentation page has no valid slug or title: {slug!r}"
            raise RenderError(msg)
        title = heading.get_text(strip=True)
        if slug in slugs or title in titles:
            msg = f"duplicate documentation page: {slug!r}, {title!r}"
            raise RenderError(msg)
        slugs.add(slug)
        titles.add(title)
        pages.append((title, node))

    if len(pages) < 2:
        msg = (
            "the HTML contains fewer than two documentation pages; "
            "it is not the Discogs API reference, or its layout changed"
        )
        raise RenderError(msg)
    if missing := REQUIRED_PAGE_SLUGS - slugs:
        msg = f"the HTML lacks required pages: {', '.join(sorted(missing))}"
        raise RenderError(msg)
    return pages


def _validate_fragment_links(pages: dict[str, str]) -> None:
    """Require every cross-page fragment to name an anchor that exists."""
    missing: list[str] = []
    for source, text in pages.items():
        for target, fragment in MARKDOWN_FRAGMENT_RE.findall(text):
            target_text = pages.get(unquote(target))
            anchor = f'<a id="{escape(fragment, quote=True)}"></a>'
            if target_text is None or anchor not in target_text:
                missing.append(f"{source}: {target}#{fragment}")
    if missing:
        msg = "links point to missing anchors:\n  " + "\n  ".join(sorted(missing))
        raise RenderError(msg)


def render_pages(html: str) -> dict[str, str]:
    """Convert the reference page to Markdown, keyed by output file name."""
    soup = BeautifulSoup(html, "html.parser")
    pages: dict[str, str] = {}
    for title, node in _page_nodes(soup):
        _prepare_page(node)
        text = markdownify(
            str(node),
            bullets="-",
            code_language_callback=_language,
            heading_style="ATX",
            newline_style="BACKSLASH",
        )
        text = _add_source_anchors(text, node)
        text = "\n".join(line.rstrip() for line in text.splitlines())
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        pages[_page_filename(title)] = f"{text}\n"
    if not any(ENDPOINT_ROUTE_RE.search(text) for text in pages.values()):
        msg = "the HTML contains no endpoint routes"
        raise RenderError(msg)
    _validate_fragment_links(pages)
    return pages
