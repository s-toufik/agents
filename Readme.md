# agents

An analytics agent and its tool server, run as two independent processes that talk to
each other over MCP (Model Context Protocol).

---

## Setup

```bash
uv sync --group dev
```

Create a `.env` file in the project root:

```bash
APP_ENV=debug

# where the toolbox's sqlite databases live
USER_DB_HOST=/absolute/path/to/sqlite
USER_DB_NAME=user
CHECKPOINT_DB_HOST=/absolute/path/to/sqlite
CHECKPOINT_DB_NAME=checkpoint

# optional -- defaults shown
# LLM_BASE_URL=http://nautilus:1234/v1
# TOOLBOX_URL=http://localhost:8001/mcp
# TOOLBOX_TOKEN=
```

---

## Running it

Start the toolbox first — the agent discovers its tools from it at boot and refuses to
start if it can't be reached:

```bash
uv run uvicorn bootstrap.application.toolbox_application:app --host 0.0.0.0 --port 8001
```

Then the agent, in a second terminal:

```bash
uv run uvicorn bootstrap.application.agent_application:app --host 0.0.0.0 --port 8000
```

| | URL |
|---|---|
| Toolbox — MCP endpoint | `http://localhost:8001/mcp` |
| Toolbox — health | `http://localhost:8001/health` |
| Agent — chat (SSE) | `POST http://localhost:8000/api/v1/agent/stream` |
| Agent — health | `http://localhost:8000/health` |

`POST /api/v1/agent/stream` body:

```json
{ "message": "how many users signed up today?", "model_name": "gpt-oss-20b", "request_id": "any-string" }
```

---

## Configuration

Everything lives under `config/` — `config/root.yml` plus `config/debug/connector/*.yml`
and `config/debug/operation/*.yml`. Both processes read the same tree; each only looks at
the connectors it needs.

### Using its own tools

The default. The agent reaches the bundled toolbox through the `toolbox` connector in
`config/debug/connector/mcp.yml`, which points at `TOOLBOX_URL` (`http://localhost:8001/mcp`
by default). Nothing to configure — just run both processes as above.

### Using an external MCP server instead

Point that same connector at a different server — the agent doesn't know or care whether
it's this project's toolbox or someone else's MCP server, it's the same client either way.
Set `TOOLBOX_URL` in `.env` to the external server's URL, or edit `base_url` in
`config/debug/connector/mcp.yml` directly.

### Using both at once

Add a second connector under `connector:` in `config/debug/connector/mcp.yml`, with a name
starting with `external_mcp_`:

```yaml
connector:
  external_mcp_analytics:
    name: external_mcp_analytics
    type: mcp
    base_url: https://some-other-server.example.com/mcp
    timeout: 30
    transport: streamable_http
    auth:
      type: token
      key_name: Authorization
      key_value: ${oc.env:ANALYTICS_MCP_TOKEN,''}
```

List it in `config/root.yml` next to the existing `mcp:` entries:

```yaml
mcp:
  toolbox: ${connector.toolbox}
  self: ${connector.self}
  external_mcp_analytics: ${connector.external_mcp_analytics}
```

Restart the agent. Any connector name prefixed `external_mcp_` is picked up automatically
at boot and merged into the same tool catalogue as the toolbox — no code change. The boot
log confirms what was found, per server:

```
Discovered 2 MCP tools from 'toolbox': users_tables, python_executor
Discovered 5 MCP tools from 'external_mcp_analytics': ...
```

---

## Development

```bash
make check       # lint + typecheck + tests
make test
make lint
make format
make typecheck
```

### Pre-commit hooks

Runs `ty`, `ruff`, and the test suite before every commit and push. Install once:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

To run them manually against the whole repo:

```bash
uv run pre-commit run --all-files --hook-stage pre-commit
```
