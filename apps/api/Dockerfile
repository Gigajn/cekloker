# CekLoker API + worker — image yang sama untuk service `api` dan `worker`.
# Build context = ROOT repo (lihat infra/docker-compose.yml), karena API
# mengimpor packages/scraper-core + packages/flag-engine dari repo.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv/api:/srv/packages/scraper-core:/srv/packages/flag-engine

WORKDIR /srv/api

COPY apps/api/pyproject.toml apps/api/README.md ./
COPY apps/api/app ./app
COPY apps/api/migrations ./migrations
COPY apps/api/scripts ./scripts
COPY packages/scraper-core /srv/packages/scraper-core
COPY packages/flag-engine /srv/packages/flag-engine

RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 ceklok \
    && mkdir -p /srv/api/data && chown ceklok:ceklok /srv/api/data
USER ceklok

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
