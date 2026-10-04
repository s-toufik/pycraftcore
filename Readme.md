# pycraftcore

The shared technical foundation of the homelab's Python services: configuration, logging, telemetry, resilient HTTP, database repositories, safe SQL and a sandbox for running untrusted Python. Small, swappable building blocks rather than a framework — every module is an interface (a port) plus the implementations behind it (adapters).

**[Using pycraftcore](#using-pycraftcore)** — install it and use each module in your service.
**[Working on pycraftcore](#working-on-pycraftcore)** — how it is organised and how to release it.

```text
  your service (agent-orchestrator, agent-toolbox, …)
        │
        ▼
  ┌─ pycraftcore ─────────────────────────────────────────────────────────────┐
  │                                                                           │
  │  set up      application_configuration · logger · telemetry · context     │
  │  talk out    http · resilient_http (retry + circuit_breaker)              │
  │  store       repository: SQLite · PostgreSQL · MongoDB                    │
  │  run safely  query_language (read-only SQL) · runtime (Python sandbox)    │
  │  utilities   file_handler · serializer · computation_engine · profiler    │
  │  …           new modules, same port + adapter shape                       │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘
```

---

## Using pycraftcore

### Install

```bash
uv add pycraftcore          # or: pip install pycraftcore
```

Requires Python 3.14. Development builds are published to TestPyPI (`pip install -i https://test.pypi.org/simple/ pycraftcore`); use them for testing only.

### What's inside

Each module stands on its own: use the ones you need. The modules today (new ones follow the same shape, see [Working on pycraftcore](#working-on-pycraftcore)):

| Package | What it gives you |
|---|---|
| `application_configuration` | YAML configuration (connectors and operations) driven by environment variables, loaded into typed objects |
| `authentication` | The auth models a connector can use: none, basic, token |
| `logger` | One log format for the whole process, with the request id on every line |
| `context` | `request_id_context`, the request id shared by logs, telemetry and outgoing calls |
| `telemetry` | OpenTelemetry traces, metrics and logs, exported to an OTLP collector (or nothing) |
| `http` | Async HTTP clients (httpx, aiohttp), request-id and request-context middlewares, retry policies |
| `resilient_http` | An HTTP transport with retries and a circuit breaker built in |
| `retry`, `circuit_breaker` | The two policies on their own, for any async call |
| `repository` | Async repositories built from a database connector — today SQLite (pooled), PostgreSQL and MongoDB |
| `query_language` | Checks that a SQL statement is read-only, and translates between dialects, before it reaches a database |
| `runtime` | Runs untrusted Python in a separate process with memory, time and module limits; optionally lets it call your functions |
| `file_handler` | Read and write files by extension (today csv, json, yml, md, txt); a new format is a new reader/writer pair |
| `serializer` | JSON, dict and binary (msgpack) serialisation of dataclasses |
| `computation_engine` | Numerical helpers: financial arithmetic, integration, interpolation |
| `profiler` | `@profiled`, an async profiling decorator |

### Configuration

A service's configuration is a folder of YAML files, with values taken from environment variables (`${oc.env:NAME}`):

| Path | What it holds |
|---|---|
| `root.yml` | The environment and the list of connectors and operations in use |
| `<env>/connector/*.yml` | Where things are: APIs, databases, files, MCP servers, telemetry |
| `<env>/operation/*.yml` | What you do with them; each operation points at a connector |

```yaml
# <env>/connector/api.yml
connector:
  weather:
    name: weather
    type: api
    base_url: https://<api-host>
    timeout: 5
    retry: 3
    auth:
      type: token
      key_name: apikey
      key_value: ${oc.env:WEATHER_API_KEY}
```

```yaml
# <env>/operation/weather.yml
operation:
  forecast:
    name: forecast
    type: api
    connector: ${connector.weather}
    endpoint: /forecast
    method: GET
    parameters:
      days: 3
```

```yaml
# root.yml
application_configuration:
  env: ${oc.env:APP_ENV,debug}
  run: async
  connector:
    api:
      weather: ${connector.weather}
  operation:
    forecast: ${operation.forecast}
```

```python
from pathlib import Path

from pycraftcore.application_configuration.adapter import (
    LoadApplicationConfiguration,
    OmegaConfigurationReader,
)
from pycraftcore.application_configuration.enum import RunTypeEnvironment
from pycraftcore.logger.adapter import StandardLogger

reader = OmegaConfigurationReader(RunTypeEnvironment.debug, Path("config"))
config = LoadApplicationConfiguration(reader, StandardLogger()).load()

connector = config.connector.api("weather")   # ApiConnector
operation = config.operation.api("forecast")  # ApiOperation
```

`config.connector` returns typed connectors per kind (`.api()`, `.database()`, `.file()`, `.mcp()`, `.telemetry()`) and `config.operation` typed operations (`.api()`, `.file()`); the `type` field of each entry decides which fields it takes.

### Logging and the request id

```python
from pycraftcore.logger import configure_logging
from pycraftcore.logger.adapter import StandardLogger

configure_logging("INFO")
logger = StandardLogger()
logger.info("booted")
```

```text
2026-09-27 10:06:17.679 | INFO     | 1bddfefb-… | controller:execute:51 - stream request accepted
```

- The third column is `request_id_context`. In a web service, `RequestIDMiddleware` (`pycraftcore.http.middleware`) sets it from the `X-Request-ID` header; every line logged during that request shows it, `-` otherwise. Don't write it in your messages.
- Uvicorn logs use the same format; chatty libraries (httpx, mcp, pymongo…) stay at `WARNING`.
- Calling `configure_logging` again replaces the handler rather than adding a second one.

### Telemetry

```python
from pycraftcore.application_configuration.enum import RunTypeEnvironment
from pycraftcore.telemetry.adapter import OpenTelemetryProvider

telemetry = OpenTelemetryProvider(
    service_name="my-service",
    environment=RunTypeEnvironment.debug,
    otlp_endpoint="<collector-host>:<port>",   # None: nothing is exported
)
tracer = telemetry.tracer("my-service")
```

Spans and log records carry the request id as an attribute, so logs and traces line up in Grafana.

### Resilient HTTP

A transport that retries what is worth retrying and stops calling a backend that keeps failing:

```python
from pycraftcore.circuit_breaker.configuration import CircuitBreakerSettings
from pycraftcore.http.configuration import HttpClientSettings, LimitsSettings
from pycraftcore.http.policy.http_error_policy import is_business_error, is_retryable
from pycraftcore.resilient_http.adapter import ResilientTransportFactory
from pycraftcore.resilient_http.configuration import ResilientHttpSettings
from pycraftcore.retry.configuration import RetrySettings

settings = ResilientHttpSettings(
    http=HttpClientSettings(limits=LimitsSettings(timeout=10)),
    retry=RetrySettings(retry_count=3, retry_delay=1, max_retry_delay=20, should_retry=is_retryable),
    circuit_breaker=CircuitBreakerSettings(
        failure_threshold=3, recovery_timeout=30, is_excluded=is_business_error, name="weather"
    ),
)
client = ResilientTransportFactory(settings=settings, trace_manager=tracer, logger=logger).create_async_client()
```

`client` is an `httpx.AsyncClient`: pass it to any library that accepts one.

### Databases

Repositories are built from a database connector and share one interface, `AsyncRepository.execute(statement)`:

```python
from pycraftcore.repository.adapter import SqliteRepositoryFactory, SqliteSettingsMapper

factory = SqliteRepositoryFactory(SqliteSettingsMapper(config.connector.database("users"))())
repository = await factory.connect()
rows = await repository.execute("SELECT id, email FROM users LIMIT 10")
await factory.disconnect()
```

`PostgresRepositoryFactory` / `PostgresSettingsMapper` and `MongoRepositoryFactory` / `MongoSettingsMapper` work the same way, and so will any database added later: a factory, a settings mapper and a repository behind the same `AsyncRepository` port.

### Read-only SQL

```python
from pycraftcore.query_language.adapter import SqlHandlerFactory

statement = SqlHandlerFactory()("SELECT * FROM users", dialect="sqlite").transpile()
```

`transpile()` raises when the statement writes, deletes or changes the schema, so only reads reach the database.

### Running untrusted Python

```python
from pycraftcore.runtime.adapter import PythonSafeCodeFactory
from pycraftcore.runtime.schema import CodeResult, SafeCodeSettings

factory = PythonSafeCodeFactory(settings=SafeCodeSettings(code_timeout=30, max_memory_mb=256))
output = await factory(code="import math\nresult = math.sqrt(2)").execute()
print(CodeResult.from_stdout(output.stdout).value)   # 1.4142135623730951
```

- The code runs in its own process; only the modules in `PYTHON_ALLOWLIST` can be imported (pandas, numpy, matplotlib, datetime…).
- `working_directory` in `SafeCodeSettings` confines file access to one folder.
- With a `HostBridgeServer`, the code can call functions of your service as if they were local — this is how agent-toolbox lets sandboxed code use its other tools.

---

## Working on pycraftcore

### How a module is organised

Every package follows the same shape, so a new backend is a new adapter, never a change for the services that use the port:

```text
  pycraftcore/<module>/
  ├── port/            Protocols the services depend on (AsyncRepository, Code, Logger…)
  ├── adapter/         Implementations (SqliteRepository, PythonSafeCode, StandardLogger…)
  ├── configuration/   Pydantic settings objects (RetrySettings, CircuitBreakerSettings…)
  ├── schema/          Data passed across the port (CodeResult, SafeCodeSettings…)
  └── enum/            Fixed choices (ConnectorType, HttpMethod…)
```

Not every module needs every folder: add a folder when it has something to hold.

### Design rules

- Services import the **port** and receive an adapter; they never construct a third-party client themselves.
- Adapters are thin: they translate between the port and the library, and keep library types out of the port.
- Settings are validated pydantic models; nothing reads environment variables except the configuration loader.
- Every public module is typed: `ty` runs in strict mode.

### Adding a module or an adapter

1. Define the protocol in `<module>/port/`.
2. Implement it in `<module>/adapter/`, with its settings in `configuration/` and the data it exchanges in `schema/`.
3. Export the public names from the package's `__init__.py`.
4. Add tests under `tests/<module>/`, and the module to [What's inside](#whats-inside) — with a short example under Using pycraftcore if services will use it directly.

### Tests and checks

```bash
make install_dev    # uv sync --group dev
make check          # ruff + ty + pytest
make test
make lint / make fix / make format / make typecheck
uv run pytest --cov=pycraftcore --cov-report=term-missing   # coverage per module
```

Pre-commit runs the test suite before every commit and push:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

### Releasing

1. Bump `version` in `pyproject.toml`.
2. `make build`.
3. `make publish_dev` to TestPyPI (needs `TEST_PYPI_TOKEN`), try it in a service, then `make publish` to PyPI (needs `RELEASE_PYPI_TOKEN`).
4. Raise the minimum version in the services that need the change (`pycraftcore>=…` in their `pyproject.toml`), then `uv lock --upgrade-package pycraftcore`.

To work on pycraftcore and a service at the same time, point the service at your checkout with an editable path dependency in its `pyproject.toml`: `pycraftcore = { path = "../pycraftcore", editable = true }` under `[tool.uv.sources]`.
