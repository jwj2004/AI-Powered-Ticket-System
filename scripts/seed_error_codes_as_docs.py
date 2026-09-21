"""
把 error_code 表的 40 条错误码导出为文档，灌入文档索引
每个错误码一个文档，内容包含 code/name/meaning/trigger_condition/known_causes/solution
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.logger import log
from app.models.user import User
from app.models.doc_space import DocSpace
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.error_code import ErrorCode
from app.services.vector_retriever import VectorRetriever


def seed_error_codes_as_docs():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            log.error("admin 用户不存在，先运行 init_users.py")
            return

        space = db.query(DocSpace).filter(DocSpace.name == "客服文档").first()
        if not space:
            log.error("客服文档空间不存在")
            return

        existing = db.query(Document).filter(Document.title.like("错误码:%")).count()
        if existing > 0:
            log.info(f"已存在 {existing} 条错误码文档，跳过")
            return

        error_codes = db.query(ErrorCode).all()
        log.info(f"开始导出 {len(error_codes)} 条错误码为文档")

        for ec in error_codes:
            content = f"""错误码: {ec.code}
名称: {ec.name}
含义: {ec.meaning or ''}

触发条件:
{ec.trigger_condition or ''}

已知原因:
{ec.known_causes or ''}

解决方案:
{ec.solution or ''}

相关版本: {ec.related_versions or ''}
"""

            doc = Document(
                space_id=space.id,
                title=f"错误码:{ec.code} - {ec.name}",
                content=content,
                content_type="txt",
                version=1,
                owner_id=admin.id,
            )
            db.add(doc)
            db.flush()

            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=0,
                content=content,
            )
            db.add(chunk)
            db.flush()

            VectorRetriever.add_document_chunks([content], [chunk.id])

            log.info(f"  导出: {ec.code} - {ec.name}")

        db.commit()
        log.success(f"完成！共导出 {len(error_codes)} 条错误码文档")

    finally:
        db.close()


if __name__ == "__main__":
    seed_error_codes_as_docs()
