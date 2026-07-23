"""CodeMemory Backend API — FastAPI server.

Reads from the existing codememory index.json and .md files.
Does NOT modify src/codememory/ internal logic.

R16-A1: Endpoints split into routers/ by business domain.
server.py retains only app creation, middleware, and router mounting.
R17-T1: Migrated from deprecated @app.on_event("startup") to lifespan.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# Ensure codememory package is importable
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Ensure backend modules are importable
_BACKEND = Path(__file__).resolve().parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Import shared state from shared.py (single source of truth for ContextVar etc.)
from shared import (
    current_dataset as _current_dataset,
    get_available_datasets as _get_available_datasets,
    get_dataset_records as _get_dataset_records,
    get_default_dataset_name as _get_default_dataset_name,
    resolve_root as _resolve_root,
)

# ---------------------------------------------------------------------------
# Lifespan (R17-T1: replaces deprecated @app.on_event("startup"))
# ---------------------------------------------------------------------------

from codememory.index import reindex as _cm_reindex


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Reindex contained demo datasets without mutating external instances."""
    logger = logging.getLogger("codememory.startup")
    for dataset in _get_dataset_records():
        if dataset.source != "demo":
            continue
        try:
            _cm_reindex(dataset.root)
            logger.info("Reindexed %s (%d memories)", dataset.name, dataset.memory_count)
        except Exception as exc:
            logger.error("Failed to reindex %s: %s", dataset.name, exc)
    yield


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(title="CodeMemory API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-request dataset context middleware
# R17-CR1: exempt paths must not write ContextVar (the /api/datasets endpoint
# uses DEFAULT_DATASET directly to return the server's real default, not
# whatever the client sent in a header).
class _DatasetContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        is_exempt = path in ("/", "/api/datasets", "/api/datasets/switch", "/docs", "/openapi.json")
        dataset = request.headers.get("X-Codememory-Dataset", "")
        token = None
        if dataset and dataset.strip() and not is_exempt:
            try:
                _resolve_root(dataset)
            except ValueError:
                datasets = _get_available_datasets()
                names = [d["name"] for d in datasets]
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": (
                            "Invalid X-Codememory-Dataset alias. "
                            f"Available datasets: {', '.join(names) if names else 'none found'}"
                        ),
                    },
                )
            token = _current_dataset.set(dataset)
        elif not is_exempt and path.startswith("/api/"):
            datasets = _get_available_datasets()
            names = [d["name"] for d in datasets]
            return JSONResponse(
                status_code=400,
                content={
                    "detail": (
                        "X-Codememory-Dataset header is required. "
                        f"Available datasets: {', '.join(names) if names else 'none found'}"
                    ),
                },
            )
        try:
            return await call_next(request)
        finally:
            if token is not None:
                _current_dataset.reset(token)


app.add_middleware(_DatasetContextMiddleware)


# ---------------------------------------------------------------------------
# Router mounting (R16-A1)
# ---------------------------------------------------------------------------

from routers.memories import router as memories_router
from routers.search import router as search_router
from routers.sources import router as sources_router
from routers.stats import router as stats_router
from routers.reviews import router as reviews_router
from routers.personal import router as personal_router

app.include_router(memories_router)
app.include_router(search_router)
app.include_router(sources_router)
app.include_router(stats_router)
app.include_router(reviews_router)
app.include_router(personal_router)

# Ordering note: include_router places routes in registration order.
# The generic GET /api/memories/{memory_id:path} and the backlinks route
# in memories_router must be registered in the correct order to avoid
# route capture issues — this is handled within the module itself since
# FastAPI resolves routes by specificity within a single router.


# ---------------------------------------------------------------------------
# Root health endpoint
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    datasets = _get_available_datasets()
    return {
        "service": "CodeMemory API",
        "version": "0.1.0",
        "default_dataset": _get_default_dataset_name(),
        "available_datasets": [d["name"] for d in datasets],
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    print(f"CodeMemory API starting on http://localhost:{port}")
    default_dataset = _get_default_dataset_name()
    print(f"Default dataset: {default_dataset} ({_resolve_root(default_dataset)})")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
