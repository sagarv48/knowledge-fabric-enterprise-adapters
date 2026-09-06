# ==============================================================================
# Enterprise Adapters - Multi-Stage Production Dockerfile
# ==============================================================================

# --- Stage 1: Build & Packaging ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir .

# --- Stage 2: Minimal Hardened Runtime ---
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Knowledge Fabric Enterprise Adapters" \
      org.opencontainers.image.description="Private enterprise adapter layer and SaaS connectors" \
      org.opencontainers.image.vendor="Knowledge Fabric Contributors" \
      org.opencontainers.image.licenses="Apache-2.0"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create secure non-root system user and group (UID/GID 10001)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -m -d /home/appuser -s /bin/bash appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

CMD ["python", "-m", "enterprise_adapters.server"]
