"""
知答 MVP · FastAPI 入口（C 骨架 + B 草稿路由）
C 维护骨架与 CORS；B 挂载真实 POST /api/draft。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.draft.router import router as draft_router

app = FastAPI(title="知答 MVP", version="0.1")

# 开发期允许所有来源（油猴脚本从任意页面 fetch localhost:8000）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# B 模块：真实草稿生成（retrieve → build_context → llm_generate）
app.include_router(draft_router)


# ---------- 健康检查 ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "zhida-mvp", "version": "0.1"}


# ---------- 1. 错误码秒查（A 实现，当前 mock） ----------
@app.get("/api/lookup")
def lookup(code: str = ""):
    # TODO(A): 查 error_code 表，按 code 精确匹配
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
