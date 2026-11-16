"""Build a local Markdown copy of the Discogs API reference"""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("discogs-api-reference")

__all__ = ["__version__"]
