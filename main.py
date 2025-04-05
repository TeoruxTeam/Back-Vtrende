import firebase_admin
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from accounts.router import router as account_router
from auth.router import router as auth_router
from core.container import Container
from core.environment import env
from users.router import router as user_router
from favorites.router import router as favorite_router
from items.router import router as item_router
from orders.router import router as order_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(account_router)
app.include_router(favorite_router)
app.include_router(item_router)
app.include_router(order_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=env.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


container = Container()
container.init_resources()
container.wire(modules=[__name__])


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
