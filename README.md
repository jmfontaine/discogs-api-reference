# discogs-api-reference

Build a local Markdown copy of the Discogs API reference

## Installation

```bash
uv tool install discogs-api-reference
```

or `pip install discogs-api-reference`.

## Usage

```bash
discogs-api-reference --help
```

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
