from __future__ import annotations

from importlib.metadata import version

import pytest

import discogs_api_reference
from discogs_api_reference.cli import main


def test_version_matches_installed_metadata() -> None:
    # Fails once __version__ is set by hand instead of read from the metadata.
    assert discogs_api_reference.__version__ == version("discogs-api-reference")


def test_cli_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out == f"{discogs_api_reference.__version__}\n"
