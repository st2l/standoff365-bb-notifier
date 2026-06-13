# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install dependencies first for layer caching.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

RUN useradd --create-home --uid 10001 watcher \
    && mkdir -p /app/state \
    && chown -R watcher:watcher /app/state
USER watcher

VOLUME ["/app/state"]

ENTRYPOINT ["s365watch"]
