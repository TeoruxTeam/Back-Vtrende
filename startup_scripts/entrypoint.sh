#!/bin/sh

# Debugging step to list contents of /app
ls -l /app

# Verify wait-for-it.sh exists and is executable
if [ -f /app/startup_scripts/wait-for-it.sh ]; then
    echo "wait-for-it.sh found"
else
    echo "wait-for-it.sh not found"
    exit 1
fi

/app/startup_scripts/wait-for-it.sh vivli_db:5432 --strict --timeout=60 -- echo "Database is up"

if [ "$ENTRYPOINT_BACKEND" = 'true' ]; then
    echo "Starting Uvicorn... '$ENTRYPOINT_BACKEND'"
    alembic upgrade head
    pytest --asyncio-mode=auto  
    poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --reload

elif [ "$ENTRYPOINT_CELERY_WORKER" = 'true' ]; then
    echo "Starting Celery worker... '$ENTRYPOINT_CELERY_WORKER'"
    celery -A core.celery worker --loglevel=debug -E
    celery -A core.celery inspect registered
    
elif [ "$ENTRYPOINT_CELERY_BEAT" = 'true' ]; then
    echo "Starting Celery beat... '$ENTRYPOINT_CELERY_BEAT'"
    celery -A core.celery beat --loglevel=info

else
    echo "No valid service specified. Check environment variables."
    exit 1
fi