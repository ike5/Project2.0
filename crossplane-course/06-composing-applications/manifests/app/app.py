"""A tiny sample app for the Crossplane course.

Its only job is to prove that connection details reached it. It reports which
environment variables it received WITHOUT ever printing the password -- which is
the whole point of the connection-secret mechanism.
"""
import os
import socket

from flask import Flask, jsonify

app = Flask(__name__)


def db_configured() -> bool:
    return all(os.environ.get(k) for k in ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD"))


def db_reachable() -> bool:
    host, port = os.environ.get("DB_HOST"), os.environ.get("DB_PORT")
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            return True
    except OSError:
        return False


@app.get("/")
def index():
    password = os.environ.get("DB_PASSWORD", "")
    return jsonify(
        app=os.environ.get("APP_NAME", "unknown"),
        served_by=socket.gethostname(),
        database={
            "configured": db_configured(),
            "host": os.environ.get("DB_HOST"),
            "port": os.environ.get("DB_PORT"),
            "user": os.environ.get("DB_USER"),
            # Report only that a password ARRIVED, never its value. An app that
            # logs its own credentials undoes the security the platform provides.
            "password_present": bool(password),
            "password_length": len(password),
            "reachable": db_reachable(),
        },
        storage={"bucket": os.environ.get("BUCKET_NAME")},
    )


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
