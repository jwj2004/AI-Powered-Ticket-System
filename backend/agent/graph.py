"""LangGraph 五节点：路由 → 检索 → 质量 → 生成 → 反馈。"""

from __future__ import annotations

import logging
from typing import Any, Iterator, Optional, TypedDict

from openai import OpenAI

from backend.agent import prompts, rules
from backend.clients.retrieve_client import RetrieveClient, extract_error_code
from backend.config import get_settings
from backend.retrieve.hybrid import hybrid_rerank_chunks
from backend.retrieve.rerank import rerank_chunks
from backend.retrieve.rewrite import rewrite_query
from backend import store

logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    message: str
    user_id: int
    username: str
    role: str
    history: list
    route_kind: str
    rewritten_query: str
    lookup: Optional[dict[str, Any]]
    chunks: list
    reply: str
    citations: list
    confidence: str
    gap_id: Optional[int]
    create_gap: bool
    persist_gap: bool
    awaiting_feedback: bool
    from_cache: bool


def _patch_langchain_debug() -> None:
    """当前环境 langchain.debug 缺失会导致 Graph.invoke 直接崩，补上后再走 LangGraph。"""
    try:
        import langchain

        if not hasattr(langchain, "debug"):
            langchain.debug = False
    except ImportError:
        return


def _client() -> RetrieveClient:
    return RetrieveClient(get_settings())


def route_node(state: AgentState) -> dict[str, Any]:
    """路由：结构化直查 / RAG / 闲聊拒答。"""
    question = state.get("message") or ""
    kind = rules.classify_route(question)
    return {"route_kind": kind}


def retrieve_node(state: AgentState) -> dict[str, Any]:
    """检索：先改写查询，再向量召回 + BM25 融合，最后 cross-encoder 重排。"""
    question = state.get("message") or ""
    role = state.get("role") or "ops"
    history = state.get("history") or []
    settings = get_settings()
    client = _client()

    rewritten = question
    if settings.enable_query_rewrite:
        rewritten = rewrite_query(question, history=history) or question

    lookup = None
    if state.get("route_kind") == "lookup":
        code = extract_error_code(question) or extract_error_code(rewritten)
        lookup = client.lookup(code) if code else None

    chunks: list[dict[str, Any]] = []
    if not lookup:
        raw = client.retrieve_chunks(
            rewritten,
            role=role,
            top_k=settings.retrieve_candidate_k,
        )
        if not raw and rewritten != question:
            raw = client.retrieve_chunks(
                question,
                role=role,
                top_k=settings.retrieve_candidate_k,
            )
        fused = (
            hybrid_rerank_chunks(rewritten, raw, top_k=max(settings.retrieve_top_k, 8))
            if settings.enable_hybrid_retrieve
            else raw
        )
        ranked = rerank_chunks(rewritten, fused, top_k=max(settings.retrieve_top_k, 8))
        strong = [
            c
            for c in ranked
            if float(c.get("score") or 0.0) >= settings.medium_score_threshold
        ]
        chunks = (strong or ranked)[: settings.retrieve_top_k]
    return {"lookup": lookup, "chunks": chunks, "rewritten_query": rewritten}


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


def _chunk_text(text: str, size: int = 2) -> Iterator[str]:
    text = text or ""
    if not text:
        return
    for i in range(0, len(text), size):
        yield text[i : i + size]


def iter_reply_tokens(state: AgentState) -> Iterator[str]:
    """真正流式：有 LLM Key 时按 token 推；否则把模板回答切成小段。"""
    existing = (state.get("reply") or "").strip()
    if existing and (state.get("from_cache") or (state.get("confidence") or "") == "low"):
        yield from _chunk_text(existing)
        return

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
    elif chunks:
        messages = prompts.build_rag_prompt(
            question=question, chunks=chunks, history=history
        )
        fallback = _template_from_chunks(chunks)
    else:
        yield from _chunk_text(state.get("reply") or "")
        return

    if not settings.llm_api_key:
        yield from _chunk_text(fallback)
        return

    try:
        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
        )
        stream = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.2,
            stream=True,
        )
        got = False
        for event in stream:
            delta = ""
            try:
                delta = event.choices[0].delta.content or ""
            except (AttributeError, IndexError):
                delta = ""
            if delta:
                got = True
                yield delta
        if not got:
            yield from _chunk_text(fallback)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM 流式调用失败，回退模板: %s", exc)
        yield from _chunk_text(fallback)


def generate_node(state: AgentState) -> dict[str, Any]:
    """生成：只根据 lookup / 文档块拼证据写回答。"""
    if (state.get("confidence") or "") == "low" and (state.get("reply") or "").strip():
        return {}
    reply = "".join(iter_reply_tokens(state)).strip()
    return {"reply": reply}


def quality_node(state: AgentState) -> dict[str, Any]:
    """质量：证据不足则不硬答，并按需写入 knowledge_gap。"""
    lookup = state.get("lookup")
    chunks = state.get("chunks") or []
    route = state.get("route_kind") or ""

    if route == "refuse":
        return {
            "confidence": "low",
            "reply": rules.REFUSE_MESSAGE,
            "citations": [],
            "gap_id": None,
            "create_gap": False,
        }

    if lookup:
        return {
            "confidence": "high",
            "citations": rules.citations_from_chunks(chunks),
            "create_gap": False,
        }

    level = rules.confidence_level(chunks)
    if level in {"high", "medium"}:
        return {
            "confidence": level,
            "citations": rules.citations_from_chunks(chunks),
            "create_gap": False,
        }

    gap_id = None
    if state.get("persist_gap"):
        store.init_db()
        gap_id = store.create_gap(
            question=state.get("message") or "",
            user_id=int(state.get("user_id") or 0),
            username=str(state.get("username") or ""),
        )
    return {
        "confidence": "low",
        "reply": rules.LOW_MESSAGE,
        "citations": [],
        "create_gap": gap_id is None,
        "gap_id": gap_id,
    }


def feedback_node(state: AgentState) -> dict[str, Any]:
    """反馈：问答链路收口，标记该回答可赞/踩；真正写入由 POST /api/feedback 完成。"""
    return {"awaiting_feedback": True}


def dispatch_from_route(state: AgentState) -> str:
    if (state.get("route_kind") or "rag") == "refuse":
        return "quality"
    return "retrieve"


def build_graph():
    """五个节点用条件边连接；LangGraph 不可用时用同等顺序的本地执行器。"""
    _patch_langchain_debug()
    try:
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(AgentState)
        graph.add_node("n_route", route_node)
        graph.add_node("n_retrieve", retrieve_node)
        graph.add_node("n_quality", quality_node)
        graph.add_node("n_generate", generate_node)
        graph.add_node("n_feedback", feedback_node)
        graph.add_edge(START, "n_route")
        graph.add_conditional_edges(
            "n_route",
            dispatch_from_route,
            {
                "retrieve": "n_retrieve",
                "quality": "n_quality",
            },
        )
        graph.add_edge("n_retrieve", "n_quality")
        graph.add_edge("n_quality", "n_generate")
        graph.add_edge("n_generate", "n_feedback")
        graph.add_edge("n_feedback", END)
        compiled = graph.compile()
        return _SafeGraph(compiled)
    except Exception as exc:  # noqa: BLE001
        logger.warning("LangGraph 不可用，使用本地五节点执行器: %s", exc)
        return _LocalGraph()


class _SafeGraph:
    def __init__(self, compiled) -> None:
        self.compiled = compiled
        self.uses_langgraph = True

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        _patch_langchain_debug()
        try:
            return self.compiled.invoke(state, config={"callbacks": []})
        except TypeError:
            return self.compiled.invoke(state)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LangGraph 执行失败，回退本地执行器: %s", exc)
            return _LocalGraph().invoke(state)


class _LocalGraph:
    """与五节点顺序一致的兜底执行器。"""

    uses_langgraph = False

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        state = {**state, **route_node(state)}  # type: ignore[arg-type]
        if dispatch_from_route(state) == "retrieve":  # type: ignore[arg-type]
            state = {**state, **retrieve_node(state)}  # type: ignore[arg-type]
        state = {**state, **quality_node(state)}  # type: ignore[arg-type]
        state = {**state, **generate_node(state)}  # type: ignore[arg-type]
        state = {**state, **feedback_node(state)}  # type: ignore[arg-type]
        return state


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def graph_node_names() -> list[str]:
    return ["n_route", "n_retrieve", "n_quality", "n_generate", "n_feedback"]


def prepare_state(state: dict[str, Any]) -> dict[str, Any]:
    """流式路径：跑到质量节点为止，生成由 token 迭代器负责。"""
    state = {**state, **route_node(state)}  # type: ignore[arg-type]
    if dispatch_from_route(state) == "retrieve":  # type: ignore[arg-type]
        state = {**state, **retrieve_node(state)}  # type: ignore[arg-type]
    state = {**state, **quality_node(state)}  # type: ignore[arg-type]
    return state
