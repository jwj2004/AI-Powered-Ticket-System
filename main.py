"""
知答 - 企业内部知识库智能问答 Agent
A: 数据与检索（auth/users/doc-spaces/documents/chat/conversations/gaps/notifications/dashboard/faq）
B: 生成与编排（LangGraph，待接入）
C: 前端与工程
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import log
from app.api import (
    lookup_retrieve,
    auth,
    users,
    doc_spaces,
    documents,
    chat,
    conversations,
    gaps,
    notifications,
    dashboard,
    faq,
    logs,
    stats,
)
from backend.routers import router as b_router

app = FastAPI(
    title=settings.app_name,
    description="知答 - 企业内部知识库智能问答 Agent",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A 模块路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(doc_spaces.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(gaps.router)
app.include_router(notifications.router)
app.include_router(dashboard.router)
app.include_router(faq.router)
app.include_router(lookup_retrieve.router)
app.include_router(logs.router)
app.include_router(stats.router)

# B 模块路由（LangGraph 问答编排）
app.include_router(b_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "zhida", "version": "0.3.0"}


@app.on_event("startup")
async def startup_event():
    log.success(f"{settings.app_name} 启动成功")
    log.info(f"API 文档: http://127.0.0.1:8000/docs")
    from app.services.document_service import ensure_chunk_type_column
    from app.services.vector_retriever import VectorRetriever

    ensure_chunk_type_column()
    from backend.config import get_settings as get_b_settings
    from backend import store

    b_settings = get_b_settings()
    log.info(f"B llm_api_key 长度: {len((b_settings.llm_api_key or '').strip())}")
    store.init_db()
    cleared = store.clear_hot_cache()
    log.info(f"热缓存已清空，删除 {cleared} 条")
    VectorRetriever.ensure_init()
    log.success("向量模型加载完成")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
