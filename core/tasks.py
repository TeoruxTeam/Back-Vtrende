import asyncio

from celery import Task

from core.celery import app
from core.container import Container
from core.logger import logger


@app.task(bind=True, base=Task, name="send_notifications")
def send_notifications(self, notifications):
    async def main():
        try:
            notification_facade = Container().notification_facade()
            await notification_facade.make_notifications(notifications)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений: {e}")

    asyncio.run(main())
