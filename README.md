# flip-service

A Temporal-based service that reverses strings via an external HTTP flip server.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11 or 3.12 | `python --version` |
| Poetry | any recent | `poetry --version` |
| Temporal CLI | latest | see install below |

**Temporal CLI** — install via Homebrew or the official script:

```bash
brew install temporal
# or
curl -sSf https://temporal.download/cli.sh | sh
```

Full install documentation: https://docs.temporal.io/cli

All Python dependencies (including `httpx`, `temporalio`, `fastapi`, `uvicorn`) are managed by Poetry and installed in the setup step below.

---

## Setup

```bash
poetry install
```

---

## Running the project

The service requires four processes running concurrently. Start them in this order, each in its own terminal.

**1. Temporal development server**

```bash
temporal server start-dev
```

**2. Flip server** (the external HTTP string-flipping service)

```bash
poetry run python server.py
```

**3. Worker** (executes workflow and activity tasks)

```bash
poetry run python worker.py
```

**4. Client** (submits a flip job and prints results)

```bash
poetry run python client.py <string> [<string> ...]
```

### Example

```bash
poetry run python client.py hello world
```

Expected output:

```
Progress: 0 strings flipped, 0 HTTP 200s
Progress: 2 strings flipped, 2 HTTP 200s
olleh dlrow
```

The progress lines are printed every 2 seconds while the workflow runs. The final line contains the flipped strings separated by spaces.

The flip server introduces randomness: a 10% chance of an immediate HTTP 500 per request, and a 10% per-string chance of returning `-` instead of the flipped result. Both cases are retried automatically by the workflow. With retries, you may see the HTTP 200 counter exceed the strings-flipped counter before both settle at completion.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `TEMPORAL_HOST` | `localhost:7233` | Address of the Temporal server, used by the worker and client |
| `FLIP_SERVER_URL` | `http://127.0.0.1:8000` | Base URL of the flip HTTP server, used by the worker |

---

## Testing

There are three test layers. Run them independently.

**Unit tests** — mock all I/O; fast, no external processes required:

```bash
poetry run pytest tests/test_validation.py tests/test_activities.py tests/test_workflow.py tests/test_client.py
```

**Component tests** — real HTTP calls against a local in-process fixture server; no Temporal:

```bash
poetry run pytest tests/test_activities_component.py
```

**Integration tests** — full stack with a real embedded Temporal server and real activity code against the fixture server:

```bash
poetry run pytest tests/test_workflow_integration.py
```

> Integration tests start an embedded Temporal server and are slower than the other layers (~10–30 seconds total).

---

## Manual smoke test

This exercises the full stack end-to-end using the real flip server, including its randomness and retry behaviour.

1. Start all four processes as described in [Running the project](#running-the-project).
2. Run the client with a few strings:

```bash
poetry run python client.py hello world foo bar
```

3. Observe the progress output. Because the server has a 10% per-request failure rate and a 10% per-string partial failure rate, some runs will show the HTTP 200 counter temporarily exceeding the strings-flipped counter before resolving. All strings will eventually be flipped and printed on the final line.
