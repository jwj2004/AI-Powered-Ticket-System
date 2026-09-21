"""封装 A 的 POST /api/retrieve（mock / 真实可切换）。"""

from __future__ import annotations

from typing import Any, Optional

import httpx

from backend.config import Settings, get_settings

# 错误码命中时的结构化 solution（质量兜底话术，对齐 error_code.solution）
_ERROR_CODE_SOLUTIONS: dict[str, str] = {
    "PAY_CALLBACK_TIMEOUT": (
        "先在支付商户后台手动查询该笔订单支付状态；"
        "若已支付，在商城后台对该订单执行「补单/手动确认收款」；"
        "同时核对当前店铺版本的支付回调地址是否与商户平台配置一致，"
        "并关注近 24 小时是否有版本升级导致回调路径变更。"
    ),
}

# D2 假证据：把「证据→草稿」链路跑通
_MOCK_TICKETS: list[dict[str, Any]] = [
    {
        "ticket_id": "T20260715001",
        "solution_text": (
            "同现象：微信已付款但订单待支付。核实为回调超时，"
            "商户后台已支付，后台补单后恢复；建议客户核对回调地址。"
        ),
        "score": 0.87,
    },
    {
        "ticket_id": "T20260721001",
        "solution_text": (
            "升级 v3.8.x 后回调路径变更导致通知丢失。"
            "更正商户平台回调 URL 并补单，问题关闭。"
        ),
        "score": 0.81,
    },
    {
        "ticket_id": "T20260803012",
        "solution_text": (
            "网络抖动导致异步通知丢失。指导客户在支付后台查单，"
            "商城侧执行手动确认收款，并开启回调重试。"
        ),
        "score": 0.76,
    },
]

_MOCK_CUSTOMER_VERSIONS: dict[str, str] = {
    "C001": "v3.7.2",
    "C002": "v3.8.0",
    "C003": "v3.8.5",
    "C004": "v4.1.0",
}


def _summarize_one_line(solution_text: str, max_len: int = 80) -> str:
    text = " ".join(solution_text.strip().split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


class RetrieveClient:
    """只暴露 retrieve()，内部按配置走 mock 或真实 HTTP。"""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def retrieve(
        self,
        query: str,
        customer_id: Optional[str] = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        if self.settings.use_mock_retrieve:
            return self._mock_retrieve(query, customer_id, top_k)
        return self._http_retrieve(query, customer_id, top_k)

    def get_customer_version(self, customer_id: Optional[str]) -> Optional[str]:
        """客户版本号（D3 可改为调 A 的 context 接口）。"""
        if not customer_id:
            return None
        if self.settings.use_mock_retrieve:
            return _MOCK_CUSTOMER_VERSIONS.get(customer_id)
        url = f"{self.settings.retrieve_base_url.rstrip('/')}/api/tickets/{customer_id}/context"
        try:
            with httpx.Client(timeout=self.settings.retrieve_timeout_seconds) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                version = data.get("version")
                return version if version else None
        except httpx.HTTPError:
            return None

    def get_error_code_solution(self, error_code: Optional[str]) -> Optional[str]:
        """错误码命中时的结构化 solution（mock 内置；真实模式接 /api/lookup）。"""
        if not error_code:
            return None
        if self.settings.use_mock_retrieve:
            return _ERROR_CODE_SOLUTIONS.get(error_code)
        url = f"{self.settings.retrieve_base_url.rstrip('/')}/api/lookup"
        try:
            with httpx.Client(timeout=self.settings.retrieve_timeout_seconds) as client:
                resp = client.get(url, params={"code": error_code})
                if resp.status_code != 200:
                    return None
                data = resp.json()
                if data.get("code") == "NOT_EXIST":
                    return None
                solution = data.get("solution") or None
                return solution if solution else None
        except httpx.HTTPError:
            return None

    def _mock_retrieve(
        self,
        query: str,
        customer_id: Optional[str],
        top_k: int,
    ) -> dict[str, Any]:
        """关键词触发假证据；无关问题返回空，用于验证「无引用不输出」。"""
        _ = customer_id
        keywords = ("付", "支付", "微信", "订单", "待支付", "回调", "PAY")
        if not any(k in query for k in keywords):
            return {"error_code": None, "tickets": []}

        tickets = []
        for item in _MOCK_TICKETS[: max(1, min(top_k, 3))]:
            tickets.append(
                {
                    "ticket_id": item["ticket_id"],
                    "solution_text": item["solution_text"],
                    "score": item["score"],
                    "summary": _summarize_one_line(item["solution_text"]),
                }
            )
        return {
            "error_code": "PAY_CALLBACK_TIMEOUT",
            "tickets": tickets,
        }

    def _http_retrieve(
        self,
        query: str,
        customer_id: Optional[str],
        top_k: int,
    ) -> dict[str, Any]:
        url = f"{self.settings.retrieve_base_url.rstrip('/')}/api/retrieve"
        payload = {
            "query": query,
            "customer_id": customer_id,
            "top_k": top_k,
        }
        with httpx.Client(timeout=self.settings.retrieve_timeout_seconds) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        tickets = []
        for item in (data.get("tickets") or [])[:3]:
            solution_text = item.get("solution_text") or ""
            tickets.append(
                {
                    "ticket_id": item.get("ticket_id"),
                    "solution_text": solution_text,
                    "score": float(item.get("score") or 0.0),
                    "summary": _summarize_one_line(solution_text),
                }
            )
        error_code = data.get("error_code")
        return {
            "error_code": error_code if error_code else None,
            "tickets": tickets,
        }


def retrieve(
    query: str,
    customer_id: Optional[str] = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """模块级便捷入口，供 service 直接调用。"""
    return RetrieveClient().retrieve(query, customer_id, top_k)
