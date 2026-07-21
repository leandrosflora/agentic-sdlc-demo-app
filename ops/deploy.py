from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / ".demo" / "deployment.json"
LOG_PATH = ROOT / ".demo" / "server.log"


def read_state() -> dict:
    if not STATE_PATH.exists():
        return {"current_digest": None, "previous_digest": None, "pid": None, "history": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def write_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(STATE_PATH)


def stop(pid: int | None) -> None:
    if not pid:
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.2)
    except ProcessLookupError:
        pass


def launch(digest: str, unhealthy: bool = False) -> int:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["ARTIFACT_DIGEST"] = digest
    env["DEMO_HEALTH_MODE"] = "unhealthy" if unhealthy else "healthy"
    with LOG_PATH.open("ab") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "demo_app.server", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return process.pid


def wait_until_started() -> None:
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/ready", timeout=0.5).read()
            return
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"demo server did not start; inspect {LOG_PATH}")


def deploy() -> None:
    digest = os.environ.get("ARTIFACT_DIGEST")
    if not digest:
        raise ValueError("ARTIFACT_DIGEST is required")
    state = read_state()
    stop(state.get("pid"))
    previous = state.get("current_digest")
    pid = launch(digest, os.environ.get("P6_DEMO_FORCE_UNHEALTHY") == "true")
    wait_until_started()
    state.update({"previous_digest": previous, "current_digest": digest, "pid": pid})
    state["history"].append({"action": "deploy", "digest": digest})
    write_state(state)
    print(json.dumps({"status": "deployed", "digest": digest, "pid": pid}))


def rollback() -> None:
    state = read_state()
    target = os.environ.get("ARTIFACT_DIGEST") or state.get("previous_digest")
    if not target:
        raise ValueError("no previous digest available for rollback")
    failed = state.get("current_digest")
    stop(state.get("pid"))
    pid = launch(target)
    wait_until_started()
    state.update({"current_digest": target, "pid": pid})
    state["history"].append({"action": "rollback", "from": failed, "to": target})
    write_state(state)
    print(json.dumps({"status": "rolled_back", "from": failed, "to": target, "pid": pid}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("deploy", "rollback", "stop", "status"))
    args = parser.parse_args()
    if args.action == "deploy":
        deploy()
    elif args.action == "rollback":
        rollback()
    elif args.action == "stop":
        state = read_state()
        stop(state.get("pid"))
        state["pid"] = None
        write_state(state)
    else:
        print(json.dumps(read_state(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
