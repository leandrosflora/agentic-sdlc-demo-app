from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Callable


def _response(start_response: Callable, status: str, payload: dict) -> list[bytes]:
    encoded = json.dumps(payload, sort_keys=True).encode()
    start_response(status, [
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(encoded))),
        ("Cache-Control", "no-store"),
    ])
    return [encoded]


def application(environ: dict, start_response: Callable) -> list[bytes]:
    path = environ.get("PATH_INFO", "/")
    digest = os.environ.get("ARTIFACT_DIGEST", "development")
    if path == "/health":
        healthy = os.environ.get("DEMO_HEALTH_MODE", "healthy") == "healthy"
        return _response(
            start_response, "200 OK" if healthy else "503 Service Unavailable",
            {"status": "healthy" if healthy else "unhealthy", "digest": digest},
        )
    if path == "/ready":
        return _response(start_response, "200 OK", {"status": "ready", "digest": digest})
    if path == "/version":
        return _response(start_response, "200 OK", {"digest": digest})
    if path == "/":
        return _response(start_response, "200 OK", {
            "service": "agentic-sdlc-demo-app",
            "message": "Deployed by the governed Agentic SDLC workflow",
            "digest": digest,
            "timestamp": datetime.now(UTC).isoformat(),
        })
    return _response(start_response, "404 Not Found", {"error": "not_found", "path": path})
