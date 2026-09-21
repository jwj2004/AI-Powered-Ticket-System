"""「无引用不输出」硬规则与置信度判定。"""

from __future__ import annotations

from typing import Any, Optional

from backend.config import get_settings

LOW_MESSAGE = "未找到可靠依据，建议转二线处理"


def judge_confidence(
    error_code: Optional[str],
    tickets: list[dict[str, Any]],
    high_score_threshold: Optional[float] = None,
) -> str:
    """
    仅返回 high / low。
    - 命中错误码 → high
    - 存在分数 ≥ 阈值的相似工单 → high
    - 否则 → low
    """
    if error_code:
        return "high"
    threshold = (
        high_score_threshold
        if high_score_threshold is not None
        else get_settings().high_score_threshold
    )
    for ticket in tickets:
        score = float(ticket.get("score") or 0.0)
        if score >= threshold:
            return "high"
    return "low"


def should_refuse(error_code: Optional[str], tickets: list[dict[str, Any]]) -> bool:
    """检索为空或置信度为 low 时拒绝输出草稿。"""
    if not error_code and not tickets:
        return True
    return judge_confidence(error_code, tickets) == "low"


def low_confidence_response(query_id: str) -> dict[str, Any]:
    """契约规定的证据不足响应。"""
    return {
        "query_id": query_id,
        "error_code": None,
        "evidence": [],
        "draft": None,
        "confidence": "low",
        "message": LOW_MESSAGE,
    }
