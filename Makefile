venv:
	uv venv

install:
	uv sync

install_dev:
	uv sync --group dev

update_dependency:
ifdef PACKAGE
	uv lock --upgrade-package $(PACKAGE)
else
	uv lock --upgrade
endif
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .

fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

typecheck:
	uv run ty check

check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

# --- run -------------------------------------------------------------------
run_toolbox:
	uv run uvicorn bootstrap.application.toolbox_application:app --host 0.0.0.0 --port 8001

run_agent:
	uv run uvicorn bootstrap.application.agent_application:app --host 0.0.0.0 --port 8000

# Toolbox first: the agent discovers its tools at boot.
run:
	$(MAKE) -j2 run_toolbox run_agent

clean:
	rm -rf dist src/*.egg-info

build:
	rm -rf dist src/*.egg-info
	uv build
