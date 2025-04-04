import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

from asgiref.sync import async_to_sync
from celery import Celery, Task
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from redis.asyncio import Redis

from admin.facade import IAdminFacade
from core.container import Container
from core.environment import env
from core.logger import logger
from core.redis_client import RedisPool
from locations.schemas import LocationDTO
from locations.services import ILocationService
from stats.schemas import ActivityStatsSchema
from stats.services import IStatsService

# Celery app setup
app = Celery(
    "vivli",
    broker=f"redis://:{env.redis_password}@{env.redis_host}:{env.redis_port}/{env.redis_db}",
    backend=f"redis://:{env.redis_password}@{env.redis_host}:{env.redis_port}/{env.redis_db}",
)

app.conf.beat_schedule = {
    "export-activity-stats-every-hour": {
        "task": "export_activity_stats",
        "schedule": crontab(minute=0, hour="*"),
    },
    "cancel-pending-orders-every-day": {
        "task": "cancel_pending_orders",
        "schedule": crontab(minute=0, hour=0),
    },
}

# Celery configuration
app.conf.update(
    worker_hijack_root_logger=False,  # Отключение захвата root-логгера Celery
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=4,
    task_always_eager=False,
)

# Redis client setup
redis_pool: RedisPool = Container().redis_pool()


@app.task(bind=True, base=Task, name="update_address_by_coordinates")
def update_address_by_coordinates(self):
    async def main():
        LOCK_KEY = "update_address_by_coordinates_lock"
        LOCK_TIMEOUT = 60
        have_lock = False
        async with redis_pool.get_redis() as redis_client:
            try:
                have_lock = await redis_client.set(
                    LOCK_KEY, "1", nx=True, ex=LOCK_TIMEOUT
                )
                if not have_lock:
                    logger.info(
                        "Задача уже выполняется другим воркером. Пропуск выполнения."
                    )
                    return

                while True:
                    try:
                        location_service: ILocationService = (
                            Container().location_service()
                        )
                        oldest_locations: List[LocationDTO] = (
                            await location_service.get_locations_without_address(
                                limit=100
                            )
                        )

                        if oldest_locations:
                            await location_service.update_address_by_coordinates(
                                oldest_locations
                            )
                            await asyncio.sleep(5)
                        else:
                            logger.info("Нет локаций для обновления.")
                            await asyncio.sleep(30)

                        await asyncio.sleep(2)

                    except SoftTimeLimitExceeded:
                        logger.error("Превышено время выполнения задачи.")
                        break

                    except Exception as e:
                        logger.error(f"Ошибка при выполнении задачи: {e}")
                        await asyncio.sleep(5)

            finally:
                if have_lock:
                    await redis_client.delete(LOCK_KEY)

    asyncio.run(main())


@app.task(bind=True, base=Task, name="export_activity_stats")
def export_activity_stats(self):
    async def main():
        LOCK_KEY = "export_activity_stats_lock"
        LOCK_TIMEOUT = 60
        have_lock = False
        async with redis_pool.get_redis() as redis_client:
            try:
                have_lock = await redis_client.set(
                    LOCK_KEY, "1", nx=True, ex=LOCK_TIMEOUT
                )
                if not have_lock:
                    logger.info(
                        "Задача уже выполняется другим воркером. Пропуск выполнения."
                    )
                    return

                try:
                    start_date = datetime.now(timezone.utc) - timedelta(hours=1)
                    end_date = datetime.now(timezone.utc)

                    request_count = await redis_client.get("request_count") or 0
                    request_count = int(request_count)
                    logger.warning(f"count {request_count}")
                    stats = ActivityStatsSchema(
                        count=int(request_count),
                        start_date=start_date,
                        end_date=end_date,
                    )
                    logger.info(f"Activity stats: {stats}")

                    await redis_client.set("request_count", 0)
                    logger.warning(f"restarted request count")
                    stats_service: IStatsService = Container().stats_service()
                    logger.warning(f"stats service {stats_service}")
                    await stats_service.add_activity_stats(stats)

                except Exception as e:
                    logger.error(f"Ошибка при выгрузке статистики активности: {e}")

            finally:
                if have_lock:
                    await redis_client.delete(LOCK_KEY)

    asyncio.run(main())


@app.task(bind=True, base=Task, name="cancel_pending_orders")
def cancel_pending_orders(self):
    async def main():
        LOCK_KEY = "cancel_pending_orders_lock"
        LOCK_TIMEOUT = 60
        have_lock = False
        async with redis_pool.get_redis() as redis_client:
            try:
                have_lock = await redis_client.set(
                    LOCK_KEY, "1", nx=True, ex=LOCK_TIMEOUT
                )
                if not have_lock:
                    logger.info(
                        "Задача уже выполняется другим воркером. Пропуск выполнения."
                    )
                    return

                try:
                    promotion_service = Container().promotion_service()
                    order_ids = await promotion_service.get_pendings_to_cancel()

                    if order_ids:
                        logger.info(f"Отмена ордеров с ID: {order_ids}")
                        await promotion_service.cancel_orders(order_ids)
                    else:
                        logger.info("Нет ордеров для отмены.")

                except Exception as e:
                    logger.error(f"Ошибка при выполнении задачи отмены ордеров: {e}")

            finally:
                if have_lock:
                    await redis_client.delete(LOCK_KEY)

    asyncio.run(main())


update_address_by_coordinates.delay()
