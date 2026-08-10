from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.dependencies import app_repository
from backend.app.api.routes import search, sessions, status, users

FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


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

    if FRONTEND_DIST.is_dir():
        # Only present in the production Docker image, where the frontend is
        # pre-built; local dev serves it separately via `npm run dev`. A 404
        # handler (rather than a competing catch-all route) means it can
        # never shadow an unmatched /api/* request into a 405.
        app.mount(
            "/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets"
        )

        @app.exception_handler(StarletteHTTPException)
        async def spa_fallback(request: Request, exc: StarletteHTTPException):
            if exc.status_code == 404 and not request.url.path.startswith("/api"):
                return FileResponse(FRONTEND_DIST / "index.html")
            return await http_exception_handler(request, exc)

    return app


app = create_app()
