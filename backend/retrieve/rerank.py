"""Cross-encoder 重排召回结果；无模型时用启发式回退。"""

from __future__ import annotations

import logging
from typing import Any, Optional

from backend.config import get_settings
from backend.retrieve.hybrid import tokenize

logger = logging.getLogger(__name__)

_MODEL = None
_LOAD_TRIED = False


def _load_cross_encoder():
    global _MODEL, _LOAD_TRIED
    if _LOAD_TRIED:
        return _MODEL
    _LOAD_TRIED = True
    settings = get_settings()
    if not settings.enable_cross_encoder:
        return None
    try:
        from sentence_transformers import CrossEncoder

        _MODEL = CrossEncoder(settings.cross_encoder_model)
    except Exception as exc:  # noqa: BLE001
        logger.warning("CrossEncoder 加载失败，使用启发式重排: %s", exc)
        _MODEL = None
    return _MODEL


def _heuristic_score(query: str, chunk: dict[str, Any]) -> float:
    q_tokens = set(tokenize(query))
    text = f"{chunk.get('title') or ''} {chunk.get('content') or ''}"
    d_tokens = set(tokenize(text))
    overlap = len(q_tokens & d_tokens) / max(1, len(q_tokens))
    vec = float(chunk.get("score") or 0.0)
    return 0.6 * overlap + 0.4 * vec


def rerank_chunks(
    query: str,
    chunks: list[dict[str, Any]],
    *,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    if not chunks:
        return []
    model = _load_cross_encoder()
    scored: list[tuple[float, dict[str, Any]]]
    if model is not None:
        pairs = [
            (query, f"{c.get('title') or ''}\n{c.get('content') or ''}") for c in chunks
        ]
        try:
            scores = model.predict(pairs)
            scored = [(float(s), c) for s, c in zip(scores, chunks)]
        except Exception as exc:  # noqa: BLE001
            logger.warning("CrossEncoder 预测失败，回退启发式: %s", exc)
            scored = [(_heuristic_score(query, c), c) for c in chunks]
    else:
        scored = [(_heuristic_score(query, c), c) for c in chunks]
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for score, chunk in scored[: max(1, top_k)]:
        item = dict(chunk)
        item["rerank_score"] = round(float(score), 4)
        out.append(item)
    return out
