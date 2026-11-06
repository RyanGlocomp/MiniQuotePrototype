"""M0: /health answers even when the model server is down. Never calls the real Ollama."""
from fastapi.testclient import TestClient

from app import config
from app.main import app


def test_health_reports_llm_down_without_crashing(monkeypatch):
    monkeypatch.setattr(config, "LLM_BASE_URL", "http://127.0.0.1:9/v1")  # nothing listens here
    body = TestClient(app).get("/health").json()
    assert body["checks"]["api"]["ok"] is True
    assert body["checks"]["templates"] == {"ok": True, "count": 1}
    assert body["checks"]["llm"]["ok"] is False
    assert body["ok"] is False


def test_templates_lists_demo_client():
    assert TestClient(app).get("/templates").json() == [
        {"client": "Demo Client", "brand": "Demo Brand", "template_id": "demo_client", "version": 1}
    ]
