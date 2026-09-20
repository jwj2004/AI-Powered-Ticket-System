"""BM25 关键词检索 + 向量分 RRF 融合。"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    tokens: list[str] = []
    buf: list[str] = []
    chars: list[str] = []

    def flush_buf() -> None:
        if buf:
            tokens.append("".join(buf))
            buf.clear()

    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            flush_buf()
            chars.append(ch)
            tokens.append(ch)
        elif ch.isalnum():
            chars.clear()
            buf.append(ch)
        else:
            flush_buf()
            chars.clear()
    flush_buf()
    for i in range(len(chars) - 1):
        tokens.append(chars[i] + chars[i + 1])
    return tokens or [text]


class BM25:
    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(doc) for doc in corpus]
        self.n = len(self.docs)
        self.avgdl = (sum(len(d) for d in self.docs) / self.n) if self.n else 0.0
        self.df: Counter[str] = Counter()
        for doc in self.docs:
            for term in set(doc):
                self.df[term] += 1

    def scores(self, query: str) -> list[float]:
        q_terms = tokenize(query)
        out: list[float] = []
        for doc in self.docs:
            tf = Counter(doc)
            dl = len(doc) or 1
            score = 0.0
            for term in q_terms:
                if term not in tf:
                    continue
                n_q = self.df.get(term, 0)
                idf = math.log(1 + (self.n - n_q + 0.5) / (n_q + 0.5))
                denom = tf[term] + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
                score += idf * (tf[term] * (self.k1 + 1)) / denom
            out.append(score)
        return out


def rrf_fuse(
    ranked_lists: list[list[int]],
    *,
    k: int = 60,
) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion，返回 (doc_index, score) 降序。"""
    fused: dict[int, float] = {}
    for ranking in ranked_lists:
        for rank, idx in enumerate(ranking, start=1):
            fused[idx] = fused.get(idx, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def hybrid_rerank_chunks(
    query: str,
    chunks: list[dict[str, Any]],
    *,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    if not chunks:
        return []
    corpus = [f"{c.get('title') or ''} {c.get('content') or ''}" for c in chunks]
    bm25 = BM25(corpus)
    bm25_scores = bm25.scores(query)
    bm25_order = sorted(range(len(chunks)), key=lambda i: bm25_scores[i], reverse=True)
    vec_order = sorted(
        range(len(chunks)),
        key=lambda i: float(chunks[i].get("score") or 0.0),
        reverse=True,
    )
    fused = rrf_fuse([bm25_order, vec_order])
    fused.sort(key=lambda pair: (pair[1], bm25_scores[pair[0]]), reverse=True)
    picked: list[dict[str, Any]] = []
    for idx, fused_score in fused[: max(1, top_k)]:
        item = dict(chunks[idx])
        item["bm25_score"] = round(bm25_scores[idx], 4)
        item["fused_score"] = round(fused_score, 4)
        picked.append(item)
    return picked
