# pycraftcore

`pycraftcore` is a reusable technical infrastructure library for Python applications: configuration, resilient HTTP
clients, a pooled async SQLite repository, a sandboxed Python code runner, safe SQL validation, serialization, and a
handful of other adapters — small, swappable building blocks rather than a framework.

**Design principles:** Modularity · Reusability · Maintainability

---

## Table of Contents

- [Functionality](#functionality)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)

---

## Functionality

| Module | Package | What it gives you |
|---|---|---|
| Configuration Management | `application_configuration` | Environment-driven YAML configuration for connectors and operations, validated and typed |
| Authentication | `application_configuration` | Shared auth models (none / basic / token) for any connector |
| Logging | `logger` | Structured application logging |
| Telemetry & Observability | `telemetry` | Distributed tracing, exportable to console or an OTLP collector |
| HTTP Client Utilities | `http` | Resilient HTTP client with retries, circuit breaking, and tracing |
| Repository / SQLite | `repository` | Async SQLite repository with real connection pooling for concurrent access |
| Query Language / SQL Safety | `query_language` | Validates that a SQL statement is read-only before it reaches a database |
| Runtime / Sandboxed Execution | `runtime` | Runs untrusted Python code in an isolated process with resource limits |
| Serialization | `serialization` | JSON, dict, and binary (msgpack) serialization for dataclasses |
| Scientific computation engine | `computation` | Financial arithmetic and calculus (integration, interpolation) |
| File handler | `file_handler` | Read/write files by extension, pluggable for new formats |
| Profiler | `profiler` | Async function profiling decorator |

---

## Installation

**Stable release** (recommended for production):

```bash
pip install pycraftcore
```

**Development build** (latest features, may be unstable):

```bash
pip install -i https://test.pypi.org/simple/ pycraftcore
```
> [!WARNING]
> The development build is intended for testing only and should **not** be used in production.

---

## Configuration

Services are configured using YAML files combined with environment variables.

**Directory layout** — a `root.yml` plus per-kind subdirectories, one file per item:

| Path | Description |
|---|---|
| `root.yml` | Root application configuration (`env`, `run`) |
| `connector/*.yml` | Data source connector definitions |
| `operation/*.yml` | Retrieval operations and business use cases |

**Environment variables** referenced from YAML via `${oc.env:NAME}`:

| Variable | Used by |
|---|---|
| `APP_ENV` | `root.yml` → `env` |
| `<CONNECTOR_NAME>_API_KEY` | a connector's `auth.key_value` |
| `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | a database connector's `host`/`default_name`/`auth` |

This list isn't exhaustive — any config value can be templated the same way; check the YAML under `config/<env>/`
for what a given deployment actually reads.

**Connector example** (`connector/<tag>.yml`):

```yaml
connector:
  <connector_tag>:
    name: <connector name>
    type: api
    base_url: <base url>
    timeout: 5
    retry: 3
    auth:
      type: token
      key_name: apikey
      key_value: ${oc.env:connector_api_key}
```

**Operation example** (`operation/<tag>.yml`) — references a connector by tag:

```yaml
operation:
  <operation_tag>:
    name: <operation name>
    type: api
    connector: ${connector.<connector_tag>}
    endpoint: /<path>
    method: GET
    parameters:
      <param>: <value>
```

**Root example** (`root.yml`) — wires everything together for a given environment:

```yaml
application_configuration:
  env: ${oc.env:APP_ENV,debug}
  run: async

  connector:
    api:
      <connector_tag>: ${connector.<connector_tag>}
    file:
      <connector_tag>: ${connector.<connector_tag>}
    database:
      <connector_tag>: ${connector.<connector_tag>}
    telemetry:
      <connector_tag>: ${connector.<connector_tag>}
    
  operation:
    <operation_tag>: ${operation.<operation_tag>}
    # ...
```

Connectors and operations both declare a `type`, which determines which fields they take and which concrete object
they load as.

**Using it in code:**

```python
from pathlib import Path

from pycraftcore.application_configuration.adapter.load_application_configuration import (
    LoadApplicationConfiguration,
)
from pycraftcore.application_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from pycraftcore.application_configuration.enum.run_type_environment import RunTypeEnvironment
from pycraftcore.logger.adapter.loguru_logger import LoguruLogger

reader = OmegaConfigurationReader(RunTypeEnvironment.deploy, Path("config"))
loader = LoadApplicationConfiguration(reader, LoguruLogger())

config = loader.load()

connector = config.connector.api("<connector_tag>")  # ApiConnector
operation = config.operation.api("<operation_tag>")  # ApiOperation
```

`config.connector`/`config.operation` return the concrete connector/operation type for a given tag (`.api()`,
`.database()`, `.file()`, `.telemetry()` where applicable) instead of a raw dict — see
`pycraftcore.application_configuration` for the full API.

---

## Development

### Pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com) to run the unit test suite before every commit and push (see
`.pre-commit-config.yaml`). Git hooks live under `.git/hooks/` and aren't tracked by git, so after cloning or pulling
this change, install them once:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

After that, `git commit` and `git push` will run `uv run pytest` automatically and abort on failure. To run the
hooks manually against the whole repo:

```bash
uv run pre-commit run --all-files --hook-stage pre-commit
```

### Makefile commands

```bash
make install_dev   # uv sync --group dev
make test           # uv run pytest
make lint            # uv run ruff check
make format          # uv run ruff format
make typecheck        # uv run ty check (strict mode)
```

Run `pytest --cov=pycraftcore --cov-report=term-missing` for a coverage breakdown by module.
