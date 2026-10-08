import asyncio
import http
import socket
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import RootModel

_HOST = "127.0.0.1"
_SERVER_START_POLL_INTERVAL = 0.01


def _make_app(flip_string: Callable[[str], str], always_500: bool, fail_first_n: int) -> FastAPI:
    app = FastAPI()
    request_count = 0

    @app.post("/flip")
    async def flip(request: RootModel[list[str]]):
        nonlocal request_count
        request_count += 1
        if always_500 or request_count <= fail_first_n:
            return JSONResponse(
                status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"detail": "Controlled server error"},
            )
        return [flip_string(s) for s in request.root]

    return app


@asynccontextmanager
async def controlled_flip_server(
    flip_string: Callable[[str], str] = lambda s: s[::-1],
    always_500: bool = False,
    fail_first_n: int = 0,
) -> AsyncIterator[str]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((_HOST, 0))
        port = sock.getsockname()[1]

    config = uvicorn.Config(_make_app(flip_string, always_500, fail_first_n), host=_HOST, port=port, log_level="error")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    while not server.started:
        await asyncio.sleep(_SERVER_START_POLL_INTERVAL)

    try:
        yield f"http://{_HOST}:{port}"
    finally:
        server.should_exit = True
        await task
