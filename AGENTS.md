# AGENTS.md

Guidance for coding agents working in this repository.

## Project

discogs-api-reference: Build a local Markdown copy of the Discogs API reference

The tool downloads `https://www.discogs.com/developers` and converts it to one
Markdown file per section ([README.md](README.md)). These limits keep it a reader of
one documentation page, never a scraper of Discogs, and changes must keep them:

- It fetches only `DOCS_URL` (`_fetch.py`): no other address, no URL option, no
  crawling. It retries with another browser handshake only after a rejection.
- Its `User-Agent` names the tool and links to this repository. It never claims to
  be a browser, even though it opens the connection the way one does.
- The repository never contains Discogs content. Tests build their HTML from
  `tests/reference_html.py`, which mimics the page's layout with invented text; never
  commit a saved copy of the page or the generated Markdown.
- The Markdown layout described under "Output" in README.md is a contract: projects
  parse the route lines and the response markers. Change it only on purpose, and
  update the README and the tests with it.

## Commands

Task runner is [just](https://github.com/casey/just); every recipe runs its tool
through [uv](https://docs.astral.sh/uv/).

```bash
just setup              # Install deps + pre-commit hooks (hooks: main checkout only)
just test               # Run pytest with coverage
just test <path>        # Run one test file or directory
just format             # ruff format + pyproject-fmt + rumdl fmt (Markdown)
just lint-fix           # ruff check --fix + rumdl check --fix
just type-check         # ty check
just verify-types       # Public API type completeness; fails until the first export
just deps-unused        # deptry src
just spell              # cspell against cspell.json
just qa                 # All checks: every pre-commit hook, then verify-types
just deps-update        # Update deps to latest versions
just changelog-preview  # Release notes for unreleased commits
just release-prepare    # Maintainers only: open the PR that sets the release version
just release            # Maintainers only: tag the merged release and publish it
just release-next       # Maintainers only: open the PR for the next development version
```

Run a single test: `just test tests/test_version.py -k matches_installed_metadata`

Before finishing a change, run `just format && just lint-fix && just qa && just test`.
`just qa` runs pre-commit, which sees only files git tracks: `git add` new files
first.

## Language

Write US English in everything you write for this project: code comments,
docstrings, error messages, identifiers, tests, documentation, commit messages
and replies. That means `-ize` and `-yze` (`normalize`, `analyze`), `-or`
(`behavior`, `honor`), `-er` (`center`), a single `l` before a suffix
(`labeling`, `canceled`), and `license` as both noun and verb. Leave other
people's text, such as `LICENSE.txt` or vendored code, as it is.

## Conventions

- Python 3.11+, developed on the version in `.python-version`; ruff
  enforces a line length of 88
- ty is the type checker; pyright runs only for `--verifytypes`. The
  package ships `py.typed` (PEP 561), so the public API stays fully typed
- Dependency groups: `dev` holds the tools and includes `test`, which holds only
  what the tests import. CI installs `test` on its own, next to the built wheel, so a
  test cannot lean on a `dev` tool
- Workarounds that are knowingly less than ideal carry a `KLUDGE:` comment
  stating what is wrong and what removes it. Grep for `KLUDGE` before changing
  one; do not add one without a removal condition

## Architecture

What future work on discogs-api-reference may assume today. Commands and day-to-day
conventions are above; the process for contributors is in
[CONTRIBUTING.md](CONTRIBUTING.md).

### Shape

A Python CLI published to PyPI. The `discogs-api-reference` console script calls
`discogs_api_reference.cli:main`; projects run it with `uvx discogs-api-reference`.

- `_fetch.py` downloads the page
- `_render.py` validates the page and converts each section to Markdown
- `cli.py` compares the result with the local copy, then reports or writes

### Language, runtime, and tooling

- Python 3.11+ (`requires-python`); developed on the version in
  `.python-version`
- uv manages dependencies and environments; `uv.lock` is committed, and uv_build
  builds the distributions
- just is the task runner
- ruff formats and lints; pyproject-fmt formats `pyproject.toml`; rumdl formats and
  lints Markdown, configured in `.rumdl.toml`
- ty checks types; pyright `--verifytypes` checks that the public API is fully
  typed
- deptry reports unused and undeclared dependencies
- cspell checks spelling against `cspell.json`; actionlint checks the workflows
- pre-commit holds the one list of checks, run on every commit, by `just qa` and by
  CI. The tools the justfile also runs on their own come from `uv.lock` through
  `uv run`; the general file checks, actionlint and cspell are pinned in
  `.pre-commit-config.yaml`

### Structure

- `src/discogs_api_reference/`: the package (src layout)
- `tests/`: the pytest suite
- `scripts/`: distribution checks that CI runs
- `docs/`: durable project documents, when there are any

### Testing

pytest with coverage (`just test`). CI runs the suite:

- on every supported Python, 3.11 to 3.15
- against the oldest dependency versions `pyproject.toml` allows, with deprecations
  fatal
- against the built wheel, installed into a clean environment

### Distribution

- Wheel and sdist built once by CI and checked by `scripts/check_distributions.py`
  and `twine check --strict`; the same files are published, never rebuilt
- Published to PyPI through trusted publishing from `.github/workflows/publish.yml`
  when a `vX.Y.Z` tag on `main` is pushed; `just release` creates it signed
- Between releases `main` carries a development version, `X.Y.Z.devN`, which sorts
  below `X.Y.Z`
- Release notes generated by git-cliff from the pull request titles on `main`
- License: Apache-2.0

### CI

- `.github/workflows/ci.yml` runs on pushes to `main` and on every pull request:
  every pre-commit hook and `--verifytypes`, then the tests, then
  builds and install-tests the distributions. Actions are pinned to commit
  SHAs, and no checkout keeps its token
- The `CI passed` job needs every other job and fails when one failed or was canceled.
  It is the one required check: a new job joins its `needs`
- Dependabot opens weekly grouped updates for GitHub Actions and `uv.lock`, with
  `build:` commit messages and the `dependencies` and `build` labels; it moves the
  lock only, never the minimum versions in `pyproject.toml`

### Agent support

Coding agents are expected contributors. They follow this file. Agents
never release.

## Releasing

**Agents never release.** Do not run `just release-prepare`, `just release` or
`just release-next`, create or push a `v*` tag (pushing one publishes to PyPI),
create a GitHub release, or interact with PyPI. Finish the work, run the checks
above, report, and stop.

The process for maintainers is in [CONTRIBUTING.md](CONTRIBUTING.md#releasing).

## Shared Workflow

This repository follows the shared workflow: the `github-workflow` skill's repository
setup describes its GitHub settings, rulesets, labels and templates. Those settings are
managed as code in the `infra` repository; change them there, never with `gh api` or
the GitHub web UI.

It is a pull-request repository: work happens on a branch and lands through a pull
request.

### Deviations From the Shared Workflow

None.
