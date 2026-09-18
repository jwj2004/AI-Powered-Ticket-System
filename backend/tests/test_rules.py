"""硬规则单元测试。"""

from backend.draft import rules


def test_judge_confidence_error_code_is_high():
    assert rules.judge_confidence("PAY_CALLBACK_TIMEOUT", []) == "high"


def test_judge_confidence_high_score_ticket():
    tickets = [{"ticket_id": "T1", "score": 0.9}]
    assert rules.judge_confidence(None, tickets) == "high"


def test_judge_confidence_low_score_is_low():
    tickets = [{"ticket_id": "T1", "score": 0.2}]
    assert rules.judge_confidence(None, tickets) == "low"


def test_should_refuse_when_empty():
    assert rules.should_refuse(None, []) is True


def test_low_confidence_response_contract():
    resp = rules.low_confidence_response("q_20260915_abc123")
    assert resp["query_id"] == "q_20260915_abc123"
    assert resp["error_code"] is None
    assert resp["evidence"] == []
    assert resp["draft"] is None
    assert resp["confidence"] == "low"
    assert resp["message"] == "未找到可靠依据，建议转二线处理"
