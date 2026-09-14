"""
知答 MVP · C 板块后端骨架（mock 版）
D1 目标：三个接口返回契约里的 JSON，油猴脚本能调通。
A/B 后续把实现替换成真实逻辑，接口字段不动。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="知答 MVP", version="0.1")

# 开发期允许所有来源（油猴脚本从任意页面 fetch localhost:8000）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 健康检查 ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "zhida-mvp", "version": "0.1"}


# ---------- 1. 错误码秒查（A 实现，当前 mock） ----------
@app.get("/api/lookup")
def lookup(code: str = ""):
    # TODO(A): 查 error_code 表，按 code 精确匹配
    # 这里先返回 mock，保证前端能渲染
    return {
        "code": code or "PAY_CALLBACK_TIMEOUT",
        "name": "支付回调超时",
        "meaning": "买家已付款但商城订单长时间未变成已支付",
        "trigger_condition": "买家付款后 5 分钟内未收到支付平台异步通知",
        "causes": [
            "商户平台回调地址不通",
            "店铺刚升级过版本回调路径变更",
            "网络抖动导致通知丢失",
        ],
        "solution": "先在支付商户后台手动查询该笔订单支付状态确认真的已付款；检查回调地址是否与商户平台配置一致。",
        "related_versions": ["v4.1.0+"],
    }


# ---------- 2. 草稿生成（B 实现，当前 mock） ----------
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


# ---------- 3. 反馈埋点（A 实现表，C 上报） ----------
class FeedbackRequest(BaseModel):
    query_id: str
    copied: bool = False
    thumbs_down: bool = False


@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    # TODO(A): 写 query_log 表
    print(f"[feedback] query_id={req.query_id} copied={req.copied} thumbs_down={req.thumbs_down}")
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
