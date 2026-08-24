FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/app ./app
COPY backend/docker-entrypoint.sh /usr/local/bin/cat-ci-entrypoint
COPY postgres/init/ /demo-seed/
RUN chmod +x /usr/local/bin/cat-ci-entrypoint
EXPOSE 8000
ENTRYPOINT ["cat-ci-entrypoint"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
