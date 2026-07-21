import json
import os

from demo_app.app import application


def request(path):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(application({"PATH_INFO": path}, start_response))
    return captured["status"], captured["headers"], json.loads(body)


def test_root_exposes_service_and_digest(monkeypatch):
    monkeypatch.setenv("ARTIFACT_DIGEST", "sha256:test")
    status, headers, body = request("/")
    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json"
    assert body["service"] == "agentic-sdlc-demo-app"
    assert body["digest"] == "sha256:test"


def test_health_is_healthy_by_default(monkeypatch):
    monkeypatch.delenv("DEMO_HEALTH_MODE", raising=False)
    status, _, body = request("/health")
    assert status == "200 OK"
    assert body["status"] == "healthy"


def test_health_can_trigger_observable_failure(monkeypatch):
    monkeypatch.setenv("DEMO_HEALTH_MODE", "unhealthy")
    status, _, body = request("/health")
    assert status == "503 Service Unavailable"
    assert body["status"] == "unhealthy"


def test_ready_version_and_not_found(monkeypatch):
    monkeypatch.setenv("ARTIFACT_DIGEST", "sha256:v1")
    assert request("/ready")[2]["status"] == "ready"
    assert request("/version")[2]["digest"] == "sha256:v1"
    status, _, body = request("/missing")
    assert status == "404 Not Found"
    assert body["error"] == "not_found"
