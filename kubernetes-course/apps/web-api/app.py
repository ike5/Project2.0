"""
web-api: a deliberately tiny Flask app used throughout the course.

It is designed to demonstrate Kubernetes concepts, so it exposes:
  GET /            -> greeting + which pod/host served it (great for load-balancing demos)
  GET /healthz     -> liveness probe target (always 200 unless we toggle it)
  GET /readyz      -> readiness probe target (becomes 503 after /toggle-ready)
  GET /config      -> echoes env/config so you can see ConfigMaps & Secrets land
  GET /work        -> burns CPU briefly, for HPA autoscaling demos
  POST /toggle-ready -> flip readiness on/off to watch Services add/remove this pod

Config is read from environment variables so we can inject it via ConfigMaps/Secrets.
"""
import os
import socket
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

# --- config from the environment (set these via ConfigMaps/Secrets in K8s) ---
GREETING = os.environ.get("GREETING", "Hello from web-api")
COLOR = os.environ.get("COLOR", "blue")
APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")
# A "secret" we only echo as masked, to show Secret injection without leaking it.
API_TOKEN = os.environ.get("API_TOKEN", "")

# readiness can be toggled at runtime to demonstrate readiness probes
_ready = True


@app.get("/")
def index():
    return jsonify(
        message=GREETING,
        color=COLOR,
        version=APP_VERSION,
        served_by=socket.gethostname(),  # the pod name, when running in K8s
    )


@app.get("/healthz")
def healthz():
    # Liveness: is the process alive? Keep this cheap and dependency-free.
    return jsonify(status="ok"), 200


@app.get("/readyz")
def readyz():
    # Readiness: should we receive traffic right now?
    if _ready:
        return jsonify(status="ready"), 200
    return jsonify(status="not-ready"), 503


@app.post("/toggle-ready")
def toggle_ready():
    global _ready
    _ready = not _ready
    return jsonify(ready=_ready)


@app.get("/config")
def config():
    return jsonify(
        greeting=GREETING,
        color=COLOR,
        version=APP_VERSION,
        # never echo a secret in cleartext — show only that it was injected
        api_token_present=bool(API_TOKEN),
        api_token_masked=("*" * len(API_TOKEN)) if API_TOKEN else "",
        all_env_keys=sorted(os.environ.keys()),
    )


@app.get("/work")
def work():
    # Busy-loop for ~`ms` milliseconds to generate CPU load for HPA demos.
    ms = int(request.args.get("ms", "250"))
    deadline = time.time() + ms / 1000.0
    iterations = 0
    while time.time() < deadline:
        iterations += 1
    return jsonify(did_work_ms=ms, iterations=iterations, served_by=socket.gethostname())


if __name__ == "__main__":
    # 0.0.0.0 so it's reachable from outside the container.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
