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
from app.models.doc_space import DocSpace
from app.models.doc_version import DocVersion
from app.services.document_service import (
    parse_file,
    create_document,
    delete_document,
    update_document,
    rollback_document,
)
from app.api.doc_spaces import filter_spaces_by_role
from app.services.log_service import log_action

router = APIRouter(prefix="/api/documents", tags=["文档管理"])


class UpdateRequest(BaseModel):
    title: Optional[str] = None
    content: str
    space_id: Optional[int] = None


class RollbackRequest(BaseModel):
    target_version: int


class VersionResponse(BaseModel):
    version: int
    created_at: str


@router.get("")
def list_documents(
    space_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Document, DocSpace).join(DocSpace, Document.space_id == DocSpace.id)
    if space_id:
        q = q.filter(Document.space_id == space_id)
    rows = q.order_by(Document.updated_at.desc()).all()

    # 按角色过滤空间
    spaces = [space for _, space in rows]
    if user.role != "admin":
        visible_space_ids = {s.id for s in filter_spaces_by_role(spaces, user.role)}
        rows = [(doc, space) for doc, space in rows if space.id in visible_space_ids]

    result = []
    for doc, space in rows:
        owner_name = ""
        if doc.owner_id:
            owner = db.query(User).filter(User.id == doc.owner_id).first()
            if owner:
                owner_name = owner.username
        result.append({
            "id": doc.id,
            "title": doc.title,
            "space": space.name,
            "version": doc.version,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else "",
            "owner": owner_name,
            "approved": doc.approved,
            "view_count": doc.view_count or 0,
        })
    return result


@router.get("/{doc_id}")
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查空间权限
    space = db.query(DocSpace).filter(DocSpace.id == doc.space_id).first()
    if space and user.role != "admin":
        visible = filter_spaces_by_role([space], user.role)
        if not visible:
            raise HTTPException(status_code=403, detail="无权访问此文档")

    doc.view_count = (doc.view_count or 0) + 1
    db.commit()
    return {
        "id": doc.id,
        "title": doc.title,
        "content": doc.content or "",
        "space_id": doc.space_id,
        "version": doc.version,
        "approved": doc.approved,
        "view_count": doc.view_count,
    }


@router.post("/upload")
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
    chunk_count = db.query(Document).filter(Document.id == doc.id).first()
    log_action(db, user.id, user.username, "upload_document", resource=f"doc:{doc.id}", detail=file.filename)
    db.commit()
    return {"id": doc.id, "title": doc.title, "chunks": chunk_count.version if chunk_count else 0}


@router.put("/{doc_id}")
def edit_document(
    doc_id: int,
    req: UpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        doc = update_document(db, doc_id, req.content, title=req.title)
        return {"id": doc.id, "version": doc.version, "title": doc.title}
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
        VersionResponse(version=v.version, created_at=v.created_at.isoformat() if v.created_at else "")
        for v in versions
    ]


@router.post("/{doc_id}/rollback")
def rollback_document_api(
    doc_id: int,
    req: RollbackRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    try:
        doc = rollback_document(db, doc_id, req.target_version)
        return {"id": doc.id, "version": doc.version, "title": doc.title}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{doc_id}/approve")
def approve_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    doc.approved = True
    log_action(db, user.id, user.username, "approve_document", resource=f"doc:{doc_id}", detail=doc.title)
    db.commit()
    return {"ok": True}


@router.post("/{doc_id}/reject")
def reject_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    title = doc.title
    delete_document(db, doc_id)
    log_action(db, user.id, user.username, "reject_document", resource=f"doc:{doc_id}", detail=title)
    db.commit()
    return {"ok": True}
