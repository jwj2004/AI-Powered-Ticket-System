"""LangGraph 五节点：路由 → 检索/直查 → 生成 → 质量（缺口）→ 结束；赞踩走独立接口。"""

from __future__ import annotations

import logging
from typing import Any, Optional, TypedDict

from openai import OpenAI

from backend.agent import prompts, rules
from backend.clients.retrieve_client import RetrieveClient, extract_error_code
from backend.config import Settings, get_settings

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    message: str
    user_id: int
    username: str
    role: str
    history: list
    route_kind: str
    lookup: Optional[dict[str, Any]]
    chunks: list
    reply: str
    citations: list
    confidence: str
    gap_id: Optional[int]
    create_gap: bool


def _client() -> RetrieveClient:
    return RetrieveClient(get_settings())


def route_node(state: AgentState) -> AgentState:
    question = state.get("message") or ""
    code = extract_error_code(question)
    if code:
        state["route_kind"] = "lookup"
        return state
    state["route_kind"] = rules.classify_route(question)
    return state


def lookup_node(state: AgentState) -> AgentState:
    question = state.get("message") or ""
    code = extract_error_code(question)
    found = _client().lookup(code) if code else None
    state["lookup"] = found
    if not found:
        state["route_kind"] = "rag"
    return state


def retrieve_node(state: AgentState) -> AgentState:
    question = state.get("message") or ""
    role = state.get("role") or "ops"
    chunks = _client().retrieve_chunks(question, role=role, top_k=5)
    state["chunks"] = chunks
    return state


def _llm_generate(messages: list[dict[str, str]], settings: Settings, fallback: str) -> str:
    if not settings.llm_api_key:
        return fallback
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
        return content or fallback
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM 调用失败，回退模板: %s", exc)
        return fallback


def _template_from_lookup(lookup: dict[str, Any]) -> str:
    code = lookup.get("code") or ""
    name = lookup.get("name") or ""
    solution = lookup.get("solution") or ""
    return f"{name}（{code}）：{solution}".strip()


def _template_from_chunks(chunks: list[dict[str, Any]]) -> str:
    parts = []
    for c in chunks[:3]:
        title = c.get("title") or "内部文档"
        content = (c.get("content") or "").strip()
        if content:
            parts.append(f"根据《{title}》：{content}")
    return "\n".join(parts)


def generate_node(state: AgentState) -> AgentState:
    settings = get_settings()
    question = state.get("message") or ""
    history = state.get("history") or []
    lookup = state.get("lookup")
    chunks = state.get("chunks") or []

    if lookup:
        messages = prompts.build_lookup_prompt(
            question=question, lookup=lookup, history=history
        )
        fallback = _template_from_lookup(lookup)
        state["reply"] = _llm_generate(messages, settings, fallback)
        return state

    if chunks:
        messages = prompts.build_rag_prompt(
            question=question, chunks=chunks, history=history
        )
        fallback = _template_from_chunks(chunks)
        state["reply"] = _llm_generate(messages, settings, fallback)
        return state

    state["reply"] = ""
    return state


def quality_node(state: AgentState) -> AgentState:
    """证据充分才输出生成结果；否则固定拒答文案，并标记需要记缺口。"""
    lookup = state.get("lookup")
    chunks = state.get("chunks") or []
    route = state.get("route_kind") or ""

    if route == "refuse":
        state["confidence"] = "low"
        state["reply"] = rules.REFUSE_MESSAGE
        state["citations"] = []
        state["gap_id"] = None
        state["create_gap"] = False
        return state

    if lookup:
        state["confidence"] = "high"
        state["citations"] = rules.citations_from_chunks(chunks)
        state["create_gap"] = False
        return state

    if rules.chunks_are_strong(chunks):
        state["confidence"] = "high"
        state["citations"] = rules.citations_from_chunks(chunks)
        state["create_gap"] = False
        return state

    state["confidence"] = "low"
    state["reply"] = rules.LOW_MESSAGE
    state["citations"] = []
    state["create_gap"] = True
    state["gap_id"] = None
    return state


def dispatch_from_route(state: AgentState) -> str:
    route = state.get("route_kind") or "rag"
    if route == "lookup":
        return "lookup"
    if route == "refuse":
        return "quality"
    return "retrieve"


def dispatch_after_lookup(state: AgentState) -> str:
    if state.get("lookup"):
        return "generate"
    return "retrieve"


def build_graph():
    """编译 LangGraph；若环境缺少 langgraph，则退回同等节点顺序的本地执行器。"""
    try:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(AgentState)
        graph.add_node("n_route", route_node)
        graph.add_node("n_lookup", lookup_node)
        graph.add_node("n_retrieve", retrieve_node)
        graph.add_node("n_generate", generate_node)
        graph.add_node("n_quality", quality_node)
        graph.set_entry_point("n_route")
        graph.add_conditional_edges(
            "n_route",
            dispatch_from_route,
            {
                "lookup": "n_lookup",
                "retrieve": "n_retrieve",
                "quality": "n_quality",
            },
        )
        graph.add_conditional_edges(
            "n_lookup",
            dispatch_after_lookup,
            {
                "generate": "n_generate",
                "retrieve": "n_retrieve",
            },
        )
        graph.add_edge("n_retrieve", "n_generate")
        graph.add_edge("n_generate", "n_quality")
        graph.add_edge("n_quality", END)
        compiled = graph.compile()
        return _SafeGraph(compiled)
    except Exception as exc:  # noqa: BLE001 — 环境依赖冲突时仍要能问答
        logger.warning("LangGraph 不可用，使用本地五节点执行器: %s", exc)
        return _LocalGraph()


class _SafeGraph:
    """优先走 LangGraph；运行期依赖冲突则回退本地节点。"""

    def __init__(self, compiled) -> None:
        self.compiled = compiled

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.compiled.invoke(state)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LangGraph 执行失败，回退本地执行器: %s", exc)
            return _LocalGraph().invoke(state)


class _LocalGraph:
    """与 LangGraph 节点顺序一致，避免缺依赖时问答不可用。"""

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        state = route_node(state)  # type: ignore[arg-type]
        nxt = dispatch_from_route(state)  # type: ignore[arg-type]
        if nxt == "lookup":
            state = lookup_node(state)  # type: ignore[arg-type]
            nxt2 = dispatch_after_lookup(state)  # type: ignore[arg-type]
            if nxt2 == "retrieve":
                state = retrieve_node(state)  # type: ignore[arg-type]
                state = generate_node(state)  # type: ignore[arg-type]
            else:
                state = generate_node(state)  # type: ignore[arg-type]
        elif nxt == "retrieve":
            state = retrieve_node(state)  # type: ignore[arg-type]
            state = generate_node(state)  # type: ignore[arg-type]
        state = quality_node(state)  # type: ignore[arg-type]
        return state


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH
