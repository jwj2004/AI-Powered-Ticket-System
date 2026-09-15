"""cite 辅助函数测试。"""

from backend.draft.cite import build_template_draft, tickets_to_evidence


def test_tickets_to_evidence_uses_summary_not_full_solution():
    tickets = [
        {
            "ticket_id": "T1",
            "solution_text": "这是一段很长的解决方案内容，不应该整段进入 evidence。" * 3,
            "summary": "同现象：付款后订单待支付",
            "score": 0.9,
        }
    ]
    evidence = tickets_to_evidence(tickets)
    assert evidence == [
        {"ticket_id": "T1", "summary": "同现象：付款后订单待支付"}
    ]


def test_template_draft_mentions_version_and_error_code():
    draft = build_template_draft(
        raw_text="付了钱订单没更新",
        error_code="PAY_CALLBACK_TIMEOUT",
        error_solution="先在商户后台查单再补单。",
        tickets=[{"ticket_id": "T20260715001", "summary": "回调超时补单"}],
        customer_version="v3.8.5",
    )
    assert "v3.8.5" in draft
    assert "PAY_CALLBACK_TIMEOUT" in draft
    assert "T20260715001" in draft
