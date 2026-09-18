from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.models.doc_space import DocSpace

router = APIRouter(prefix="/api/doc-spaces", tags=["文档空间"])


class SpaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.get("")
def list_spaces(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    spaces = db.query(DocSpace).all()
    return [
        {"id": s.id, "name": s.name, "description": s.description or ""}
        for s in spaces
    ]


@router.post("")
def create_space(
    req: SpaceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    existing = db.query(DocSpace).filter(DocSpace.name == req.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="空间名已存在")
    space = DocSpace(name=req.name, description=req.description)
    db.add(space)
    db.commit()
    db.refresh(space)
    return {"id": space.id, "name": space.name, "ok": True}


@router.put("/{space_id}")
def update_space(
    space_id: int,
    req: SpaceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    space = db.query(DocSpace).filter(DocSpace.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="空间不存在")
    if req.name is not None:
        space.name = req.name
    if req.description is not None:
        space.description = req.description
    db.commit()
    return {"ok": True}


@router.delete("/{space_id}")
def delete_space(
    space_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    space = db.query(DocSpace).filter(DocSpace.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="空间不存在")
    db.delete(space)
    db.commit()
    return {"ok": True}
