#!/bin/sh

if [ -f /app/startup_scripts/wait-for-it.sh ]; then
    echo "wait-for-it.sh found"
else
    echo "wait-for-it.sh not found"
    exit 1
fi

/app/startup_scripts/wait-for-it.sh marketplace_db:5432 --strict --timeout=60 -- echo "Database is up"

if [ "$ENTRYPOINT_BACKEND" = 'true' ]; then
    echo "Starting Uvicorn... '$ENTRYPOINT_BACKEND'"
    alembic upgrade head
    pytest --asyncio-mode=auto  
    poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "No valid service specified. Check environment variables."
    exit 1
fi