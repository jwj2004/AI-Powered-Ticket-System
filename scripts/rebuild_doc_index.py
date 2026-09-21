"""按当前切块逻辑重写已审批文档的 document_chunk，并重建文档 FAISS 索引。

FAQ 文档走 split_document（单条 Q&A），普通文档仍是 500 字重叠 50。
用法：python scripts/rebuild_doc_index.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_service import ensure_chunk_type_column, split_document
from app.services.vector_retriever import VectorRetriever


def main() -> None:
    ensure_chunk_type_column()
    db = SessionLocal()
    texts: list[str] = []
    chunk_ids: list[int] = []
    try:
        docs = (
            db.query(Document)
            .filter(Document.approved.is_(True))
            .order_by(Document.id)
            .all()
        )
        for doc in docs:
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            parts = split_document(doc.content or "", doc.title)
            print(f"doc {doc.id} approved={doc.approved} chunks={len(parts)} title={doc.title}")
            for index, (chunk_text, chunk_type) in enumerate(parts):
                row = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=index,
                    content=chunk_text,
                    chunk_type=chunk_type,
                )
                db.add(row)
                db.flush()
                texts.append(chunk_text)
                chunk_ids.append(row.id)
        db.commit()
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
