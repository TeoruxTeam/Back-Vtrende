from pydantic import BaseModel


class LocalizationFromORM(BaseModel):
    id: int
    localization_key_id: int
    language: str
    value: str


class LocalizationKeyFromORM(BaseModel):
    id: int
    key: str
