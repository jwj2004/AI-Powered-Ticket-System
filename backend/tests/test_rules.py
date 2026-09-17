"""路由与硬规则单元测试。"""

from backend.agent import rules


def test_classify_lookup_when_error_code_present():
    assert rules.classify_route("PAY_CALLBACK_TIMEOUT 怎么处理") == "lookup"


def test_classify_refuse_chitchat():
    assert rules.classify_route("今天天气怎么样，帮我写一首诗") == "refuse"


def test_classify_rag_for_export_timeout():
    assert rules.classify_route("订单导出超时怎么办？") == "rag"


def test_chunks_are_strong():
    assert rules.chunks_are_strong([{"score": 0.9}], high_score_threshold=0.75) is True
    assert rules.chunks_are_strong([{"score": 0.2}], high_score_threshold=0.75) is False
    assert rules.chunks_are_strong([]) is False


def test_citations_from_chunks():
    citations = rules.citations_from_chunks(
        [
            {
                "document_id": 1,
                "title": "订单导出超时排查",
                "chunk_index": 3,
                "score": 0.9,
            }
        ]
    )
    assert citations == [
        {"document_id": 1, "title": "订单导出超时排查", "chunk_index": 3}
    ]
