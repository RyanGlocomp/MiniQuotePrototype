# Multi-arch base: builds natively as linux/arm64 on the DGX Spark.
FROM python:3.12-slim

# LibreOffice Calc only (no GUI) for stage a conversions and stage f recalc.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libreoffice-calc-nogui \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /usr/local/bin/uv

WORKDIR /srv/api
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app

# Run as a non-root user; job files stay owned by it.
ARG APP_UID=1000
RUN useradd --create-home --uid ${APP_UID} app
USER app
ENV PATH="/srv/api/.venv/bin:$PATH"
EXPOSE 8107
CMD ["sh", "-c", "exec uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT:-8107}"]
