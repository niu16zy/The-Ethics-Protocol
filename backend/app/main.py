from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.dependencies import app_repository
from backend.app.api.routes import search, sessions, status, users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app_repository().initialize()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="The Ethics Protocol API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^http://(127\.0\.0\.1|localhost):\d+$",
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    app.include_router(users.router)
    app.include_router(sessions.router)
    app.include_router(search.router)
    app.include_router(status.router)
    return app


app = create_app()
