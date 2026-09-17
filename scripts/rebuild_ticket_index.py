"""重建工单 FAISS 索引（用 BGE-small-zh-v1.5 替换旧模型）"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.models.ticket import Ticket
from app.services.vector_retriever import VectorRetriever


def rebuild():
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).filter(Ticket.raw_text.isnot(None)).all()
        texts = [t.raw_text for t in tickets]
        ticket_ids = [t.ticket_id for t in tickets]
        print(f"共 {len(texts)} 条工单需要重建索引")
    finally:
        db.close()

    VectorRetriever.init()

    import faiss
    import numpy as np

    embeddings = VectorRetriever._model.encode(texts, show_progress_bar=True, batch_size=64)
    embeddings = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(embeddings)

    dim = VectorRetriever._dim
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    mapping = {str(i): tid for i, tid in enumerate(ticket_ids)}

    faiss.write_index(index, "db/ticket_index.faiss")
    with open("db/ticket_id_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"工单索引重建完成: {index.ntotal} 条, 维度 {dim}")


if __name__ == "__main__":
    rebuild()
