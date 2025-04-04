from core.container import Container
from core.socketio_server import CustomSocketServer

from .auth import setup_auth_handlers
from .chats import setup_chat_handlers
from .notifications import setup_notification_handlers


def setup_sockets(container: Container):
    sio = container.socketio_server()
    setup_auth_handlers(sio)
    setup_chat_handlers(sio)
    setup_notification_handlers(sio)
