"""
查询服务 - 错误码查询 + 埋点记录
"""
from typing import Optional

from app.core.logger import log
from app.core.database import SessionLocal
from app.models import ErrorCode, QueryLog


def lookup_error_code(code: str) -> Optional[dict]:
    """
    根据错误码查询详情
    返回 dict 或 None（未找到）
    """
    db = SessionLocal()
    try:
        ec = db.query(ErrorCode).filter(ErrorCode.code == code).first()
        if not ec:
            return None

        # 把分号分隔的字符串转成数组
        causes = [c.strip() for c in ec.known_causes.split(";") if c.strip()] if ec.known_causes else []
        versions = [v.strip() for v in ec.related_versions.split(";") if v.strip()] if ec.related_versions else []

        return {
            "code": ec.code,
            "name": ec.name,
            "meaning": ec.meaning,
            "trigger_condition": ec.trigger_condition,
            "causes": causes,
            "solution": ec.solution,
            "related_versions": versions,
        }
    finally:
        db.close()


def record_query_log(
    query_id: str,
    raw_text: str,
    customer_id: Optional[str] = None,
    error_code: Optional[str] = None,
    confidence: str = "high",
    latency_ms: int = 0,
):
    """记录查询埋点"""
    from datetime import datetime
    db = SessionLocal()
    try:
        log_item = QueryLog(
            query_id=query_id,
            timestamp=datetime.now().isoformat(timespec="seconds"),
            raw_text=raw_text[:1024],
            customer_id=customer_id,
            error_code=error_code,
            confidence=confidence,
            latency_ms=latency_ms,
            copied=0,
            thumbs_down=0,
        )
        db.add(log_item)
        db.commit()
        log.debug(f"记录 query_log: {query_id}")
    except Exception as e:
        db.rollback()
        log.error(f"记录 query_log 失败: {e}")
    finally:
        db.close()


def update_feedback(query_id: str, copied: bool = False, thumbs_down: bool = False) -> bool:
    """更新反馈埋点"""
    db = SessionLocal()
    try:
        log_item = db.query(QueryLog).filter(QueryLog.query_id == query_id).first()
        if not log_item:
            log.warning(f"反馈更新失败：query_id={query_id} 不存在")
            return False

        if copied:
            log_item.copied = 1
        if thumbs_down:
            log_item.thumbs_down = 1

        db.commit()
        log.info(f"反馈已更新: query_id={query_id}, copied={copied}, thumbs_down={thumbs_down}")
        return True
    except Exception as e:
        db.rollback()
        log.error(f"更新反馈失败: {e}")
        return False
    finally:
        db.close()
