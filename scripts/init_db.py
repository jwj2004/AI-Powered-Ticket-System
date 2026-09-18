"""
D1 - 数据初始化脚本（使用 SQLAlchemy）
功能：建表 + 灌三张 CSV 数据
用法：python scripts/init_db.py
"""
import os
import sys
import csv

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import log, init_db, SessionLocal
from app.models import ErrorCode, CustomerAsset, Ticket

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def seed_error_codes(db):
    """灌错误码数据"""
    csv_path = os.path.join(DATA_DIR, "seed_error_codes.csv")
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obj = ErrorCode(
                code=row["code"],
                name=row["name"],
                meaning=row["meaning"],
                trigger_condition=row["trigger_condition"],
                known_causes=row["known_causes"],
                solution=row["solution"],
                related_versions=row["related_versions"],
            )
            db.merge(obj)  # merge = 存在则更新，不存在则插入
            count += 1
    db.commit()
    log.info(f"error_code 表灌入 {count} 条")
    return count


def seed_customers(db):
    """灌客户数据"""
    csv_path = os.path.join(DATA_DIR, "seed_customers.csv")
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            obj = CustomerAsset(
                customer_id=row["customer_id"],
                shop_name=row["shop_name"],
                plan=row["plan"],
                version=row["version"],
                enabled_modules=row["enabled_modules"],
                key_configs=row["key_configs"],
                recent_changes=row["recent_changes"],
            )
            db.merge(obj)
            count += 1
    db.commit()
    log.info(f"customer_asset 表灌入 {count} 条")
    return count


def seed_tickets(db):
    """灌工单数据"""
    csv_path = os.path.join(DATA_DIR, "seed_tickets.csv")
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            handle_minutes = int(row["handle_minutes"]) if row["handle_minutes"] else None
            obj = Ticket(
                ticket_id=row["ticket_id"],
                customer_id=row["customer_id"],
                created_at=row["created_at"],
                error_code=row["error_code"],
                raw_text=row["raw_text"],
                solution_text=row["solution_text"],
                status=row["status"],
                handle_minutes=handle_minutes,
            )
            db.merge(obj)
            count += 1
    db.commit()
    log.info(f"ticket 表灌入 {count} 条")
    return count


def verify_data(db):
    """验证数据统计"""
    from app.models import QueryLog, VectorIndexMeta
    from sqlalchemy import func, inspect

    log.info("📊 数据统计：")
    for model, name in [
        (ErrorCode, "error_code"),
        (CustomerAsset, "customer_asset"),
        (Ticket, "ticket"),
        (QueryLog, "query_log"),
        (VectorIndexMeta, "vector_index_meta"),
    ]:
        # 自动取主键列
        pk = inspect(model).primary_key[0]
        count = db.query(func.count(pk)).scalar()
        log.info(f"  {name}: {count} 条")

    # Top 5 高频错误码
    top5 = (
        db.query(Ticket.error_code, func.count(Ticket.ticket_id).label("cnt"))
        .filter(Ticket.error_code != "")
        .group_by(Ticket.error_code)
        .order_by(func.count(Ticket.ticket_id).desc())
        .limit(5)
        .all()
    )
    log.info("🔥 高频错误码 Top 5：")
    for code, cnt in top5:
        log.info(f"  {code}: {cnt} 单")


def main():
    log.info("=" * 50)
    log.info("知答 MVP - D1 数据库初始化 (SQLAlchemy)")
    log.info("=" * 50)

    # 建表
    init_db()

    # 灌数据
    db = SessionLocal()
    try:
        seed_error_codes(db)
        seed_customers(db)
        seed_tickets(db)
        verify_data(db)
    finally:
        db.close()

    log.success("✅ 数据库初始化完成！")


if __name__ == "__main__":
    main()
