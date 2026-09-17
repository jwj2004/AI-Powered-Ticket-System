"""生成流水线：retrieve → build_context → llm_generate。"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI

from backend.clients.retrieve_client import RetrieveClient
from backend.config import Settings, get_settings
from backend.draft import cite, prompts, rules

logger = logging.getLogger(__name__)


def generate_query_id() -> str:
    """形如 q_20260915_abc123。"""
    day = datetime.now().strftime("%Y%m%d")
    suffix = secrets.token_hex(3)
    return f"q_{day}_{suffix}"


def build_context(
    *,
    raw_text: str,
    customer_id: Optional[str],
    retrieve_result: dict[str, Any],
    client: RetrieveClient,
) -> dict[str, Any]:
    """拼装下游生成所需上下文。"""
    error_code = retrieve_result.get("error_code") or None
    tickets = list(retrieve_result.get("tickets") or [])[:3]
    customer_version = client.get_customer_version(customer_id)
    error_solution = client.get_error_code_solution(error_code)
    evidence = cite.tickets_to_evidence(tickets)
    return {
        "raw_text": raw_text,
        "customer_id": customer_id,
        "customer_version": customer_version,
        "error_code": error_code,
        "error_solution": error_solution,
        "tickets": tickets,
        "evidence": evidence,
    }


def llm_generate(context: dict[str, Any], settings: Settings) -> str:
    """
    有 API Key 时走 OpenAI 兼容接口；
    无 Key / 调用失败时回退到模板拼接（保证 D2 链路可跑通）。
    """
    error_code = context.get("error_code")
    error_solution = context.get("error_solution")
    tickets = context.get("tickets") or []

    if error_code and error_solution:
        messages = prompts.build_error_code_prompt(
            raw_text=context["raw_text"],
            error_code=error_code,
            error_solution=error_solution,
            tickets=tickets,
            customer_version=context.get("customer_version"),
        )
    else:
        messages = prompts.build_similar_ticket_prompt(
            raw_text=context["raw_text"],
            tickets=tickets,
            customer_version=context.get("customer_version"),
        )

    if not settings.llm_api_key:
        logger.info("LLM_API_KEY 未配置，使用模板拼接草稿")
        return cite.build_template_draft(
            raw_text=context["raw_text"],
            error_code=error_code,
            error_solution=error_solution,
            tickets=tickets,
            customer_version=context.get("customer_version"),
        )

    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
        )
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.2,
        )
        content = (resp.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("LLM 返回空内容")
        return content
    except Exception as exc:  # noqa: BLE001 — 兜底保证接口可用
        logger.warning("LLM 调用失败，回退模板拼接: %s", exc)
        return cite.build_template_draft(
            raw_text=context["raw_text"],
            error_code=error_code,
            error_solution=error_solution,
            tickets=tickets,
            customer_version=context.get("customer_version"),
        )


def generate_draft(
    raw_text: str,
    customer_id: Optional[str] = None,
    *,
    settings: Optional[Settings] = None,
    client: Optional[RetrieveClient] = None,
) -> dict[str, Any]:
    """
    主入口：retrieve → build_context → llm_generate。
    输出严格匹配 /api/draft 契约。
    """
    settings = settings or get_settings()
    client = client or RetrieveClient(settings)
    query_id = generate_query_id()

    retrieve_result = client.retrieve(query=raw_text, customer_id=customer_id, top_k=3)
    error_code = retrieve_result.get("error_code") or None
    tickets = list(retrieve_result.get("tickets") or [])

    if rules.should_refuse(error_code, tickets):
        return rules.low_confidence_response(query_id)

    context = build_context(
        raw_text=raw_text,
        customer_id=customer_id,
        retrieve_result=retrieve_result,
        client=client,
    )
    draft = llm_generate(context, settings)

    return {
        "query_id": query_id,
        "error_code": context["error_code"],
        "evidence": context["evidence"],
        "draft": draft,
        "confidence": "high",
    }
