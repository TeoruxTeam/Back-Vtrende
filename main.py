from typing import List

import firebase_admin
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from accounts.router import router as account_router
from admin.router import router as admin_router
from auth.router import router as auth_router
from categories.router import router as categories_router
from chats.router import router as chats_router
from core.celery import app as celery_app
from core.container import Container
from core.environment import env
from core.middlewares import RequestCountMiddleware, TrailingSlashMiddleware
from items.router import router as listing_router
from localization.router import router as localization_router
from notifications.router import router as notifications_router
from payments.router import router as payments_router
from promotions.router import router as promotion_router
from sockets.setup_sockets import setup_sockets
from users.router import router as user_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=env.secret_key)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(account_router)
app.include_router(listing_router)
app.include_router(categories_router)
app.include_router(chats_router)
app.include_router(localization_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(promotion_router)
app.include_router(payments_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=env.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

firebase_cred = firebase_admin.credentials.Certificate(env.firebase_credentials_path)
firebase_admin.initialize_app(firebase_cred)


container = Container()
container.init_resources()
container.wire(modules=[__name__])

app.add_middleware(RequestCountMiddleware, redis_pool=container.redis_pool())

setup_sockets(container)

socketio_app = container.socketio_app()

app.mount("/", socketio_app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {"non_field_error": []}
    for error in exc.errors():
        field_path = ".".join(
            str(x) for x in error["loc"] if not isinstance(x, int) and x != "body"
        )
        error_key = (
            "error.validation."
            + error["type"]
            + ("." + field_path if field_path else "")
        )
        if not field_path or any(isinstance(x, int) for x in error["loc"]):
            errors["non_field_error"].append(error_key)
        else:
            errors[field_path] = error_key
    return JSONResponse(status_code=400, content={"errors": errors, "status": "error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.detail, "status": "error"}
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 500:
        return JSONResponse(
            status_code=500,
            content={"error": "error.server.internal_error", "status": "error"},
        )

    return await http_exception_handler(request, exc)
