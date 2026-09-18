from sqlalchemy.orm import Session

from app.models.operation_log import OperationLog


def log_action(db: Session, user_id: int, username: str, action: str, resource: str = "", detail: str = ""):
    entry = OperationLog(
        user_id=user_id,
        username=username,
        action=action,
        resource=resource,
        detail=detail,
    )
    db.add(entry)
    db.commit()
