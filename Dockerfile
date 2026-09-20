FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./
COPY profiles ./profiles

RUN python -m pip install --upgrade pip \
    && pip install \
        --index-url https://download.pytorch.org/whl/cpu \
        torch \
    && pip install .

EXPOSE 8000

HEALTHCHECK \
    --interval=30s \
    --timeout=5s \
    --start-period=20s \
    --retries=3 \
    CMD curl --fail http://127.0.0.1:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "jobintel.api:app", "--host", "0.0.0.0", "--port", "8000"]
