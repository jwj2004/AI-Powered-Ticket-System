"""Prompt：结构化直查 / 文档 RAG / 多轮追问。"""

from __future__ import annotations

from typing import Any, Optional

SYSTEM_PROMPT = (
    "你是企业内部知识库问答助手，只根据给定证据回答员工问题。"
    "严禁编造证据中没有的事实；每个关键结论都必须能在证据中找到来源。"
    "语气简洁、可直接给客服/运维/新人阅读。只输出答案正文，不要解释推理过程。"
)


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "（无）"
    lines = []
    for item in history[-10:]:
        role = "用户" if item.get("role") == "user" else "助手"
        lines.append(f"{role}: {item.get('content')}")
    return "\n".join(lines)


def _format_chunks(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "（无）"
    lines = []
    for i, c in enumerate(chunks[:5], start=1):
        lines.append(
            f"{i}. document_id={c.get('document_id')} title={c.get('title')} "
            f"chunk_index={c.get('chunk_index')} score={c.get('score')}\n"
            f"   content={c.get('content')}"
        )
    return "\n".join(lines)


def build_lookup_prompt(
    *,
    question: str,
    lookup: dict[str, Any],
    history: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    user = f"""请根据结构化错误码条目回答。

【当前问题】
{question}

【最近对话】
{_format_history(history or [])}

【错误码条目（唯一事实来源）】
code={lookup.get("code")}
name={lookup.get("name")}
solution={lookup.get("solution")}

【输出要求】
1. 用错误码标准解法为主，可轻度润色，不得改写核心步骤。
2. 点名错误码。
3. 只输出答案正文。
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_rag_prompt(
    *,
    question: str,
    chunks: list[dict[str, Any]],
    history: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    user = f"""请根据内部文档片段回答。

【当前问题】
{question}

【最近对话】
{_format_history(history or [])}

【文档证据（唯一事实来源）】
{_format_chunks(chunks)}

【输出要求】
1. 只使用上述文档中的事实；找不到就不要写。
2. 回答中可用文档标题点到为止，不要编造文档没有的步骤。
3. 只输出答案正文。
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
