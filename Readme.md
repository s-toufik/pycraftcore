# pycraftcore

A shared technical foundation for Python services: configuration, logging, telemetry, resilient HTTP, HTTP APIs on Litestar, FastAPI or BlackSheep, database repositories, safe SQL and a sandbox for running untrusted Python. Small, swappable building blocks rather than a framework — every module is an interface (a port) plus the implementations behind it (adapters).

**[Using pycraftcore](#using-pycraftcore)** — install it and use each module in your service.
**[Working on pycraftcore](#working-on-pycraftcore)** — how it is organised and how to release it.

```text
  your service (orders-api, billing-worker, …)
        │
        ▼
  ┌─ pycraftcore ─────────────────────────────────────────────────────────────┐
  │                                                                           │
  │  set up      application_configuration · logger · telemetry · context     │
  │  talk out    http · resilient_http (retry + circuit_breaker)              │
  │  serve       web: ASGI APIs on Litestar, FastAPI or BlackSheep            │
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

Requires Python 3.14. Each module's third-party dependencies sit behind an extra of the same name, so a service installs only what it uses:

```bash
uv add "pycraftcore[http,repository]"     # or: pip install "pycraftcore[http,repository]"
uv add "pycraftcore[all]"                 # every module
```

A bare `pycraftcore` installs no third-party packages: only `authentication`, `context` and `logger` work without an extra. For any other module, importing its adapters without the extra fails with `ModuleNotFoundError`.

| Extra | Third-party packages | Also brings in |
|---|---|---|
| `authentication`, `context`, `logger` | none | — |
| `profiler` | pyinstrument | — |
| `query_language` | sqlglot | — |
| `computation_engine` | numpy, scipy | — |
| `serializer` | orjson, msgpack, pydantic | — |
| `file_handler` | orjson, pyyaml | — |
| `runtime` | pydantic | — |
| `runtime-sandbox` | pandas, numpy, matplotlib, python-dateutil | `runtime` |
| `circuit_breaker` | aiobreaker | `logger` |
| `retry` | tenacity | `logger` |
| `http` | aiohttp, httpx, orjson | `context`, `logger` |
| `web` | none | `context` |
| `web_fastapi`, `web_litestar`, `web_blacksheep` | fastapi, litestar, blacksheep (one each) | `web` |
| `application_configuration` | omegaconf, pydantic, python-dotenv | `http`, `logger`, `authentication` |
| `telemetry` | opentelemetry (api, sdk, otlp exporter, logging instrumentation) | `application_configuration`, `context` |
| `resilient_http` | aiohttp, httpx | `circuit_breaker`, `http`, `retry`, `telemetry` |
| `repository` | aiosqlite, pymongo, psycopg, psycopg-pool, orjson, pydantic | `application_configuration`, `authentication` |

List every module your code imports, even when one extra already brings in another. That way your service stays correct if these links change. For the Python sandbox, use `runtime-sandbox` rather than `runtime`: the sandboxed code runs on your service's interpreter, so the libraries it may import (pandas, numpy, matplotlib, dateutil) must be installed there.

Development builds are published to TestPyPI; use them for testing only. Their dependencies come from PyPI, so add it as an extra index:

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "pycraftcore[http]"
```

### What's inside

Each module stands on its own: use the ones you need. The modules today (new ones follow the same shape, see [Working on pycraftcore](#working-on-pycraftcore)):

| Package | What it gives you |
|---|---|
| `application_configuration` | YAML configuration (connectors, operations, servers and the log level) driven by environment variables, loaded into typed objects |
| `authentication` | The auth models a connector can use: none, basic, token |
| `logger` | One log format for the whole process, with the request id on every line |
| `context` | `request_id_context`, the request id shared by logs, telemetry and outgoing calls |
| `telemetry` | OpenTelemetry traces, metrics and logs, exported to an OTLP collector (or nothing) |
| `http` | Async HTTP clients (httpx, aiohttp) and retry policies |
| `web` | The framework-free parts of an HTTP API: `ApiSettings` (title, version, base path, docs, CORS), the actuator, `RequestIDMiddleware`, server-sent events with heartbeats |
| `web_litestar`, `web_fastapi`, `web_blacksheep` | One toolkit per framework: build the app with pycraftcore's conventions and write your routes with the framework's own features |
| `resilient_http` | An HTTP transport with retries and a circuit breaker built in |
| `retry`, `circuit_breaker` | The two policies on their own, for any async call |
| `repository` | Async repositories built from a database connector — today SQLite (pooled), PostgreSQL and MongoDB |
| `query_language` | Checks that a SQL statement is read-only, and translates between dialects, before it reaches a database |
| `runtime` | Runs untrusted Python in a separate process with memory, time and module limits; optionally lets it call your functions |
| `file_handler` | Read and write files by extension (today csv, json, yml, md, txt, svg); a new format is a new reader/writer pair |
| `serializer` | JSON, dict and binary (msgpack) serialisation of dataclasses |
| `computation_engine` | Numerical helpers: financial arithmetic, integration, interpolation |
| `profiler` | `@profiled`, an async profiling decorator |

### Configuration

A service's configuration is a folder of YAML files, with values taken from environment variables (`${oc.env:NAME}`):

| Path | What it holds |
|---|---|
| `root.yml` | The environment, the log level and the list of connectors, operations and servers in use |
| `<env>/connector/*.yml` | Where things are: APIs, databases, files, MCP servers, telemetry |
| `<env>/operation/*.yml` | What you do with them; each operation points at a connector |
| `<env>/server/*.yml` | How the service itself is served: base path, API documentation, CORS origins, and your own `parameters` |

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
# <env>/server/asgi.yml
server:
  weather-api:
    name: weather-api
    type: asgi
    base_path: ${oc.env:WEB_BASE_PATH,""}
    docs: ${oc.env:WEB_DOCS,false}
    cors_origins: ["*"]
    parameters:
      max_forecast_days: ${oc.env:MAX_FORECAST_DAYS,7}
```

```yaml
# root.yml
application_configuration:
  env: ${oc.env:APP_ENV,debug}
  run: async
  log: ${oc.env:LOG_LEVEL,INFO}
  server:
    asgi:
      weather-api: ${server.weather-api}
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

connector = config.connector.api("weather")  # ApiConnector
operation = config.operation.api("forecast")  # ApiOperation
server = config.server.asgi("weather-api")  # AsgiServer
```

`config.connector` returns typed connectors per kind (`.api()`, `.database()`, `.file()`, `.mcp()`, `.telemetry()`), `config.operation` typed operations (`.api()`, `.file()`) and `config.server` typed servers (`.asgi()`); the `type` field of each entry decides which fields it takes.

- `log` is a `LogLevel` (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, upper case): pass it to `configure_logging(config.log)`.
- A server holds `base_path`, `docs` and `cors_origins`: turn them into the web toolkit's `ApiSettings` (see [Serving an HTTP API](#serving-an-http-api)). Which framework serves the API is a choice made in code, not in the configuration.
- `parameters` is yours: pycraftcore passes it through untouched. `oc.env` always gives strings, so convert the values where you read them.
- `log` and `server` are required, like `connector` and `operation`. A service that serves no HTTP API writes `server: {}`.

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

- The third column is `request_id_context`. In a web service, `RequestIDMiddleware` (`pycraftcore.web.middleware`, added for you by the web toolkits) sets it from the `X-Request-ID` header; every line logged during that request shows it, `-` otherwise. Don't write it in your messages.
- Uvicorn's and Granian's worker logs use the same format; chatty libraries (httpx, mcp, pymongo…) stay at `WARNING`.
- Calling `configure_logging` again replaces the handler rather than adding a second one.

### Telemetry

```python
from pycraftcore.application_configuration.enum import RunTypeEnvironment
from pycraftcore.telemetry.adapter import OpenTelemetryProvider

telemetry = OpenTelemetryProvider(
    service_name="my-service",
    environment=RunTypeEnvironment.debug,
    otlp_endpoint="<collector-host>:<port>",  # None: nothing is exported
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
    retry=RetrySettings(
        retry_count=3, retry_delay=1, max_retry_delay=20, should_retry=is_retryable
    ),
    circuit_breaker=CircuitBreakerSettings(
        failure_threshold=3, recovery_timeout=30, is_excluded=is_business_error, name="weather"
    ),
)
client = ResilientTransportFactory(
    settings=settings, trace_manager=tracer, logger=logger
).create_async_client()
```

`client` is an `httpx.AsyncClient`: pass it to any library that accepts one.

### Serving an HTTP API

Pick a framework and write your routes with its own features: msgspec Structs and dependency injection with Litestar, pydantic and `Depends` with FastAPI, BlackSheep's binders and services. pycraftcore gives every framework the same toolkit, so what each service would otherwise repeat is done once: the request id, CORS, the API documentation, one base path for everything, `{"detail": …}` errors, the actuator, and server-sent events that stop when the client leaves.

```python
import msgspec
from litestar import get, post
from litestar.params import JSONBody
from litestar.response import Stream

from pycraftcore.web.actuator import Actuator
from pycraftcore.web.schema import ApiSettings
from pycraftcore.web.sse import EVENT_STREAM_MEDIA_TYPE, with_heartbeat
from pycraftcore.web_litestar import actuator_router, create_app, detail_handler, event_stream


class Order(msgspec.Struct):
    reference: str


@post("/v1/orders", status_code=200)
async def place(data: JSONBody[Order]) -> Order:
    return await orders.place(data)


@get("/v1/orders/updates", media_type=EVENT_STREAM_MEDIA_TYPE)
async def updates() -> Stream:
    return event_stream(with_heartbeat(orders.updates(), every=15.0))


api = ApiSettings(
    title="orders-api", version="1.4.0", base_path="/orders-api", docs=True, cors_origins=("*",)
)
actuator = Actuator("orders-api", "1.4.0", "staging", "team@example.com", is_ready=lambda: ready)

app = create_app(
    api,
    routes=[place, updates, actuator_router(actuator)],
    lifespan=boot_and_shutdown,
    exception_handlers={OutOfStock: detail_handler(503)},
    debug=False,
)
```

Each toolkit — `pycraftcore.web_litestar`, `web_fastapi`, `web_blacksheep` — has the same four functions, with the framework's own types:

| Function | What it gives you |
|---|---|
| `create_app(api, routes=…, lifespan=…, middleware=…, exception_handlers=…, **options)` | The framework's app: your routes under `api.base_path`, `RequestIDMiddleware` first, CORS from `api.cors_origins`, and when `api.docs` is on Swagger UI at `{base_path}/docs` and the schema at `{base_path}/docs/openapi.json` (no documentation otherwise). Every other option (above, `debug`) goes to the framework unchanged and wins over pycraftcore's defaults |
| `actuator_router(actuator)` | `/actuator/health`, `/health/liveness`, `/health/readiness` (503 until `is_ready()` is true) and `/info`, as a native router |
| `event_stream(frames)` | A native `text/event-stream` response with the stream headers. When the client leaves, the stream stops and your generator's `finally` runs |
| `detail_handler(status_code)` | A native exception handler answering `{"detail": "<message>"}` with that status |

- **`routes`** takes what the framework mounts: Litestar route handlers, controllers and routers; FastAPI `APIRouter`s; BlackSheep `Router`s.
- **`lifespan`** is a plain async context manager (start and stop your pools and clients); routes get what it builds through the framework's dependency injection.
- **`base_path`** (empty by default) puts every route under a prefix, the actuator and the documentation included: above, `POST /orders-api/v1/orders`. Use it when a gateway forwards a path prefix without removing it. It starts with `/` and does not end with one, otherwise `ApiSettings` raises `ValueError`.
- **From the configuration**: a server in `<env>/server/*.yml` gives `ApiSettings(title=server.name, version=…, base_path=server.base_path, docs=server.docs, cors_origins=server.cors_origins)`.
- **Invalid bodies** are answered the framework's way: FastAPI 422, Litestar and BlackSheep 400.

What each framework asks of your routes:

- **Litestar**: declare the body as `data: JSONBody[Model]`, and give event-stream routes `media_type=EVENT_STREAM_MEDIA_TYPE` so the documentation shows it. A POST answers 201 unless you set `status_code`.
- **FastAPI**: give event-stream routes `response_class=EventStreamResponse` (from `pycraftcore.web_fastapi`) so the documentation shows `text/event-stream`.
- **BlackSheep**: document statuses and media types with BlackSheep's `@docs(...)` from `openapi_handler(api)`, and pass that handler to `create_app(openapi=…)`. `event_stream(frames, request)` also takes the request: BlackSheep does not notice a client leaving an idle stream, so the stream checks `request.is_disconnected()` every second. `/docs` redirects to `/docs/`. `create_app` returns the app wrapped in `RequestIDMiddleware`, so configure the application through `create_app`'s arguments.

Long silences in an event stream make proxies close the connection. `with_heartbeat` (`pycraftcore.web.sse`) sends an SSE comment (`: heartbeat`) whenever the stream has been quiet for `every` seconds; clients ignore it. It is built on `with_idle_ticks(source, every)` (`pycraftcore.web.streaming`), which yields the source's items plus an `IDLE` marker each time nothing arrived in time. Closing it closes the source, even while it is waiting.

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
print(CodeResult.from_stdout(output.stdout).value)  # 1.4142135623730951
```

- The code runs in its own process; only the modules in `PYTHON_ALLOWLIST` can be imported (pandas, numpy, matplotlib, datetime…).
- `working_directory` in `SafeCodeSettings` confines file access to one folder.
- With a `HostBridgeServer`, the code can call functions of your service as if they were local — for example, a tool service can let sandboxed code call its other tools.
- When the code fails, `output.stderr` holds its traceback, limited to the code's own lines: each frame with its line number and source line, then the error. Internal frames (the sandbox runner, the libraries it calls) are left out. Whatever the code printed before failing stays in `output.stdout`.

  ```text
  Traceback (most recent call last):
    File "<sandbox>", line 3, in <module>
      value = rows[5]
              ~~~~^^^
  IndexError: list index out of range
  ```

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
4. Declare its third-party packages as an extra named after the module in `[project.optional-dependencies]` (pull in other modules with `pycraftcore[<module>]`). Then add it to `all`, to the [Install](#install) table, and to the `extras` matrix in `.github/workflows/cicd.yml`, which installs each extra alone and imports its package.
5. Add tests under `tests/<module>/`, and the module to [What's inside](#whats-inside) — with a short example under Using pycraftcore if services will use it directly.

### Adding a web framework

1. Create `pycraftcore/web_<name>/` with the modules the other toolkits have, using the framework's own types: `app_factory.create_app`, `actuator_router`, `event_stream` and `detail_handler`. `create_app` puts the routes under `api.base_path`, adds `RequestIDMiddleware`, CORS and the documentation from `ApiSettings`, runs the `lifespan`, and passes every other option to the framework.
2. Add the extra `web_<name> = ["<framework>", "pycraftcore[web]"]`, then add it to `all`, to the [Install](#install) table and to the CI `extras` matrix.
3. Write the test orders app in the framework's own style in `tests/web/apps/<name>_orders.py` (start from one of the others) and add it to `EVERY_TOOLKIT` in `tests/web/apps/__init__.py`. The shared tests then check it like the others: routes and bodies, request id, statuses, errors, event streams and client disconnect, CORS, base path, documentation, actuator and lifespan.

### Tests and checks

```bash
make install_dev    # uv sync --group dev --all-extras
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
4. Raise the minimum version in the services that need the change (`pycraftcore[<extras>]>=…` in their `pyproject.toml`), then `uv lock --upgrade-package pycraftcore`.

To work on pycraftcore and a service at the same time, point the service at your checkout with an editable path dependency in its `pyproject.toml`: `pycraftcore = { path = "../pycraftcore", editable = true }` under `[tool.uv.sources]`.
