from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from discogs_api_reference import _fetch
from discogs_api_reference._fetch import FetchError, fetch_html
from discogs_api_reference.cli import MARKER, main

if TYPE_CHECKING:
    from pathlib import Path


def run(*args: str) -> int:
    with pytest.raises(SystemExit) as exit_info:
        main(list(args))
    code = exit_info.value.code
    assert isinstance(code, int)
    return code


@pytest.fixture
def saved(tmp_path: Path, html: str) -> Path:
    path = tmp_path / "developers.html"
    path.write_text(html, encoding="utf-8")
    return path


def test_reports_without_writing_by_default(saved: Path, tmp_path: Path) -> None:
    output = tmp_path / "reference"

    assert run("--from-html", str(saved), "--output-dir", str(output)) == 0
    assert not output.exists()


def test_write_then_check_finds_no_difference(saved: Path, tmp_path: Path) -> None:
    output = tmp_path / "reference"

    assert run("--from-html", str(saved), "--output-dir", str(output), "--write") == 0
    assert sorted(path.name for path in output.glob("*.md")) == [
        "Authentication.md",
        "Database.md",
        "Home.md",
    ]
    assert run("--from-html", str(saved), "--output-dir", str(output), "--check") == 0


def test_check_fails_when_a_page_differs(saved: Path, tmp_path: Path) -> None:
    output = tmp_path / "reference"
    run("--from-html", str(saved), "--output-dir", str(output), "--write")
    (output / "Home.md").write_text("edited\n", encoding="utf-8")

    assert run("--from-html", str(saved), "--output-dir", str(output), "--check") == 1


def test_write_removes_a_page_the_reference_dropped(
    saved: Path, tmp_path: Path
) -> None:
    output = tmp_path / "reference"
    run("--from-html", str(saved), "--output-dir", str(output), "--write")
    (output / "Old Section.md").write_text("gone upstream\n", encoding="utf-8")

    assert run("--from-html", str(saved), "--output-dir", str(output), "--write") == 0
    assert not (output / "Old Section.md").exists()


def test_write_never_deletes_files_it_did_not_write(
    saved: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "docs"
    output.mkdir()
    (output / "guide.md").write_text("mine\n", encoding="utf-8")

    assert run("--from-html", str(saved), "--output-dir", str(output), "--write") == 2
    assert (output / "guide.md").read_text(encoding="utf-8") == "mine\n"
    assert not (output / "Home.md").exists()
    assert not (output / MARKER).exists()
    assert "guide.md" in capsys.readouterr().err


def test_invalid_html_is_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    challenge = tmp_path / "challenge.html"
    challenge.write_text("<title>Just a moment...</title>", encoding="utf-8")
    output = tmp_path / "reference"

    assert (
        run("--from-html", str(challenge), "--output-dir", str(output), "--write") == 2
    )
    assert not output.exists()
    assert "Nothing was written" in capsys.readouterr().err


class FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


CHALLENGE = FakeResponse(403, "<!DOCTYPE html><title>Just a moment...</title>")


def fake_requests(
    monkeypatch: pytest.MonkeyPatch, response: FakeResponse
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr(_fetch.requests, "get", fake_get)
    return calls


def test_fetch_names_itself_and_suggests_a_saved_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_requests(monkeypatch, CHALLENGE)

    with pytest.raises(FetchError, match="--from-html"):
        fetch_html()
    # One request per browser handshake, all for the one page, and the tool
    # may borrow a browser's handshake, but never its name.
    assert len(calls) == len(_fetch.BROWSER_HANDSHAKES)
    assert {call["url"] for call in calls} == {_fetch.DOCS_URL}
    assert all(
        call["headers"]["User-Agent"].startswith("discogs-api-reference/")
        for call in calls
    )


def test_fetch_never_follows_a_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_requests(monkeypatch, FakeResponse(301))

    with pytest.raises(FetchError, match="HTTP 301"):
        fetch_html()
    assert len(calls) == 1
    assert calls[0]["allow_redirects"] is False
