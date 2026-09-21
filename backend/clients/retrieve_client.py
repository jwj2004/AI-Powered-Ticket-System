"""封装 A 的检索 / 错误码直查（mock 与真实可切换）。"""

from __future__ import annotations

import re
from typing import Any, Optional

import httpx

from backend.config import get_settings

# mock 文档块：完整版 RAG 的知识来源（A 的 FAISS 未就绪时用）
_MOCK_CHUNKS: list[dict[str, Any]] = [
    {
        "document_id": 1,
        "title": "订单导出超时排查",
        "chunk_index": 3,
        "content": (
            "订单导出超时通常是因为一次导出超过 5 万条。"
            "建议按周拆分导出，避开高峰时段，并检查导出任务是否已在后台排队。"
        ),
        "score": 0.92,
        "spaces": ["客服文档", "运维文档"],
        "keywords": ("导出", "超时", "订单导出", "5万", "五万"),
    },
    {
        "document_id": 2,
        "title": "支付回调超时排查手册",
        "chunk_index": 1,
        "content": (
            "PAY_CALLBACK_TIMEOUT：买家已付款但订单仍待支付。"
            "先在支付商户后台确认该笔是否已扣款；若已支付，在商城执行补单，"
            "并核对该店铺版本的回调地址是否与商户平台一致。"
        ),
        "score": 0.90,
        "spaces": ["客服文档"],
        "keywords": ("支付", "回调", "待支付", "微信", "付款", "PAY_CALLBACK"),
    },
    {
        "document_id": 3,
        "title": "优惠券核销失败",
        "chunk_index": 0,
        "content": (
            "优惠券核销失败常见原因是活动叠加冲突或券已过期。"
            "先核对券批次状态，关闭冲突促销后再重试核销。"
        ),
        "score": 0.88,
        "spaces": ["客服文档"],
        "keywords": ("优惠券", "核销", "券"),
    },
    {
        "document_id": 4,
        "title": "物流轨迹不更新",
        "chunk_index": 0,
        "content": (
            "物流轨迹推送失败时，先在承运商后台确认已揽收，"
            "再核对店铺物流订阅开关与回调地址。"
        ),
        "score": 0.86,
        "spaces": ["运维文档"],
        "keywords": ("物流", "轨迹", "揽收", "运单"),
    },
    {
        "document_id": 5,
        "title": "新手指南-如何提交工单",
        "chunk_index": 0,
        "content": (
            "新人提交工单时请写清：店铺编号、发生时间、错误现象、是否已重启。"
            "不要在工单里发送客户手机号等隐私信息。"
        ),
        "score": 0.84,
        "spaces": ["新手指南"],
        "keywords": ("工单", "新人", "怎么提单", "提交工单", "新手"),
    },
]

_ERROR_CODE_RE = re.compile(r"\b([A-Z][A-Z0-9_]{5,})\b")

_MOCK_LOOKUP: dict[str, dict[str, Any]] = {
    "PAY_CALLBACK_TIMEOUT": {
        "code": "PAY_CALLBACK_TIMEOUT",
        "name": "支付回调超时",
        "solution": (
            "先在支付商户后台手动查询该笔订单支付状态；"
            "若已支付，在商城后台对该订单执行补单/手动确认收款；"
            "同时核对当前店铺版本的支付回调地址是否与商户平台配置一致。"
        ),
    }
}

_ROLE_SPACES = {
    "admin": {"客服文档", "运维文档", "新手指南"},
    "ops": {"客服文档", "运维文档"},
    "newbie": {"新手指南"},
}


def extract_error_code(text: str) -> Optional[str]:
    match = _ERROR_CODE_RE.search(text or "")
    return match.group(1) if match else None


def spaces_for_role(role: str) -> set[str]:
    return _ROLE_SPACES.get(role, _ROLE_SPACES["ops"])


class RetrieveClient:
    """文档块 top5 + 错误码 lookup。"""

    def __init__(self, settings=None) -> None:
        self.settings = settings or get_settings()

    def lookup(self, code: str) -> Optional[dict[str, Any]]:
        if not code:
            return None
        if self.settings.use_mock_retrieve:
            data = _MOCK_LOOKUP.get(code)
            return dict(data) if data else None
        url = f"{self.settings.retrieve_base_url.rstrip('/')}/api/lookup"
        try:
            with httpx.Client(timeout=self.settings.retrieve_timeout_seconds) as client:
                resp = client.get(url, params={"code": code})
                if resp.status_code != 200:
                    return None
                data = resp.json()
                if data.get("code") in {None, "", "NOT_EXIST"}:
                    return None
                return {
                    "code": data.get("code"),
                    "name": data.get("name") or "",
                    "solution": data.get("solution") or "",
                }
        except httpx.HTTPError:
            return None

    def retrieve_chunks(
        self,
        query: str,
        *,
        role: str = "ops",
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        pool = max(top_k, int(getattr(self.settings, "retrieve_candidate_k", top_k) or top_k))
        if self.settings.use_mock_retrieve:
            return self._mock_chunks(query, role=role, top_k=pool)
        return self._http_chunks(query, role=role, top_k=pool)

    def reindex_document(self, document_id: int) -> bool:
        """管理员补文档后通知 A 重新向量化；A 未就绪时静默跳过。"""
        if self.settings.use_mock_retrieve:
            return True
        url = f"{self.settings.retrieve_base_url.rstrip('/')}/api/documents/{document_id}/reindex"
        try:
            with httpx.Client(timeout=self.settings.retrieve_timeout_seconds) as client:
                resp = client.post(url)
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def _mock_chunks(self, query: str, *, role: str, top_k: int) -> list[dict[str, Any]]:
        allowed = spaces_for_role(role)
        scored: list[dict[str, Any]] = []
        q = query or ""
        for item in _MOCK_CHUNKS:
            if not set(item["spaces"]) & allowed:
                continue
            hits = sum(1 for kw in item["keywords"] if kw.lower() in q.lower())
            # 有关键词命中视为向量检索高分；无命中仍进候选池，交给 BM25 融合
            if hits > 0:
                score = min(0.99, float(item["score"]) + 0.01 * hits)
            else:
                score = round(0.12 + 0.02 * min(hits, 3), 4)
            scored.append(
                {
                    "document_id": item["document_id"],
                    "title": item["title"],
                    "chunk_index": item["chunk_index"],
                    "content": item["content"],
                    "score": round(score, 4),
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        limit = max(1, min(top_k, len(scored))) if scored else 0
        return scored[:limit] if scored else []

    def _http_chunks(self, query: str, *, role: str, top_k: int) -> list[dict[str, Any]]:
        url = f"{self.settings.retrieve_base_url.rstrip('/')}/api/retrieve"
        payload = {"query": query, "top_k": top_k, "role": role}
        try:
            with httpx.Client(timeout=self.settings.retrieve_timeout_seconds) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError:
            return []

        limit = max(1, min(top_k, 20))
        if data.get("chunks"):
            chunks = []
            for item in data["chunks"][:limit]:
                chunks.append(
                    {
                        "document_id": item.get("document_id"),
                        "title": item.get("title") or "",
                        "chunk_index": int(item.get("chunk_index") or 0),
                        "content": item.get("content") or item.get("text") or "",
                        "score": float(item.get("score") or 0.0),
                    }
                )
            return chunks

        # 兼容工单副驾旧 retrieve：tickets → 临时当成文档块
        tickets = data.get("tickets") or []
        chunks = []
        for idx, item in enumerate(tickets[:limit]):
            chunks.append(
                {
                    "document_id": idx + 1,
                    "title": item.get("ticket_id") or f"ticket-{idx}",
                    "chunk_index": 0,
                    "content": item.get("solution_text") or "",
                    "score": float(item.get("score") or 0.0),
                }
            )
        return chunks
