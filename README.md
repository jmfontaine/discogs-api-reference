# discogs-api-reference

Build a local Markdown copy of the
[Discogs API reference](https://www.discogs.com/developers), one file per section, for
the tools and coding agents that cannot read the website.

Discogs publishes its API reference only as a web page, and Cloudflare blocks scripts
and agents on every discogs.com page. This tool downloads that one page, converts it to
Markdown, and reports what changed since your last copy.

## Installation

The tool needs Python 3.11 or later. Install it from PyPI with
[uv](https://docs.astral.sh/uv/):

```bash
uv tool install discogs-api-reference
```

Or run it without installing it:

```bash
uvx discogs-api-reference
```

## Usage

```bash
discogs-api-reference [OPTIONS]
```

| Option | Effect |
| --- | --- |
| (none) | Report which files would change; write nothing |
| `--write` | Create or update the copy |
| `--check` | Exit with status 1 when the copy is out of date |
| `--diff` | Also print a unified diff for each change |
| `--output-dir DIR` | Where the copy lives (default: `reference/discogs_api`) |
| `--from-html PATH` | Convert a page saved from a browser instead of downloading it |

Errors exit with status 2 and write nothing.

In a project, git-ignore the copy and add a recipe, for example in a `justfile`. The
`@latest` suffix makes uvx check for a new release on each run; without it, uvx keeps
the version it cached on its first run, and a fix for a change to the Discogs page
would not reach the project:

```just
# Compare reference/discogs_api/ with the Discogs API reference (--diff, --check, --write)
[positional-arguments]
update-api-docs *args:
    uvx discogs-api-reference@latest "$@"
```

## Output

- One Markdown file per section of the reference, named after its title, such as
  `Database.md` or `User Collection.md`.
- Every heading and endpoint keeps the website's ID as an `<a id="…">` anchor, and links
  between sections are relative links to those anchors.
- Each endpoint starts with its name as a level-4 heading, then the HTTP method, then
  its route alone on a line between backticks, such as `` `/releases/{release_id}` ``.
  Its parameters, requests and responses follow as list items: `- **Parameters**`,
  `- **Request**` and ``- **Response `200`**``. Examples are fenced code blocks, with
  `json` for JSON bodies.
- `--write` also creates a `.discogs-api-reference` file in the directory. The tool
  deletes a page that the reference no longer has only from a directory with that file,
  so it never deletes Markdown it did not write.

## Use of Discogs Content

The reference belongs to Discogs. The copy is for your own local use, such as building
tools that call the API as its terms allow. Do not commit, publish or share it: the
Discogs Terms of Service forbid providing cached copies of their content to others.

The tool sends one request to `https://www.discogs.com/developers` per run, and tries
again with another browser profile, up to three requests in all, only when Cloudflare
rejects one. It accepts no other address. Its `User-Agent` header names the tool and
links to this repository. Cloudflare rejects connections that do not look like a
browser's, so the tool uses [curl_cffi](https://github.com/lexiforest/curl_cffi) to open
the connection the way a browser does.

When the download fails, open the page in a browser, save it as HTML, and pass the file
with `--from-html`.

## Development

See [CONTRIBUTING.md][contributing]. In short, with [uv][uv] and [just][just] installed:

```bash
just setup  # Install dependencies and git hooks
just qa     # Run all checks
just test   # Run the tests
```

## License

[Apache License 2.0][license]

<!-- Absolute URLs, so the links also work on PyPI. -->
[contributing]: https://github.com/jmfontaine/discogs-api-reference/blob/main/CONTRIBUTING.md
[license]: https://github.com/jmfontaine/discogs-api-reference/blob/main/LICENSE.txt
[uv]: https://docs.astral.sh/uv/
[just]: https://github.com/casey/just
