"""
知答 MVP - 数据检索服务
A: lookup / retrieve / feedback（已实现）
B: draft（当前 mock，待 B 替换为 LLM 实现）
C: 健康检查 + 前端联调入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.core.config import settings
from app.core.logger import log
from app.api import lookup_router

app = FastAPI(
    title=settings.app_name,
    description="知答 MVP - 数据检索后端",
    version="0.1.0",
)

# CORS - 允许油猴脚本跨域调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 A 的路由（lookup / tickets_context / retrieve / feedback）
app.include_router(lookup_router)


# ---------- 健康检查 ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "zhida-mvp", "version": "0.1"}


# ---------- B 的接口：草稿生成（当前 mock，待 B 替换） ----------
class DraftRequest(BaseModel):
    raw_text: str
    customer_id: Optional[str] = None


@app.post("/api/draft")
def draft(req: DraftRequest):
    # TODO(B): 调 /api/retrieve 拿证据 → LLM 生成草稿 → 拼引用
    # TODO(B): 证据不足时返回 confidence=low, draft=null
    # query_id 契约要求必返，供前端复制时上报 /api/feedback
    return {
        "query_id": "q_mock_001",
        "error_code": "PAY_CALLBACK_TIMEOUT",
        "evidence": [
            {
                "ticket_id": "T20260715001",
                "summary": "同现象：微信付款后订单待支付，原因为回调路径升级后未更新",
            },
            {
                "ticket_id": "T20260721001",
                "summary": "付款订单卡待支付，手动点「同步支付状态」后恢复",
            },
        ],
        "draft": "您好，已为您核实该笔订单。您当前店铺版本为 v3.8.5，支付回调地址需在微信商户平台更新为最新路径。麻烦您先在微信商户后台确认该笔款项是否已实际扣账，如已扣账，我们会为您手动同步订单状态。",
        "confidence": "high",
    }


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
