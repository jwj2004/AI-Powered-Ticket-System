import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User
from app.models.message import Message
from app.models.document import Document

router = APIRouter(prefix="/api/stats", tags=["统计"])


@router.get("/doc-citations")
def doc_citations(
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """文档引用 Top5：统计 assistant 消息中 citations_json 出现的 document_id 次数"""

    rows = db.query(Message.citations_json).filter(
        Message.role == "assistant",
        Message.citations_json.isnot(None),
    ).all()

    counter: Counter = Counter()
    for (citations_json,) in rows:
        try:
            citations = json.loads(citations_json)
            for c in citations:
                doc_id = c.get("document_id")
                if doc_id:
                    counter[doc_id] += 1
        except (json.JSONDecodeError, TypeError):
            continue

    top5 = counter.most_common(5)
    doc_ids = [doc_id for doc_id, _ in top5]
    docs = {d.id: d.title for d in db.query(Document).filter(Document.id.in_(doc_ids)).all()} if doc_ids else {}

    return [
        {"document_id": doc_id, "title": docs.get(doc_id, f"文档#{doc_id}"), "citations": cnt}
        for doc_id, cnt in top5
    ]
