"""CodeMemory Backend API — FastAPI server.

Reads from the existing codememory index.json and .md files.
Does NOT modify src/codememory/ internal logic.

R16-A1: Endpoints split into routers/ by business domain.
server.py retains only app creation, middleware, and router mounting.
"""

from __future__ import annotations

import json
import logging
import os
import sys
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
_DEFAULT_DATASET = os.environ.get("CODEMEMORY_DEFAULT_DATASET", "investment")

from contextvars import ContextVar

_current_dataset: ContextVar[str] = ContextVar("current_dataset", default=_DEFAULT_DATASET)


def _resolve_root(dataset_name: str) -> Path:
    if not dataset_name or not dataset_name.strip():
        dataset_name = _DEFAULT_DATASET
    return (_EXAMPLES_DIR / dataset_name).resolve()


def _get_available_datasets() -> list[dict[str, str]]:
    datasets: list[dict[str, str]] = []
    if not _EXAMPLES_DIR.exists():
        return datasets
    for entry in sorted(_EXAMPLES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        idx = entry / ".codememory" / "index.json"
        if idx.exists():
            try:
                with open(idx, "r", encoding="utf-8") as f:
                    data = json.load(f)
                count = len(data.get("memories", {}))
            except Exception:
                count = 0
            datasets.append({
                "name": entry.name,
                "path": str(entry.resolve()),
                "memory_count": count,
            })
    return datasets


# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(title="CodeMemory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-request dataset context middleware
class _DatasetContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        is_exempt = path in ("/", "/api/datasets", "/docs", "/openapi.json")
        dataset = request.headers.get("X-Codememory-Dataset", "")
        if dataset and dataset.strip():
            _current_dataset.set(dataset)
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
        response = await call_next(request)
        return response


app.add_middleware(_DatasetContextMiddleware)


# ---------------------------------------------------------------------------
# Router mounting (R16-A1)
# ---------------------------------------------------------------------------

from routers.memories import router as memories_router
from routers.search import router as search_router
from routers.stats import router as stats_router

app.include_router(memories_router)
app.include_router(search_router)
app.include_router(stats_router)

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
        "default_dataset": _DEFAULT_DATASET,
        "available_datasets": [d["name"] for d in datasets],
    }


# ---------------------------------------------------------------------------
# Startup: reindex all known datasets
# ---------------------------------------------------------------------------

from codememory.index import reindex as _cm_reindex


@app.on_event("startup")
def _startup_reindex():
    """Reindex all known datasets on startup."""
    logger = logging.getLogger("codememory.startup")
    datasets = _get_available_datasets()
    for ds in datasets:
        try:
            root_path = Path(ds["path"])
            _cm_reindex(root_path)
            logger.info("Reindexed %s (%d memories)", ds["name"], ds["memory_count"])
        except Exception as exc:
            logger.error("Failed to reindex %s: %s", ds["name"], exc)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    print(f"CodeMemory API starting on http://localhost:8000")
    print(f"Default dataset: {_DEFAULT_DATASET} ({_resolve_root(_DEFAULT_DATASET)})")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=False)
