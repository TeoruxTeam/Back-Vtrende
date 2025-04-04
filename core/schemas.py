from pydantic import BaseModel


class StatusOkSchema(BaseModel):
    status: str = "ok"


class CountSchema(BaseModel):
    count: int
