import asyncio

from dependency_injector.wiring import Provide, inject

from core.container import Container
from core.logger import logger
from core.redis_client import RedisPool
from core.socketio_server import CustomSocketServer
from notifications.facade import INotificationFacade


@inject
def setup_notification_handlers(
    sio: CustomSocketServer,
    redis_pool: RedisPool = Provide[Container.redis_pool],
    notification_facade: INotificationFacade = Provide[Container.notification_facade],
):
    @sio.on("listen_for_notifications")
    async def listen_for_notifications(sid):
        async with redis_pool.get_redis() as redis_manager:
            user_id = await redis_manager.get(f"sid:{sid}")
            if user_id:
                user_id = int(user_id.decode("utf-8"))
                sio.start_background_task(
                    notification_facade.listen_for_notifications,
                    sio,
                    user_id,
                    redis_pool,
                )
