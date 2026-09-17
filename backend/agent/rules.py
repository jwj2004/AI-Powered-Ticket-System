"""路由规则与「无引用不输出」。"""

from __future__ import annotations

import re
from typing import Any, Optional

from backend.config import get_settings
from backend.clients.retrieve_client import extract_error_code

LOW_MESSAGE = "这个问题我没找到可靠依据，已记录，管理员补全后会通知你。"
REFUSE_MESSAGE = "这个问题不属于内部知识范围，我无法给出可靠依据。"

_CHITCHAT_RE = re.compile(
    r"(天气|写诗|一首诗|笑话|讲个故事|你是谁|今天星期|帮我聊天|谈恋爱)",
    re.I,
)
_KNOWLEDGE_RE = re.compile(
    r"(订单|导出|支付|回调|优惠券|核销|物流|工单|错误码|超时|登录|配置|文档|版本|排查|失败)",
)


def classify_route(question: str) -> str:
    """返回 lookup / rag / refuse。"""
    text = (question or "").strip()
    if not text:
        return "refuse"
    if extract_error_code(text):
        return "lookup"
    if _CHITCHAT_RE.search(text) and not _KNOWLEDGE_RE.search(text):
        return "refuse"
    if not _KNOWLEDGE_RE.search(text) and len(text) < 8:
        return "refuse"
    return "rag"


def chunks_are_strong(
    chunks: list[dict[str, Any]],
    high_score_threshold: Optional[float] = None,
) -> bool:
    if not chunks:
        return False
    threshold = (
        high_score_threshold
        if high_score_threshold is not None
        else get_settings().high_score_threshold
    )
    return any(float(c.get("score") or 0.0) >= threshold for c in chunks)


def citations_from_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for c in chunks[:5]:
        doc_id = c.get("document_id")
        if doc_id is None:
            continue
        items.append(
            {
                "document_id": int(doc_id),
                "title": c.get("title") or "",
                "chunk_index": int(c.get("chunk_index") or 0),
            }
        )
    return items
