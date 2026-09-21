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
    RetrieveChunk,
    RetrieveRequest,
    RetrieveResponse,
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
    2. 再用文档 FAISS 召回 top_k 切块
    """
    log.info(f"[retrieve] query={req.query[:50]}, customer_id={req.customer_id}")

    error_code = detect_error_code(req.query)

    from app.models.document import Document
    from app.models.document_chunk import DocumentChunk

    search_results = VectorRetriever.search_documents(req.query, top_k=req.top_k)
    chunks = []
    for doc_id, chunk_index, score in search_results:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        chunk = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == doc_id,
                DocumentChunk.chunk_index == chunk_index,
            )
            .first()
        )
        if not doc or not chunk:
            continue
        chunks.append(
            RetrieveChunk(
                document_id=doc_id,
                title=doc.title or "",
                chunk_index=chunk_index,
                content=chunk.content or "",
                score=round(float(score), 4),
            )
        )
        log.info(
            f"[retrieve] hit doc={doc_id} chunk={chunk_index} score={score:.4f} title={doc.title}"
        )

    return RetrieveResponse(
        error_code=error_code,
        chunks=chunks,
    )


# ============================================================
# 三、反馈埋点 POST /api/feedback
# 已移至 app/api/chat.py，统一使用 message_id 字段（接口契约对齐）
# 此处保留 update_feedback 服务函数供 B 模块内部调用
# ============================================================
