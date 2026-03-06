from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes_datasets import router as datasets_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_models import router as models_router
from backend.app.api.routes_results import router as results_router
from backend.app.api.routes_runs import router as runs_router

app = FastAPI(title="EdgeBench API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(models_router)
app.include_router(datasets_router)
app.include_router(runs_router)
app.include_router(results_router)


@app.get("/")
def root() -> dict[str, Any]:
    return {"ok": True, "name": "EdgeBench Backend"}
