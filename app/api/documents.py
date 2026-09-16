import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.doc_version import DocVersion
from app.services.document_service import (
    parse_file,
    create_document,
    delete_document,
    update_document,
)

router = APIRouter(prefix="/api/documents", tags=["文档管理"])


class DocumentResponse(BaseModel):
    id: int
    space_id: int
    title: str
    content_type: str
    version: int
    owner_id: Optional[int] = None


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentResponse]


class UpdateRequest(BaseModel):
    content: str


class VersionResponse(BaseModel):
    id: int
    version: int
    created_at: str


@router.get("", response_model=DocumentListResponse)
def list_documents(
    space_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Document)
    if space_id:
        q = q.filter(Document.space_id == space_id)
    docs = q.order_by(Document.updated_at.desc()).all()
    return {
        "total": len(docs),
        "items": [
            DocumentResponse(
                id=d.id, space_id=d.space_id, title=d.title,
                content_type=d.content_type, version=d.version, owner_id=d.owner_id,
            )
            for d in docs
        ],
    }


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    space_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    if ext not in ("pdf", "docx", "md", "txt"):
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        content_bytes = await file.read()
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        text = parse_file(tmp_path, ext)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"文件解析失败: {e}")
    finally:
        os.unlink(tmp_path)

    doc = create_document(
        db, space_id=space_id, title=file.filename,
        content=text, content_type=ext, owner_id=user.id,
    )
    return DocumentResponse(
        id=doc.id, space_id=doc.space_id, title=doc.title,
        content_type=doc.content_type, version=doc.version, owner_id=doc.owner_id,
    )


@router.put("/{doc_id}")
def edit_document(
    doc_id: int,
    req: UpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        doc = update_document(db, doc_id, req.content)
        return {"id": doc.id, "version": doc.version, "message": "更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{doc_id}")
def remove_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    delete_document(db, doc_id)
    return {"ok": True}


@router.get("/{doc_id}/versions", response_model=list[VersionResponse])
def list_versions(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    versions = (
        db.query(DocVersion)
        .filter(DocVersion.document_id == doc_id)
        .order_by(DocVersion.version.desc())
        .all()
    )
    return [
        VersionResponse(id=v.id, version=v.version, created_at=v.created_at.isoformat() if v.created_at else "")
        for v in versions
    ]
