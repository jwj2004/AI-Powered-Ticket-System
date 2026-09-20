"""pytest 公共夹具：临时库 + mock 检索 + 关闭 LLM。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.agent import graph as graph_mod
from backend.config import get_settings


@pytest.fixture(autouse=True)
def _isolate_llm_and_graph(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("ENABLE_CROSS_ENCODER", "false")
    get_settings.cache_clear()
    graph_mod._GRAPH = None
    yield
    get_settings.cache_clear()
    graph_mod._GRAPH = None


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "zhida_b.db"))
    monkeypatch.setenv("USE_MOCK_RETRIEVE", "true")
    monkeypatch.setenv("JWT_SECRET", "zhida-jwt-shared-2026")
    get_settings.cache_clear()
    graph_mod._GRAPH = None

    from backend.main import app
    from backend import store

    store.init_db()
    return TestClient(app)
