import socketio
from dependency_injector.wiring import Provide, inject

from auth.depends import get_current_confirmed_user
from auth.exceptions import InvalidTokenFormat, MissingToken
from auth.facade import IAuthFacade
from core.container import Container
from core.exceptions import AuthError
from core.logger import logger
from core.redis_client import RedisPool
from core.socketio_server import CustomSocketServer
from users.services import IUserService


@inject
def setup_auth_handlers(
    sio: CustomSocketServer,
    user_service: IUserService = Provide[Container.user_service],
    auth_facade: IAuthFacade = Provide[Container.auth_service],
    redis_pool: RedisPool = Provide[Container.redis_pool],
):
    @sio.on("connect")
    async def connect(sid, environ, auth):
        logger.info(f"Client attempting to connect: SID={sid}")
        async with redis_pool.get_redis() as redis_manager:
            try:
                token = auth.get("token")
                if not token:
                    logger.warning(f"Missing token for SID={sid}")
                    raise MissingToken

                logger.debug(f"Token retrieved for SID={sid}: {token}")

                # Проверка токена и получение пользователя
                current_user = await get_current_confirmed_user(
                    user_service=user_service, token=token
                )
                logger.info(
                    f"Authenticated user for SID={sid}: UserID={current_user.id}"
                )

                # Управление сессиями
                await redis_manager.sadd(f"user_sessions:{current_user.id}", sid)
                await redis_manager.set(f"sid:{sid}", current_user.id)
                username = (
                    f"{current_user.name} {current_user.surname}"
                    if current_user.surname
                    else current_user.name
                )
                await redis_manager.set(f"user_username:{current_user.id}", username)
                await sio.emit("connected", {"user": current_user.email}, room=sid)
                logger.info(
                    f"Client connected successfully: SID={sid}, UserID={current_user.id}"
                )
            except MissingToken:
                await handle_auth_error(sio, sid, "error.auth.token.required")
            except InvalidTokenFormat:
                await handle_auth_error(sio, sid, "error.auth.token.format.invalid")
            except AuthError:
                await handle_auth_error(sio, sid, "error.auth.token.invalid")
            except Exception as e:
                logger.error(
                    f"Unexpected error during connection: SID={sid}, Error={str(e)}"
                )
                await sio.disconnect(sid)

    @sio.on("disconnect")
    async def disconnect(sid):
        logger.info(f"Client attempting to disconnect: SID={sid}")
        async with redis_pool.get_redis() as redis_manager:
            try:
                user_id = await redis_manager.get(f"sid:{sid}")
                if user_id:
                    user_id = int(user_id.decode("utf-8"))
                    await redis_manager.srem(f"user_sessions:{user_id}", sid)
                    await redis_manager.delete(f"sid:{sid}")
                    logger.info(f"Session removed for UserID={user_id}, SID={sid}")
                else:
                    logger.info(f"No associated user found for SID={sid}")
            except Exception as e:
                logger.error(f"Error during disconnect: SID={sid}, Error={str(e)}")

        logger.info(f"Client disconnected: SID={sid}")


async def handle_auth_error(sio, sid, error_message):
    logger.warning(f"Authentication error for SID={sid}: {error_message}")
    await sio.emit("auth_error", {"message": error_message}, room=sid)
    await sio.disconnect(sid)
