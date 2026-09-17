"""evidence → 草稿的引用拼接辅助。"""

from __future__ import annotations

from typing import Any, Optional


def tickets_to_evidence(tickets: list[dict[str, Any]], limit: int = 3) -> list[dict[str, str]]:
    """
    对外 evidence：只给 ticket_id + 一句话 summary，
    不要把整段 solution_text 塞进去。
    """
    evidence: list[dict[str, str]] = []
    for item in tickets[:limit]:
        ticket_id = item.get("ticket_id") or ""
        summary = (item.get("summary") or "").strip()
        if not summary:
            raw = (item.get("solution_text") or "").strip()
            summary = " ".join(raw.split())
            if len(summary) > 80:
                summary = summary[:79] + "…"
        if not ticket_id:
            continue
        evidence.append({"ticket_id": ticket_id, "summary": summary})
    return evidence


def build_template_draft(
    *,
    raw_text: str,
    error_code: Optional[str],
    error_solution: Optional[str],
    tickets: list[dict[str, Any]],
    customer_version: Optional[str],
) -> str:
    """
    无 LLM Key 时的兜底拼接：
    客套开头（带版本号）→ 核实结论 → 解决步骤（优先错误码 solution）→ 收尾。
    """
    _ = raw_text
    version_clause = (
        f"您当前店铺版本为 {customer_version}（来自客户资产档案）。"
        if customer_version
        else "已结合您店铺当前配置进行核实。"
    )

    if error_code and error_solution:
        conclusion = (
            f"已核实该问题对应错误码 {error_code}（支付回调超时类问题）。"
        )
        steps = error_solution
        sources = "、".join(
            t.get("ticket_id") for t in tickets[:3] if t.get("ticket_id")
        )
        cite = f"参考历史工单：{sources}。" if sources else "依据来自错误码标准解法。"
    else:
        conclusion = "已对照历史同类工单完成核实。"
        # 用摘要级步骤，避免整段 solution 堆砌
        step_lines = []
        for t in tickets[:3]:
            summary = t.get("summary") or ""
            tid = t.get("ticket_id") or ""
            if summary:
                step_lines.append(f"- 参考 {tid}：{summary}")
        steps = "\n".join(step_lines) if step_lines else "请按历史同类工单步骤处理。"
        cite = "以上步骤均来自 evidence 中的历史工单摘要。"

    return (
        f"您好，已为您核实该笔问题。{version_clause}\n"
        f"{conclusion}\n"
        f"建议处理步骤：{steps}\n"
        f"{cite}\n"
        "如按上述步骤仍未恢复，请提供订单号与支付流水号，我们将为您转二线继续排查。"
    )
