from sqlalchemy.orm import Session

from app.core.logger import log
from app.models.doc_space import DocSpace
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.doc_version import DocVersion


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def parse_pdf(file_path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def parse_docx(file_path: str) -> str:
    import docx
    doc = docx.Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_md(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "md": parse_md,
    "txt": parse_txt,
}


def parse_file(file_path: str, content_type: str) -> str:
    parser = PARSERS.get(content_type)
    if not parser:
        raise ValueError(f"不支持的文件类型: {content_type}")
    return parser(file_path)


def create_document(
    db: Session,
    space_id: int,
    title: str,
    content: str,
    content_type: str,
    owner_id: int,
) -> Document:
    doc = Document(
        space_id=space_id,
        title=title,
        content=content,
        content_type=content_type,
        version=1,
        owner_id=owner_id,
    )
    db.add(doc)
    db.flush()

    version = DocVersion(
        document_id=doc.id,
        version=1,
        content=content,
    )
    db.add(version)

    chunks = split_text(content)
    chunk_ids = []
    for i, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=i,
            content=chunk_text,
        )
        db.add(chunk)
        db.flush()
        chunk_ids.append(chunk.id)

    db.commit()
    db.refresh(doc)

    # 向量化入 FAISS 索引
    if chunks:
        from app.services.vector_retriever import VectorRetriever
        VectorRetriever.add_document_chunks(chunks, chunk_ids)

    log.info(f"文档创建: {title} (space={space_id}, chunks={len(chunks)})")
    return doc


def delete_document(db: Session, doc_id: int):
    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
    chunk_ids = [c.id for c in chunks]

    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    db.query(DocVersion).filter(DocVersion.document_id == doc_id).delete()
    db.query(Document).filter(Document.id == doc_id).delete()
    db.commit()

    if chunk_ids:
        from app.services.vector_retriever import VectorRetriever
        VectorRetriever.remove_document_chunks(chunk_ids)

    log.info(f"文档删除: id={doc_id}")


def update_document(db: Session, doc_id: int, content: str, title: str | None = None):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise ValueError("文档不存在")

    old_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
    old_chunk_ids = [c.id for c in old_chunks]

    doc.version += 1
    doc.content = content
    if title is not None:
        doc.title = title

    version = DocVersion(
        document_id=doc.id,
        version=doc.version,
        content=content,
    )
    db.add(version)

    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    chunks = split_text(content)
    chunk_ids = []
    for i, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=doc_id,
            chunk_index=i,
            content=chunk_text,
        )
        db.add(chunk)
        db.flush()
        chunk_ids.append(chunk.id)

    db.commit()
    db.refresh(doc)

    # 重建该文档的向量索引
    if old_chunk_ids:
        from app.services.vector_retriever import VectorRetriever
        VectorRetriever.remove_document_chunks(old_chunk_ids)
    if chunks:
        from app.services.vector_retriever import VectorRetriever
        VectorRetriever.add_document_chunks(chunks, chunk_ids)

    log.info(f"文档更新: {doc.title} v{doc.version} (chunks={len(chunks)})")
    return doc


def rollback_document(db: Session, doc_id: int, target_version: int):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise ValueError("文档不存在")

    target = (
        db.query(DocVersion)
        .filter(DocVersion.document_id == doc_id, DocVersion.version == target_version)
        .first()
    )
    if not target:
        raise ValueError(f"版本 {target_version} 不存在")

    old_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
    old_chunk_ids = [c.id for c in old_chunks]

    doc.version += 1
    doc.content = target.content

    new_version = DocVersion(
        document_id=doc.id,
        version=doc.version,
        content=target.content,
    )
    db.add(new_version)

    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
    chunks = split_text(target.content)
    chunk_ids = []
    for i, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=doc_id,
            chunk_index=i,
            content=chunk_text,
        )
        db.add(chunk)
        db.flush()
        chunk_ids.append(chunk.id)

    db.commit()
    db.refresh(doc)

    if old_chunk_ids:
        from app.services.vector_retriever import VectorRetriever
        VectorRetriever.remove_document_chunks(old_chunk_ids)
    if chunks:
        from app.services.vector_retriever import VectorRetriever
        VectorRetriever.add_document_chunks(chunks, chunk_ids)

    log.info(f"文档回滚: {doc.title} v{doc.version} (回滚至 v{target_version})")
    return doc
