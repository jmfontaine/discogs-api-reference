"""Command-line interface for discogs-api-reference."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import discogs_api_reference

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="discogs-api-reference",
        description=discogs_api_reference.__doc__,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=discogs_api_reference.__version__,
    )
    parser.parse_args(argv)
