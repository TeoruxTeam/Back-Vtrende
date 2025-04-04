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
COPY README.md /app/
COPY pyproject.toml poetry.lock /app/
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry config installer.max-workers 3 \
    && poetry install --no-interaction --no-ansi --no-root \
    && poetry show



RUN echo "Listing contents of /app after copying files:" \
    && ls -l /app

RUN chmod +x /app/startup_scripts/entrypoint.sh \
    && echo "Listing entrypoint.sh:" \
    && ls -l /app/startup_scripts/entrypoint.sh

RUN chmod +x /app/startup_scripts/wait-for-it.sh \
    && echo "Listing wait-for-it.sh:" \
    && ls -l /app/startup_scripts/wait-for-it.sh

RUN echo "Final listing of /app:" \
    && ls -l /app

ENTRYPOINT ["/app/startup_scripts/entrypoint.sh"]
