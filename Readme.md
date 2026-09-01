# pycraftcore

`pycraftcore` is a reusable technical infrastructure library for Python applications: configuration loading, HTTP
clients with retries/circuit-breaking/tracing, a pooled async SQLite repository, a sandboxed Python code runner, safe
SQL validation, serialization, and a handful of other adapters — all built as small, swappable ports/adapters rather
than a framework.

**Design principles:** Modularity · Reusability · Maintainability

Every module follows the same shape: a `port/` package with `Protocol` interfaces and an `adapter/` package with one
or more concrete implementations, so consumers depend on the port, not the adapter.

---

## Table of Contents

- [Components](#components)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)

---

## Components

| Module | Package | Description |
|---|---|---|
| Configuration Management | `application_configuration` | Environment-driven YAML config (connector/operation/cronjob), `${oc.env:...}` injection, typed/validated models |
| Authentication | `application_configuration` | Typed auth models (none / basic / token) shared across connector configs |
| Logging | `logger` | Singleton structured logger over loguru, behind a `Logger` port |
| Telemetry & Observability | `telemetry` | OpenTelemetry-backed tracing: span decorator, request-id enrichment, console or OTLP export |
| HTTP Client Utilities | `http` | `aiohttp`/`httpx` clients behind a common port, retry policy, circuit breaker, and a `ResilientClient` composing all three with tracing |
| Repository / SQLite | `repository` | Async SQLite repository backed by a real connection pool (WAL mode, `busy_timeout`) — not just an async-wrapped single connection |
| Query Language / SQL Safety | `query_language` | `sqlglot`-based parser that rejects any non-read-only statement anywhere in the parsed tree, including nested |
| Runtime / Sandboxed Execution | `runtime` | Runs arbitrary Python in a separate OS process with an import allowlist, memory/CPU limits, and a timeout |
| Serialization | `serialization` | JSON, dict, and binary (msgpack) serialization for dataclasses, backed by pydantic validation |
| Scientific computation engine | `computation` | NumPy/SciPy-backed arithmetic (log returns, rolling average/stddev) and calculus (integration, interpolation) |
| File handler | `file_handler` | Extension-based read/write strategy (currently YAML), pluggable for more formats |
| Profiler | `profiler` | `pyinstrument`-based async function profiling decorator |

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

A database connector additionally takes `engine`, `host`, `port`, `default_name`, and a `pool` block controlling how
many pooled connections the repository opens. An `operation/<tag>.yml` follows the same shape — a `type` (`api` /
`file`) plus a `connector` reference — and adds `endpoint`/`method`/`parameters` for `api`, or `action`/`parameters`
for `file`. See `pycraftcore.application_configuration.model` for the full schema.

**Loading it:**

```python
from pathlib import Path

from pycraftcore.application_configuration.adapter.load_application_configuration import (
    LoadApplicationConfiguration,
)
from pycraftcore.application_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from pycraftcore.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from pycraftcore.logger.adapter.loguru_logger import LoguruLogger

reader = OmegaConfigurationReader(RunTypeEnvironment.deploy, Path("config"))
loader = LoadApplicationConfiguration(reader, LoguruLogger())

config = loader.load()  # re-reads and validates every call; raises on failure (after logging)
```

**Reading it back:** `connector`/`operation` are typed registries, not raw dicts — `.api(name)`/`.database(name)`/`.file(name)`/`.telemetry(name)` and `.operation.api(name)`/`.operation.file(name)` return the concrete connector/operation type (no `cast`/`isinstance` needed at the call site) and raise `KeyError`/`TypeError` on a missing or mismatched name.

```python
postgres = config.connector.database("postgres")  # DatabaseConnector
ask = config.operation.api("dummy_api_1_op")  # ApiOperation
```

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
make typecheck           # uv run ty  (strict mode)
```

Run `pytest --cov=pycraftcore --cov-report=term-missing` for a coverage breakdown by module.
