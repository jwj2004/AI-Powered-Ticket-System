"""
向量检索服务 - 封装 FAISS + BGE
- 工单索引：D1 构建，存 ticket.raw_text
- 文档块索引：文档上传时自动构建，存 document_chunk.content
"""
import os
import json
import re
from typing import List, Tuple, Optional

import faiss
import numpy as np

from app.core.config import settings
from app.core.logger import log
from app.core.database import SessionLocal
from app.models import Ticket, ErrorCode, VectorIndexMeta
from app.models.document_chunk import DocumentChunk
from app.models.document import Document


class VectorRetriever:
    """向量检索器（单例模式）"""

    _instance = None
    _ticket_index = None
    _ticket_id_mapping = {}
    _doc_index = None
    _doc_id_mapping = {}
    _model = None
    _dim = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def init(cls):
        """加载 FAISS 索引和 BGE 模型"""
        if cls._initialized:
            return

        # 从本地路径加载模型，避免网络下载问题
        local_model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "bge-small-zh-v1.5")
        if os.path.exists(local_model_path):
            log.info(f"从本地加载向量模型: {local_model_path}")
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(local_model_path)
        else:
            log.info(f"本地模型不存在，尝试在线加载: {settings.embedding_model}")
            os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(settings.embedding_model)
        cls._dim = cls._model.get_sentence_embedding_dimension()

        # 加载工单索引
        if os.path.exists(settings.faiss_index_path):
            log.info(f"加载工单 FAISS 索引: {settings.faiss_index_path}")
            cls._ticket_index = faiss.read_index(settings.faiss_index_path)
            with open(settings.faiss_mapping_path, "r", encoding="utf-8") as f:
                cls._ticket_id_mapping = {int(k): v for k, v in json.load(f).items()}
            log.success(f"工单索引加载完成，共 {cls._ticket_index.ntotal} 条")
        else:
            log.warning(f"工单 FAISS 索引不存在: {settings.faiss_index_path}")
            cls._ticket_index = faiss.IndexFlatIP(cls._dim)

        # 加载文档块索引
        if os.path.exists(settings.doc_faiss_index_path):
            log.info(f"加载文档块 FAISS 索引: {settings.doc_faiss_index_path}")
            cls._doc_index = faiss.read_index(settings.doc_faiss_index_path)
            with open(settings.doc_faiss_mapping_path, "r", encoding="utf-8") as f:
                cls._doc_id_mapping = {int(k): v for k, v in json.load(f).items()}
            log.success(f"文档块索引加载完成，共 {cls._doc_index.ntotal} 条")
        else:
            log.info("文档块索引不存在，初始化空索引")
            cls._doc_index = faiss.IndexFlatIP(cls._dim)
            cls._doc_id_mapping = {}

        cls._initialized = True

    @classmethod
    def ensure_init(cls):
        if not cls._initialized:
            cls.init()

    # ============================================================
    # 工单检索
    # ============================================================

    @classmethod
    def search_tickets(cls, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """检索相似工单，返回 [(ticket_id, score), ...]"""
        cls.ensure_init()
        if cls._ticket_index is None or cls._ticket_index.ntotal == 0:
            return []

        q_vec = cls._model.encode([query])
        q_vec = np.array(q_vec, dtype="float32")
        faiss.normalize_L2(q_vec)

        scores, indices = cls._ticket_index.search(q_vec, top_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(cls._ticket_id_mapping):
                continue
            ticket_id = cls._ticket_id_mapping[int(idx)]
            results.append((ticket_id, float(score)))
        return results

    # ============================================================
    # 文档块检索
    # ============================================================

    @classmethod
    def search_documents(cls, query: str, top_k: int = 3) -> List[Tuple[int, int, float]]:
        """检索相似文档块，返回 [(document_id, chunk_index, score), ...]"""
        cls.ensure_init()
        if cls._doc_index is None or cls._doc_index.ntotal == 0:
            return []

        q_vec = cls._model.encode([query])
        q_vec = np.array(q_vec, dtype="float32")
        faiss.normalize_L2(q_vec)

        scores, indices = cls._doc_index.search(q_vec, top_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(cls._doc_id_mapping):
                continue
            chunk_id = cls._doc_id_mapping[int(idx)]
            db = SessionLocal()
            try:
                chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
                if chunk:
                    results.append((chunk.document_id, chunk.chunk_index, float(score)))
            finally:
                db.close()
        return results

    # ============================================================
    # 混合召回（错误码精确 + 文档块向量 + 工单向量）
    # ============================================================

    @classmethod
    def hybrid_search(cls, query: str, top_k: int = 3, conversation_history: str = None) -> dict:
        """
        混合检索：
        1. 先检测错误码，精确命中直接返回结构化 solution
        2. 文档块向量召回 top_k
        3. 工单向量召回 top_k（补充）
        返回 {error_code, solution, doc_chunks, tickets, confidence}
        """
        cls.ensure_init()

        result = {
            "error_code": None,
            "solution": None,
            "doc_chunks": [],
            "tickets": [],
            "confidence": "low",
        }

        search_query = query
        if conversation_history:
            search_query = f"{conversation_history}\n{query}"

        # 1. 错误码精确查询（增强：匹配 code + name + trigger_condition）
        ec_result = detect_error_code_enhanced(query)
        if ec_result:
            result["error_code"] = ec_result["code"]
            result["solution"] = ec_result["solution"]
            result["confidence"] = "high"
            log.info(f"错误码精确命中: {ec_result['code']} (匹配方式: {ec_result['match_type']})")

        # 2. 文档块向量召回
        doc_results = cls.search_documents(search_query, top_k)
        if doc_results:
            db = SessionLocal()
            try:
                for doc_id, chunk_idx, score in doc_results:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    chunk = db.query(DocumentChunk).filter(
                        DocumentChunk.document_id == doc_id,
                        DocumentChunk.chunk_index == chunk_idx,
                    ).first()
                    if doc and chunk:
                        result["doc_chunks"].append({
                            "document_id": doc_id,
                            "title": doc.title,
                            "chunk_index": chunk_idx,
                            "content": chunk.content,
                            "score": score,
                        })
            finally:
                db.close()

        # 3. 工单向量召回（补充）
        ticket_results = cls.search_tickets(search_query, top_k)
        if ticket_results:
            db = SessionLocal()
            try:
                for ticket_id, score in ticket_results:
                    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
                    if ticket:
                        result["tickets"].append({
                            "ticket_id": ticket_id,
                            "raw_text": ticket.raw_text,
                            "error_code": ticket.error_code,
                            "score": score,
                        })
            finally:
                db.close()

        # 置信度判断
        if result["confidence"] != "high":
            if doc_results and doc_results[0][2] > 0.75:
                result["confidence"] = "medium"
            elif doc_results and doc_results[0][2] > 0.6:
                result["confidence"] = "low"
            elif doc_results or ticket_results:
                result["confidence"] = "low"
            else:
                result["confidence"] = "none"

        return result

    # ============================================================
    # 文档块向量化入索引
    # ============================================================

    @classmethod
    def add_document_chunks(cls, chunks: list, chunk_ids: list):
        """将文档块向量化并加入 FAISS 索引"""
        cls.ensure_init()
        if not chunks:
            return

        embeddings = cls._model.encode(chunks, show_progress_bar=False, batch_size=32)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)

        start_pos = cls._doc_index.ntotal
        cls._doc_index.add(embeddings)

        for i, chunk_id in enumerate(chunk_ids):
            cls._doc_id_mapping[start_pos + i] = chunk_id

        cls._save_doc_index()
        log.info(f"文档块向量化完成，新增 {len(chunks)} 条，总计 {cls._doc_index.ntotal} 条")

    @classmethod
    def remove_document_chunks(cls, chunk_ids: list):
        """从索引中移除文档块（重建方式）"""
        cls.ensure_init()
        if not chunk_ids:
            return

        remove_set = set(chunk_ids)
        new_mapping = {}
        old_vectors = []
        old_chunk_ids = []

        for pos, chunk_id in sorted(cls._doc_id_mapping.items()):
            if chunk_id not in remove_set:
                old_vectors.append(pos)
                old_chunk_ids.append(chunk_id)

        if not old_vectors:
            cls._doc_index = faiss.IndexFlatIP(cls._dim)
            cls._doc_id_mapping = {}
        else:
            all_vectors = faiss.rev_swig_ptr(cls._doc_index.get_xb(), cls._doc_index.ntotal * cls._dim)
            all_vectors = all_vectors.reshape(-1, cls._dim)
            kept_vectors = np.array([all_vectors[pos] for pos in old_vectors], dtype="float32")

            cls._doc_index = faiss.IndexFlatIP(cls._dim)
            cls._doc_index.add(kept_vectors)
            cls._doc_id_mapping = {i: cid for i, cid in enumerate(old_chunk_ids)}

        cls._save_doc_index()
        log.info(f"文档块移除完成，剩余 {cls._doc_index.ntotal} 条")

    @classmethod
    def _save_doc_index(cls):
        """保存文档块索引和映射"""
        os.makedirs(os.path.dirname(settings.doc_faiss_index_path), exist_ok=True)
        faiss.write_index(cls._doc_index, settings.doc_faiss_index_path)
        with open(settings.doc_faiss_mapping_path, "w", encoding="utf-8") as f:
            json.dump(cls._doc_id_mapping, f, ensure_ascii=False, indent=2)


# ============================================================
# 错误码识别（增强版：匹配 code + name + trigger_condition）
# ============================================================

_error_code_cache = []


def _load_error_codes():
    global _error_code_cache
    if _error_code_cache:
        return
    db = SessionLocal()
    try:
        codes = db.query(ErrorCode).all()
        _error_code_cache = [
            {
                "code": ec.code,
                "name": ec.name,
                "trigger_condition": ec.trigger_condition or "",
                "solution": ec.solution or "",
                "code_pattern": re.compile(re.escape(ec.code), re.IGNORECASE),
                "name_keywords": [w for w in ec.name.split() if len(w) > 1] if ec.name else [],
            }
            for ec in codes
        ]
        log.info(f"加载 {len(_error_code_cache)} 个错误码用于增强匹配")
    finally:
        db.close()


def detect_error_code(text: str) -> Optional[str]:
    """旧接口保留兼容"""
    _load_error_codes()
    for ec in _error_code_cache:
        if ec["code_pattern"].search(text):
            return ec["code"]
    return None


def detect_error_code_enhanced(text: str) -> Optional[dict]:
    """
    错误码识别：仅精确匹配字面量（PAY_、ERR_、ORDER_ 等大写带下划线的 code）
    自然语言描述不命中错误码表，走文档 RAG
    返回 {code, solution, match_type} 或 None
    """
    _load_error_codes()

    for ec in _error_code_cache:
        if ec["code_pattern"].search(text):
            log.debug(f"精确匹配到错误码: {ec['code']}")
            return {"code": ec["code"], "solution": ec["solution"], "match_type": "code"}

    return None


# ============================================================
# 客户上下文查询
# ============================================================

def get_customer_context(customer_id: str) -> Optional[dict]:
    from app.models import CustomerAsset
    db = SessionLocal()
    try:
        customer = db.query(CustomerAsset).filter(
            CustomerAsset.customer_id == customer_id
        ).first()
        if not customer:
            return None
        return {
            "customer_id": customer.customer_id,
            "shop_name": customer.shop_name,
            "plan": customer.plan,
            "version": customer.version,
            "enabled_modules": customer.enabled_modules,
            "key_configs": customer.key_configs,
            "recent_changes": customer.recent_changes,
        }
    finally:
        db.close()
