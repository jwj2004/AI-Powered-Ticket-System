"""确认五节点已编进 LangGraph。"""

from backend.agent.graph import build_graph, graph_node_names, get_graph


def test_five_node_names():
    assert graph_node_names() == [
        "n_route",
        "n_retrieve",
        "n_quality",
        "n_generate",
        "n_feedback",
    ]


def test_langgraph_or_equivalent_runs_route_retrieve_generate_quality_feedback():
    graph = get_graph()
    result = graph.invoke(
        {
            "message": "订单导出超时怎么办？",
            "user_id": 2,
            "username": "ops",
            "role": "ops",
            "history": [],
            "persist_gap": False,
        }
    )
    assert result.get("confidence") == "high"
    assert result.get("awaiting_feedback") is True
    assert result.get("chunks")


def test_refuse_skips_to_quality_then_feedback():
    graph = build_graph()
    result = graph.invoke(
        {
            "message": "今天天气怎么样",
            "user_id": 2,
            "username": "ops",
            "role": "ops",
            "history": [],
            "persist_gap": False,
        }
    )
    assert result.get("route_kind") == "refuse"
    assert result.get("confidence") == "low"
    assert result.get("awaiting_feedback") is True
    assert not result.get("create_gap")
