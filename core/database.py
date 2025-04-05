from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Callable, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.logger import logger


class BaseModel(DeclarativeBase):
    pass


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(db_url, echo=True)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        )

    @asynccontextmanager
    async def session(self) -> Callable[..., AbstractAsyncContextManager[AsyncSession]]:
        # Генерация новой сессии для каждого запроса
        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


class UnitOfWork:
    def __init__(
        self, session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]]
    ):
        """
        :param session_factory: Фабрика для создания сессии базы данных
        """
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self.transaction = None  # Переменная для хранения состояния транзакции

    async def begin(self):
        """
        Метод для явного начала транзакции.
        """
        if self.session is None:
            # Генерируем сессию
            async with self.session_factory() as session:
                self.session = session
                # Начинаем транзакцию
                self.transaction = await self.session.begin()

    async def commit(self):
        """
        Коммит транзакции.
        """
        if self.session is None or self.transaction is None:
            raise RuntimeError("Session or transaction not initialized.")

        try:
            await self.session.commit()  # Выполняем commit транзакции
        except Exception as e:
            await self.session.rollback()  # При ошибке делаем rollback
            logger.error(f"Error during commit: {e}")
            raise RuntimeError(f"Failed to commit transaction: {e}") from e

    async def rollback(self):
        """
        Откат транзакции.
        """
        if self.session is None or self.transaction is None:
            raise RuntimeError("Session or transaction not initialized.")

        try:
            await self.session.rollback()  # Выполняем rollback транзакции
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            raise RuntimeError(f"Failed to rollback transaction: {e}") from e

    async def close(self):
        """
        Завершение работы сессии и транзакции.
        """
        if self.session is not None:
            try:
                await self.session.close()
            except Exception as e:
                logger.error(f"Error during session closing: {e}")
                raise RuntimeError(f"Failed to close session: {e}") from e
            finally:
                self.session = None
                self.transaction = None  # Очищаем транзакцию после завершения

    async def get_session(self) -> AsyncSession:
        """
        Возвращает текущую сессию для использования в репозиториях.
        """
        if self.session is None:
            raise RuntimeError("Session is not initialized or already closed.")
        return self.session


class UnitOfWorkFactory:
    def __init__(
        self, session_factory: Callable[..., AbstractAsyncContextManager[AsyncSession]]
    ):
        self.session_factory = session_factory

    def create(self) -> UnitOfWork:
        """Создаёт экземпляр UnitOfWork, используя session_factory"""
        return UnitOfWork(self.session_factory)
