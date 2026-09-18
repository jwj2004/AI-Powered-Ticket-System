"""两套 prompt：①错误码命中版 ②纯相似工单版。"""

from __future__ import annotations

from typing import Any, Optional

SYSTEM_PROMPT = (
    "你是 SaaS 售后一线客服的智能副驾，只根据给定证据写对外答复草稿。"
    "严禁编造证据中没有的事实；每个关键结论都必须能在证据中找到来源。"
    "语气礼貌、简洁、可直接复制发给客户。"
)


def _format_tickets(tickets: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for i, t in enumerate(tickets[:3], start=1):
        lines.append(
            f"{i}. ticket_id={t.get('ticket_id')}\n"
            f"   summary={t.get('summary')}\n"
            f"   solution_text={t.get('solution_text')}\n"
            f"   score={t.get('score')}"
        )
    return "\n".join(lines) if lines else "（无）"


def build_error_code_prompt(
    *,
    raw_text: str,
    error_code: str,
    error_solution: str,
    tickets: list[dict[str, Any]],
    customer_version: Optional[str],
) -> list[dict[str, str]]:
    """① 错误码命中：以结构化 solution 为主，不靠 LLM 自由发挥。"""
    version = customer_version or "未知（未提供客户资产）"
    user = f"""请根据以下材料生成一段可直接发给客户的答复草稿。

【客户原话】
{raw_text}

【客户版本】
{version}（来源：客户资产档案；版本未知时不要编造具体版本号）

【命中错误码】
code={error_code}

【错误码标准解法（必须以此为主，可轻度润色，不得改写核心步骤）】
{error_solution}

【补充相似工单证据（仅作佐证，不可引入解法未覆盖的新事实）】
{_format_tickets(tickets)}

【输出要求】
1. 结构：客套开头（提及客户版本，并说明来源）→ 问题核实结论（点名错误码）→ 解决步骤 → 收尾。
2. 解决步骤必须以「错误码标准解法」为主，不要另起一套方案。
3. 草稿中提到的历史依据，请用 ticket_id 点到为止。
4. 只输出草稿正文，不要 Markdown 标题，不要解释你的推理过程。
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build_similar_ticket_prompt(
    *,
    raw_text: str,
    tickets: list[dict[str, Any]],
    customer_version: Optional[str],
) -> list[dict[str, str]]:
    """② 纯相似工单：只能基于 evidence 拼接，不得编造。"""
    version = customer_version or "未知（未提供客户资产）"
    user = f"""请根据以下相似工单证据生成一段可直接发给客户的答复草稿。

【客户原话】
{raw_text}

【客户版本】
{version}（来源：客户资产档案；版本未知时不要编造具体版本号）

【相似工单证据（唯一事实来源）】
{_format_tickets(tickets)}

【输出要求】
1. 结构：客套开头（提及客户版本并说明来源）→ 问题核实结论 → 解决步骤（来自 evidence）→ 收尾。
2. 草稿里每个事实都必须能在上述 evidence 中找到；找不到就不要写。
3. 引用时带上 ticket_id；不要把整段 solution_text 原样粘贴成长文。
4. 只输出草稿正文，不要 Markdown 标题，不要解释你的推理过程。
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
