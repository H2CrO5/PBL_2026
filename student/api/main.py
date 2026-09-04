"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import json
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    admin,
    assignments,
    auth,
    chat,
    dashboard,
    integration,
    materials,
    students,
    submissions,
)
from db.database import create_tables
from config import CORS_ORIGINS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    create_tables()
    yield


app = FastAPI(
    title="Student Education System API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_log(request: Request, call_next):
    """Emit privacy-safe structured request metrics for local/CloudWatch logs."""
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logging.getLogger("classpilot.student").info(json.dumps({
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": round((time.perf_counter() - started) * 1000, 1),
    }))
    return response

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(assignments.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(integration.router)
app.include_router(materials.router)
app.include_router(students.router)
app.include_router(submissions.router)


@app.get("/health")
def health():
    return {"status": "ok"}
