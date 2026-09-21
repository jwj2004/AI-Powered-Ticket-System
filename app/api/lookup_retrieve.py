"""
A 模块的 API 路由：错误码查询 + 内部检索 + 反馈埋点
D2 实现完整逻辑，D1 先搭好骨架
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logger import log
from app.schemas import (
    LookupResponse,
    RetrieveRequest,
    RetrieveResponse,
    RetrieveTicket,
)
from app.services import (
    lookup_error_code,
    detect_error_code,
    VectorRetriever,
    record_query_log,
    update_feedback,
)

router = APIRouter(prefix="/api", tags=["数据检索 (A模块)"])


# ============================================================
# 一、错误码秒查 GET /api/lookup
# ============================================================
@router.get("/lookup", response_model=LookupResponse)
def api_lookup(code: str, db: Session = Depends(get_db)):
    """
    错误码精确查询

    - 命中：返回完整错误码详情
    - 未命中：返回 code=NOT_EXIST + 空字段（**200，不是404**）
    """
    log.info(f"[lookup] 查询错误码: {code}")
    result = lookup_error_code(code)

    if result:
        return LookupResponse(**result)

    # 未命中：契约要求返回 200 + 空字段
    return LookupResponse(code="NOT_EXIST")


# ============================================================
# 二、内部检索接口 POST /api/retrieve（B 调用，不对外）
# ============================================================
@router.post("/retrieve", response_model=RetrieveResponse)
def api_retrieve(req: RetrieveRequest, db: Session = Depends(get_db)):
    """
    内部向量检索接口（B 调 A）

    1. 先从文本里识别错误码（精确匹配）
    2. 再用 FAISS 向量召回 top_k 相似工单
    """
    log.info(f"[retrieve] query={req.query[:50]}, customer_id={req.customer_id}")

    # Step 1: 错误码识别
    error_code = detect_error_code(req.query)

    # Step 2: 向量检索
    VectorRetriever.ensure_init()
    search_results = VectorRetriever.search(req.query, top_k=req.top_k)

    # Step 3: 组装工单详情
    from app.models import Ticket
    tickets = []
    for ticket_id, score in search_results:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if ticket:
            # 如果工单本身有 error_code 但文本没匹配到，也记录一下
            solution = ticket.solution_text or ""
            # 如果工单没有 solution_text，用错误码表里的 solution 兜底
            if not solution and ticket.error_code:
                ec = lookup_error_code(ticket.error_code)
                if ec:
                    solution = ec["solution"]

            tickets.append(
                RetrieveTicket(
                    ticket_id=ticket.ticket_id,
                    solution_text=solution,
                    score=round(score, 4),
                )
            )

    return RetrieveResponse(
        error_code=error_code,
        tickets=tickets,
    )


# ============================================================
# 三、反馈埋点 POST /api/feedback
# 已移至 app/api/chat.py，统一使用 message_id 字段（接口契约对齐）
# 此处保留 update_feedback 服务函数供 B 模块内部调用
# ============================================================
