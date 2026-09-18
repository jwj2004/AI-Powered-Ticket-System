"""知答 · B 模块 FastAPI 入口：生成与编排（LangGraph + /api/chat）。"""

from __future__ import annotations

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers import router as b_router
from backend import store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.init_db()
    yield


app = FastAPI(
    title="知答 · 生成与编排（B 模块）",
    version="0.3.0",
    description="企业知识库问答 Agent：POST /api/chat 支持 JSON 与 SSE 流式。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(b_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "zhida-b", "version": "0.3"}
