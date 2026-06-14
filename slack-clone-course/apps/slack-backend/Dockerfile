# Multi-stage build for the Django/Channels/Celery backend.
# Stage 1 builds wheels; stage 2 is a lean runtime image with no build toolchain.
# (New to Docker? See ../../../kubernetes-course/01-containers-docker/ — we don't
#  re-teach image/layer/Dockerfile basics here.)

# ── Stage 1: build dependencies into wheels ────────────────────────────────────
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
# Build tools only needed to compile any wheels; they stay in this stage.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ── Stage 2: lean runtime ──────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install prebuilt wheels — no compiler in the final image.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy the application code (after deps, so code changes don't bust the deps layer).
COPY . .

# Run as a non-root user (security best practice).
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
# Default command: serve ASGI (HTTP + WebSockets). Overridden for worker/beat in compose/k8s.
CMD ["web"]
