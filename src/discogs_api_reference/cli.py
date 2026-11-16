"""Command-line interface for discogs-api-reference."""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import discogs_api_reference
from discogs_api_reference._fetch import DOCS_URL, FetchError, fetch_html
from discogs_api_reference._render import RenderError, render_pages

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

DEFAULT_OUTPUT_DIR = Path("reference/discogs_api")
# Written next to the pages, so --write deletes only files in a directory this
# tool manages, never the Markdown of a directory passed by mistake.
MARKER = ".discogs-api-reference"
MARKER_TEXT = (
    "Written by discogs-api-reference. For local use only: "
    "do not commit or share these files.\n"
)
DESCRIPTION = """\
Build a local Markdown copy of the Discogs API reference
(https://www.discogs.com/developers), one file per section.

Without --write, nothing is written: the command only reports which files
would change. The copy is for local use only; never commit or share it.
"""
# Exit codes: 1 is reserved for --check finding differences.
EXIT_ERROR = 2


def _diff(name: str, old: str, new: str) -> list[str]:
    return list(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{name}",
            tofile=f"b/{name}",
        )
    )


def _counts(diff: Iterable[str]) -> tuple[int, int]:
    added = removed = 0
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="discogs-api-reference",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=discogs_api_reference.__version__,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="exit with status 1 when the local copy differs",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="replace the local copy; required to change any file",
    )
    parser.add_argument(
        "--diff", action="store_true", help="print a unified diff for each change"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"directory of the local copy (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--from-html",
        type=Path,
        metavar="PATH",
        help="convert a page saved from a browser instead of downloading it",
    )
    return parser


def _write(output_dir: Path, pages: dict[str, str], changes: list[str]) -> int:
    """Apply *changes*: write each page in *pages*, delete each other name."""
    marker = output_dir / MARKER
    stale = [name for name in changes if name not in pages]
    if stale and not marker.exists():
        print(
            f"error: {output_dir} holds Markdown files this tool did not write "
            f"({', '.join(stale)}) and no {MARKER} file. Delete them yourself, "
            "or pick another directory. Nothing was written.",
            file=sys.stderr,
        )
        return EXIT_ERROR
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in changes:
        path = output_dir / name
        if name in pages:
            path.write_text(pages[name], encoding="utf-8")
        else:
            path.unlink()
    marker.write_text(MARKER_TEXT, encoding="utf-8")
    print(f"\nWrote {len(changes)} file(s) to {output_dir}.")
    return 0


def _run(args: argparse.Namespace) -> int:
    if args.from_html:
        html = args.from_html.read_text(encoding="utf-8")
        source = str(args.from_html)
    else:
        html = fetch_html()
        source = DOCS_URL
    pages = render_pages(html)
    output_dir: Path = args.output_dir
    existing = {path.name: path for path in sorted(output_dir.glob("*.md"))}
    print(f"Source: {source} ({len(html):,} bytes, {len(pages)} pages)")

    changes: list[str] = []
    diffs: list[list[str]] = []
    for name, new in sorted(pages.items()):
        path = existing.pop(name, None)
        old = path.read_text(encoding="utf-8") if path else ""
        if old == new:
            print(f"  unchanged  {name}")
            continue
        diff = _diff(name, old, new)
        added, removed = _counts(diff)
        print(f"  {'updated' if path else 'new':<9}  {name}  +{added} -{removed}")
        changes.append(name)
        diffs.append(diff)
    for name, path in existing.items():
        diff = _diff(name, path.read_text(encoding="utf-8"), "")
        print(f"  removed    {name}  -{_counts(diff)[1]}")
        changes.append(name)
        diffs.append(diff)

    if args.diff:
        for diff in diffs:
            print(f"\n{''.join(diff)}", end="")

    if not changes:
        print(f"\n{output_dir} matches the Discogs API reference.")
        return 0
    if args.check:
        print(f"\n{len(changes)} file(s) differ.", file=sys.stderr)
        return 1
    if not args.write:
        print(f"\n{len(changes)} file(s) differ, none written. Rerun with --write.")
        return 0
    return _write(output_dir, pages, changes)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        status = _run(args)
    except (FetchError, RenderError) as error:
        print(f"error: {error}. Nothing was written.", file=sys.stderr)
        status = EXIT_ERROR
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        status = EXIT_ERROR
    sys.exit(status)
