# hero siege loot filter — one container: build the SPA, serve SPA + /api.
# Context is the repo root (so the hsfilter package + research/ come along).

FROM node:22-alpine AS web
WORKDIR /w
RUN corepack enable
COPY app/frontend/package.json app/frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY app/frontend/ ./
RUN pnpm build

FROM python:3.13-slim AS run
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv

# the core library + the read-only catalog
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY research/ ./research/
COPY data/ ./data/
COPY app/backend/pyproject.toml ./app/backend/pyproject.toml
COPY app/backend/app.py ./app/backend/app.py

RUN pip install --no-cache-dir "." "fastapi>=0.115" "uvicorn[standard]>=0.32"

COPY --from=web /w/dist ./app/backend/static

ENV HSFILTER_RESEARCH_DIR=/srv/research
RUN python -c "from hsfilter.catalog import validate_all; e=validate_all(); assert not e, e" \
 && useradd -r -u 10001 app
USER app
EXPOSE 8000
WORKDIR /srv/app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
