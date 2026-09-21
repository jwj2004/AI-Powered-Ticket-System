"""临时脚本：把已审批文档的切块重新写入文档 FAISS 索引。

不改后端逻辑，只调用现有的 VectorRetriever.add_document_chunks。
用法：python scripts/rebuild_doc_index.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.vector_retriever import VectorRetriever


def main() -> None:
    db = SessionLocal()
    try:
        docs = (
            db.query(Document)
            .filter(Document.approved.is_(True))
            .order_by(Document.id)
            .all()
        )
        texts: list[str] = []
        chunk_ids: list[int] = []
        for doc in docs:
            rows = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == doc.id)
                .order_by(DocumentChunk.chunk_index)
                .all()
            )
            print(f"doc {doc.id} approved={doc.approved} chunks={len(rows)} title={doc.title}")
            for row in rows:
                texts.append(row.content)
                chunk_ids.append(row.id)
    finally:
        db.close()

    if not texts:
        print("没有已审批文档的切块，不写索引")
        return

    VectorRetriever.ensure_init()
    VectorRetriever._doc_index = faiss.IndexFlatIP(VectorRetriever._dim)
    VectorRetriever._doc_id_mapping = {}
    VectorRetriever.add_document_chunks(texts, chunk_ids)
    print(f"重建完成 ntotal={VectorRetriever._doc_index.ntotal} mapping={len(VectorRetriever._doc_id_mapping)}")


if __name__ == "__main__":
    main()
