"""
D1 - FAISS 向量索引构建脚本
功能：用 BGE 模型把工单 raw_text 向量化，构建 FAISS 索引
用法：python scripts/build_faiss_index.py

注意：第一次运行会下载 BGE 模型（约 100MB），需要联网
"""
import os
import sys
import json
from datetime import datetime

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logger import log
from app.core.database import SessionLocal
from app.models import Ticket, VectorIndexMeta


def load_tickets(db):
    """从数据库加载所有工单"""
    tickets = db.query(Ticket).order_by(Ticket.ticket_id).all()
    log.info(f"📋 加载到 {len(tickets)} 条工单")
    return tickets


def build_index(tickets):
    """构建 FAISS 索引"""
    log.info(f"🤖 加载向量模型: {settings.embedding_model}")
    log.info("   （第一次会下载模型，约 100MB，请耐心等待...）")
    model = SentenceTransformer(settings.embedding_model)

    ticket_ids = [t.ticket_id for t in tickets]
    texts = [t.raw_text for t in tickets]

    log.info(f"🔢 开始向量化 {len(texts)} 条工单文本...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
    embeddings = np.array(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    log.info(f"📐 向量维度: {dim}")

    # 用 IndexFlatIP（内积），先对向量做归一化就等价于余弦相似度
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    log.success(f"FAISS 索引构建完成，共 {index.ntotal} 条向量")

    # 确保 db 目录存在
    os.makedirs(os.path.dirname(settings.faiss_index_path), exist_ok=True)

    # 保存索引
    faiss.write_index(index, settings.faiss_index_path)
    log.info(f"💾 索引已保存: {settings.faiss_index_path}")

    # 保存 ticket_id 到索引位置的映射
    mapping = {i: ticket_id for i, ticket_id in enumerate(ticket_ids)}
    with open(settings.faiss_mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    log.info(f"💾 ID映射已保存: {settings.faiss_mapping_path}")

    return index, mapping, model, dim


def save_meta(db, dim, count):
    """保存索引元数据到数据库"""
    meta = VectorIndexMeta(
        index_name="ticket_raw_text",
        model_name=settings.embedding_model,
        vector_dim=dim,
        ticket_count=count,
        built_at=datetime.now().isoformat(timespec="seconds"),
    )
    db.add(meta)
    db.commit()
    log.info("📝 索引元数据已写入数据库")


def quick_test(index, mapping, model, db):
    """快速测试检索效果"""
    log.info("🧪 快速检索测试（3个例子）:")
    test_queries = [
        "客户付了钱订单还是待支付",
        "优惠券用不了报错",
        "物流轨迹不更新",
    ]

    for query in test_queries:
        q_vec = model.encode([query])
        q_vec = np.array(q_vec, dtype="float32")
        faiss.normalize_L2(q_vec)
        scores, indices = index.search(q_vec, 3)

        log.info(f"  查询: {query}")
        for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
            ticket_id = mapping[int(idx)]
            ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            err_code = ticket.error_code if ticket and ticket.error_code else "无"
            text_preview = (ticket.raw_text[:30] + "...") if ticket and len(ticket.raw_text) > 30 else ticket.raw_text
            log.info(f"    Top{i+1} [{ticket_id}] 相似度={score:.3f} 错误码={err_code}")
            log.info(f"      {text_preview}")


def main():
    log.info("=" * 50)
    log.info("知答 MVP - D1 FAISS 向量索引构建")
    log.info("=" * 50)

    db = SessionLocal()
    try:
        tickets = load_tickets(db)

        if not tickets:
            log.error("工单表为空，先运行 scripts/init_db.py 灌数据")
            return

        index, mapping, model, dim = build_index(tickets)
        save_meta(db, dim, len(tickets))
        quick_test(index, mapping, model, db)
    finally:
        db.close()

    log.success("🎉 FAISS 索引构建全部完成！")


if __name__ == "__main__":
    main()
