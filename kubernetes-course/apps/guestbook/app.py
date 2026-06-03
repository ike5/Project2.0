"""
guestbook: a small multi-tier app for the capstone.

It's a single Flask service that acts as BOTH the web frontend and the API, backed
by a Redis datastore. This gives a realistic "stateless app tier + stateful data
tier" topology to deploy on Kubernetes:

    browser -> guestbook (stateless, scalable) -> redis (stateful, persistent)

Endpoints:
  GET  /            -> HTML page listing messages + a form to add one
  GET  /healthz     -> liveness (process up)
  GET  /readyz      -> readiness (can reach Redis)
  GET  /api/messages          -> JSON list of messages
  POST /api/messages {"text"} -> add a message

Config via env:
  REDIS_HOST (default "redis"), REDIS_PORT (6379), REDIS_PASSWORD (optional),
  PAGE_TITLE (default "Guestbook")
"""
import os
import socket

import redis
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD") or None
PAGE_TITLE = os.environ.get("PAGE_TITLE", "Guestbook")
KEY = "guestbook:messages"

_r = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
    socket_connect_timeout=2, decode_responses=True,
)


def _messages():
    return _r.lrange(KEY, 0, 49)  # most recent 50


@app.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200


@app.get("/readyz")
def readyz():
    try:
        _r.ping()
        return jsonify(status="ready"), 200
    except Exception as exc:  # Redis unreachable -> not ready (no traffic)
        return jsonify(status="not-ready", error=str(exc)), 503


@app.get("/api/messages")
def list_messages():
    return jsonify(messages=_messages(), served_by=socket.gethostname())


@app.post("/api/messages")
def add_message():
    text = (request.get_json(silent=True) or {}).get("text") \
        or request.form.get("text", "")
    text = text.strip()
    if not text:
        return jsonify(error="text is required"), 400
    _r.lpush(KEY, text)
    _r.ltrim(KEY, 0, 199)
    return jsonify(ok=True), 201


@app.get("/")
def index():
    items = "".join(f"<li>{m}</li>" for m in _messages())
    html = f"""<!doctype html>
<html><head><title>{PAGE_TITLE}</title></head>
<body style="font-family: sans-serif; max-width: 40rem; margin: 2rem auto;">
  <h1>{PAGE_TITLE}</h1>
  <p style="color:#888">served by {socket.gethostname()}</p>
  <form method="post" action="/api/messages">
    <input name="text" placeholder="Leave a message" style="width:70%"/>
    <button type="submit">Sign</button>
  </form>
  <ul>{items or "<li><em>No messages yet — be the first!</em></li>"}</ul>
</body></html>"""
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
