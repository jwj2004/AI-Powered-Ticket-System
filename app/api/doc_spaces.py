from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.doc_space import DocSpace

router = APIRouter(prefix="/api/doc-spaces", tags=["文档空间"])


@router.get("")
def list_spaces(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    spaces = db.query(DocSpace).all()
    return [{"id": s.id, "name": s.name} for s in spaces]
