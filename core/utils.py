import hashlib
import time
from datetime import datetime
from urllib.parse import urljoin

from fastapi import Request


def generate_hashed_filename(filename: str) -> str:
    unique_data = f"{filename}_{time.time()}"

    hash_object = hashlib.sha256(unique_data.encode())
    hashed_filename = hash_object.hexdigest()

    ext = filename.split(".")[-1] if "." in filename else ""
    if ext:
        return f"{hashed_filename}.{ext}"
    return hashed_filename


def get_media_url(base_url, path: str) -> str:
    full_url = urljoin(str(base_url), f"{path}")  # Формируем полный URL для файла
    return full_url


async def get_language_from_cookies(request: Request) -> str:
    return request.cookies.get("language", "en")


def serialize_datetime(data: dict) -> dict:
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data
