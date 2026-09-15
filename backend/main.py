"""FastAPI 入口：挂载 B 模块 /api/draft，并开好 CORS。"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.draft.router import router as draft_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="知答 · 草稿生成后端（B 模块）",
    version="0.1.0",
    description="POST /api/draft — 证据不足时宁可不答，绝不硬编。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(draft_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
