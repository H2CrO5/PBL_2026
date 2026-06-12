"""FastAPI application entry point for the teacher module."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import admin, analytics, auth, materials, questions, students
from db.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Teacher Education System API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(materials.router)
app.include_router(questions.router)
app.include_router(analytics.router)
app.include_router(students.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
