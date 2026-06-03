# A small, multi-stage-free Dockerfile kept simple on purpose so beginners can
# read every line. We optimize for clarity over absolute minimal size.

# 1. Start from a small official Python base image (pinned for reproducibility).
FROM python:3.12-slim

# 2. Don't write .pyc files and don't buffer stdout (logs appear immediately).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# 3. Create and use a working directory inside the image.
WORKDIR /app

# 4. Copy ONLY requirements first, then install. This leverages layer caching:
#    if app.py changes but requirements don't, the pip layer is reused (fast rebuilds).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Now copy the application code.
COPY app.py .

# 6. Run as a non-root user (good security hygiene; required by some clusters).
RUN useradd --create-home appuser
USER appuser

# 7. Document the port the app listens on.
EXPOSE 8080

# 8. The command that runs when the container starts.
CMD ["python", "app.py"]
