"""
向量检索服务 - 封装 FAISS + BGE
D2 的 /api/retrieve 和 /api/lookup 都会用到这里
"""
import os
import json
import re
from datetime import datetime
from typing import List, Tuple, Optional

import faiss
import numpy as np

from app.core.config import settings
from app.core.logger import log
from app.core.database import SessionLocal
from app.models import Ticket, ErrorCode, VectorIndexMeta


class VectorRetriever:
    """向量检索器（单例模式）"""

    _instance = None
    _index = None
    _id_mapping = {}  # {索引位置: ticket_id}
    _model = None
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

        log.info(f"加载向量模型: {settings.embedding_model}")
        from sentence_transformers import SentenceTransformer
        cls._model = SentenceTransformer(settings.embedding_model)

        if os.path.exists(settings.faiss_index_path):
            log.info(f"加载 FAISS 索引: {settings.faiss_index_path}")
            cls._index = faiss.read_index(settings.faiss_index_path)

            with open(settings.faiss_mapping_path, "r", encoding="utf-8") as f:
                cls._id_mapping = json.load(f)
            # key 统一转 int
            cls._id_mapping = {int(k): v for k, v in cls._id_mapping.items()}

            log.success(f"FAISS 索引加载完成，共 {cls._index.ntotal} 条")
        else:
            log.warning(f"FAISS 索引不存在: {settings.faiss_index_path}")
            log.warning("请先运行 scripts/build_faiss_index.py 构建索引")

        cls._initialized = True

    @classmethod
    def ensure_init(cls):
        """确保已初始化，未初始化则加载"""
        if not cls._initialized:
            cls.init()

    @classmethod
    def search(cls, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        检索相似工单
        返回: [(ticket_id, score), ...]
        """
        cls.ensure_init()
        if cls._index is None:
            log.error("FAISS 索引未加载，无法检索")
            return []

        # 向量化
        q_vec = cls._model.encode([query])
        q_vec = np.array(q_vec, dtype="float32")
        faiss.normalize_L2(q_vec)

        # 检索
        scores, indices = cls._index.search(q_vec, top_k)

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(cls._id_mapping):
                continue
            ticket_id = cls._id_mapping[int(idx)]
            results.append((ticket_id, float(score)))

        return results


# ============================================================
# 错误码识别：从用户文本中匹配错误码
# ============================================================

# 预编译所有错误码的正则（从数据库加载）
_error_code_patterns = []


def _load_error_codes():
    """加载所有错误码到内存，用于快速匹配"""
    global _error_code_patterns
    if _error_code_patterns:
        return
    db = SessionLocal()
    try:
        codes = db.query(ErrorCode.code).all()
        _error_code_patterns = [
            (row.code, re.compile(re.escape(row.code), re.IGNORECASE))
            for row in codes
        ]
        log.info(f"加载 {len(_error_code_patterns)} 个错误码用于文本匹配")
    finally:
        db.close()


def detect_error_code(text: str) -> Optional[str]:
    """
    从用户文本中识别错误码
    策略：精确字符串匹配（错误码是有格式的，如 PAY_CALLBACK_TIMEOUT）
    """
    _load_error_codes()
    for code, pattern in _error_code_patterns:
        if pattern.search(text):
            log.debug(f"文本匹配到错误码: {code}")
            return code
    return None


# ============================================================
# 客户上下文查询
# ============================================================

def get_customer_context(customer_id: str) -> Optional[dict]:
    """获取客户上下文信息（版本、模块、配置等）"""
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
