"""
pytest 测试基础设施
- 使用内存 SQLite 数据库，不污染开发数据
- 每个测试函数自动回滚
- 自动创建测试用户和 token
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.services.auth_service import create_user
from main import app


@pytest.fixture(scope="function")
def db_session():
    """内存数据库，测试完自动销毁"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # 创建测试用户
    create_user(db, "testadmin", "admin123", "admin")
    create_user(db, "testops", "ops123", "ops")
    create_user(db, "testnewbie", "newbie123", "newbie")

    db.commit()

    yield db
    db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient，数据库依赖注入指向内存数据库"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    """获取 admin token"""
    r = client.post("/api/auth/login", json={"username": "testadmin", "password": "admin123"})
    return r.json()["token"]


@pytest.fixture
def ops_token(client):
    """获取 ops token"""
    r = client.post("/api/auth/login", json={"username": "testops", "password": "ops123"})
    return r.json()["token"]


@pytest.fixture
def newbie_token(client):
    """获取 newbie token"""
    r = client.post("/api/auth/login", json={"username": "testnewbie", "password": "newbie123"})
    return r.json()["token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def ops_headers(ops_token):
    return {"Authorization": f"Bearer {ops_token}"}


@pytest.fixture
def newbie_headers(newbie_token):
    return {"Authorization": f"Bearer {newbie_token}"}
