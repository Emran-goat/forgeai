"""ForgeAI — Hardware-Aware AI Model Optimization Platform."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.api.models import router as models_router
from backend.api.optimizations import router as optimizations_router
from backend.api.candidates import router as candidates_router
from backend.api.benchmarks import router as benchmarks_router
from backend.api.exports import router as exports_router
from backend.api.hardware import router as hardware_router
from backend.api.websocket import router as websocket_router
from backend.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown."""
    await init_db()
    yield


app = FastAPI(
    title="ForgeAI",
    version="0.1.0",
    description="Hardware-Aware AI Model Optimization Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models_router, prefix="/api/v1")
app.include_router(optimizations_router, prefix="/api/v1")
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(benchmarks_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(hardware_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
