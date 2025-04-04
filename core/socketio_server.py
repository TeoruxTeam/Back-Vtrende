import socketio
from pydantic import ValidationError

from core.environment import env


class CustomSocketServer(socketio.AsyncServer):
    def __init__(self, *args, **kwargs):
        kwargs["cors_allowed_origins"] = (
            env.allowed_origins
        )  # Используем разрешённые origins
        kwargs["cors_credentials"] = True  # Разрешить отправку credentials
        super().__init__(*args, **kwargs)

    async def emit_to_sessions(self, sids, event_name, data):
        """
        Метод для отправки сообщения на все сессии (sids).
        """
        for sid in sids:
            await self.emit(event_name, data, room=sid)

    def validate_request(self, data, schema_class):
        """
        Универсальная функция валидации данных с использованием переданного класса схемы.
        Возвращает схему при успехе или None в случае ошибки.
        """
        try:
            return schema_class(**data)
        except ValidationError:
            return None
