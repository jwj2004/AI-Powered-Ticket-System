"""
知答 MVP · FastAPI 入口
A: lookup / retrieve / feedback
B: draft
C: 健康检查 + CORS + 前端联调入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.draft.router import router as draft_router

from app.core.config import settings
from app.core.logger import log
from app.api import lookup_router

app = FastAPI(
    title=settings.app_name,
    description="知答 MVP - 数据检索后端",
    version="0.1.0",
)

# CORS - 允许油猴脚本 / Vue 前端跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 A 的路由（lookup / retrieve / feedback）
app.include_router(lookup_router)
# B 模块：真实草稿生成（retrieve → build_context → llm_generate）
app.include_router(draft_router)


# ---------- 健康检查 ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "zhida-mvp", "version": "0.1"}


@app.on_event("startup")
async def startup_event():
    log.success(f"{settings.app_name} 启动成功")
    log.info(f"API 文档: http://127.0.0.1:8000/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
