"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import card_sets, cards, images, ownership, search

app = FastAPI(
    title="Yu-Gi-Oh Rush Duel Checklist",
    version="0.1.0",
)

# CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(card_sets.router)
app.include_router(cards.router)
app.include_router(ownership.router)
app.include_router(images.router)
app.include_router(search.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
