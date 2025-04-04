from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger


class BaseRepository:
    def __init__(self, session_factory):
        """Инициализация с фабрикой сессий."""
        self.session_factory = session_factory

    @asynccontextmanager
    async def get_session(self, session: AsyncSession = None):
        """Контекстный менеджер для работы с сессией."""
        if session:
            logger.info("Using existing session")
            yield session
        else:
            async with self.session_factory() as new_session:
                yield new_session
