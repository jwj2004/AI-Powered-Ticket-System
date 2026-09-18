"""查询改写：检索前把口语问题收成检索词。"""

from __future__ import annotations

import logging
import re
from typing import Optional

from openai import OpenAI

from backend.config import get_settings

logger = logging.getLogger(__name__)

_FILLER = re.compile(
    r"(请问|怎么处理|怎么办|如何解决|如何处理|帮我看一下|一下|呢|啊|呀|吗|么)"
)
_SYNONYMS = (
    ("付了钱", "支付 付款 待支付 回调"),
    ("没更新", "超时 待支付 未到账"),
    ("用不了", "核销失败 报错"),
    ("轨迹不更新", "物流 揽收 推送失败"),
    ("导不出", "订单导出 超时"),
)


def _rule_rewrite(question: str) -> str:
    text = (question or "").strip()
    extra = []
    for src, dst in _SYNONYMS:
        if src in text:
            extra.append(dst)
    cleaned = _FILLER.sub(" ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if extra:
        return f"{cleaned} {' '.join(extra)}".strip()
    return cleaned or text


def rewrite_query(question: str, *, history: Optional[list[dict[str, str]]] = None) -> str:
    """有 LLM Key 时让模型改写成检索短句；否则用规则改写。"""
    base = _rule_rewrite(question)
    settings = get_settings()
    if not settings.llm_api_key:
        return base
    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=min(settings.llm_timeout_seconds, 6.0),
        )
        hist = ""
        if history:
            last = history[-2:]
            hist = "；".join(f"{x.get('role')}:{x.get('content')}" for x in last)
        resp = client.chat.completions.create(
            model=settings.llm_model,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "把用户问题改写成适合检索内部文档的短查询，保留关键实体和错误现象，不要回答问题。只输出改写后的查询。",
                },
                {
                    "role": "user",
                    "content": f"上下文：{hist or '无'}\n原问题：{question}",
                },
            ],
        )
        rewritten = (resp.choices[0].message.content or "").strip()
        return rewritten or base
    except Exception as exc:  # noqa: BLE001
        logger.warning("查询改写失败，使用规则改写: %s", exc)
        return base
