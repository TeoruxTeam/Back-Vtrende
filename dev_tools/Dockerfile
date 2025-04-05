FROM python:3.12

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry config installer.max-workers 3 \
    && poetry install --no-interaction --no-ansi --no-root \
    && poetry show

ENTRYPOINT ["/app/startup_scripts/entrypoint.sh"]
