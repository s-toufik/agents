# agent

## Setup

```bash
uv sync --group dev
```

## Development

```bash
make test      # run the unit test suite (uv run pytest)
make lint       # ruff check
make format     # ruff format
make typing     # mypy --strict
```

## Pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com) to run the unit test suite before every commit and push (see `.pre-commit-config.yaml`). Git hooks live under `.git/hooks/` and aren't tracked by git, so after cloning or pulling this change, install them once:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

After that, `git commit` and `git push` will run `uv run pytest` automatically and abort on failure. To run the hooks manually against the whole repo:

```bash
uv run pre-commit run --all-files --hook-stage pre-commit
```
