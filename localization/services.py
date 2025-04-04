import json
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from babel.messages import pofile
from babel.messages.catalog import Catalog
from babel.messages.pofile import write_po
from babel.support import Translations
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.environment import env

from .repositories import ILocalizationKeyRepository, ILocalizationRepository
from .schemas import LocalizationFromORM, LocalizationKeyFromORM


class ILocalizationKeyService(ABC):

    @abstractmethod
    async def get_by_key_or_create(self, key: str, session: Optional[AsyncSession]):
        pass

    @abstractmethod
    async def get_by_key(self, key: str):
        pass

    @abstractmethod
    async def create(
        self, key: str, session: Optional[AsyncSession]
    ) -> LocalizationKeyFromORM:
        pass

    @abstractmethod
    async def update_by_id(self, id: int, key: str):
        pass

    @abstractmethod
    async def delete(self, id: int, session: Optional[AsyncSession]):
        pass

    @abstractmethod
    async def get_all(
        self, limit: int, offset: int
    ) -> Tuple[LocalizationKeyFromORM, int]:
        pass


class LocalizationKeyService(ILocalizationKeyService):

    def __init__(self, repo: ILocalizationKeyRepository):
        self.repo = repo

    async def get_by_key_or_create(
        self, key: str, session: Optional[AsyncSession] = None
    ):
        result = await self.get_by_key(key)
        if result:
            return result
        return await self.create(key, session)

    async def get_by_key(self, key: str):
        return await self.repo.get_by_key(key)

    async def create(
        self, key: str, session: Optional[AsyncSession] = None
    ) -> LocalizationKeyFromORM:
        return await self.repo.create(key, session)

    async def update_by_id(self, id: int, key: str):
        return await self.repo.update_by_id(id, key)

    async def delete(self, id: int, session: Optional[AsyncSession]):
        return await self.repo.delete_by_id(id, session)

    async def get_all(
        self, limit: int, offset: int
    ) -> Tuple[LocalizationKeyFromORM, int]:
        return await self.repo.get_all(limit, offset)


class ILocalizationService(ABC):

    @abstractmethod
    async def get_all_translations(self, language: str) -> dict:
        """
        Returning all translations for selected language
        """
        pass

    @abstractmethod
    async def get_values_by_key_id(self, key_id: int) -> List[LocalizationFromORM]:
        pass

    @abstractmethod
    async def create(
        self, key_id: int, language: str, value: str
    ) -> LocalizationFromORM:
        pass

    @abstractmethod
    async def update_by_id(self, id: int, value: str) -> LocalizationFromORM:
        pass

    @abstractmethod
    async def delete_by_id(self, id: int):
        pass

    @abstractmethod
    async def upload_locale_file(self, locale: str, file: UploadFile) -> None:
        pass


class LocalizationService(ILocalizationService):

    def __init__(self, repo: ILocalizationRepository):
        self.repo = repo
        self.locales_dir = Path(env.locales_dir)

    async def get_values_by_key_id(self, key_id: int):
        return await self.repo.get_values_by_key_id(key_id)

    async def create(
        self, key_id: int, language: str, value: str
    ) -> LocalizationFromORM:
        return await self.repo.create(key_id, language, value)

    async def update_by_id(self, id: int, value: str) -> LocalizationFromORM:
        return await self.repo.update_language_value_by_id(id, value)

    async def delete_by_id(self, id: int):
        return await self.repo.delete_by_id(id)

    # locales

    def _convert_text_to_po(self, locale: str, lines: list) -> str:
        catalog = Catalog(locale=locale)

        for line in lines:
            # Пропускаем пустые строки и комментарии (например, строки с #)
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Разделяем строку на msgid и msgstr
            try:
                msgid, msgstr = line.split("=", 1)
                catalog.add(msgid.strip(), msgstr.strip())
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="error.locale.invalid_format"
                )

        po_file_path = os.path.join(
            self.locales_dir, locale, "LC_MESSAGES", "messages.po"
        )
        os.makedirs(os.path.dirname(po_file_path), exist_ok=True)

        with open(po_file_path, "wb") as po_file:
            write_po(po_file, catalog)

        return po_file_path

    def _compile_po_to_mo(self, po_file_path: str) -> None:
        mo_file_path = po_file_path.replace(".po", ".mo")

        # Компиляция .po файла в .mo
        os.system(f"msgfmt {po_file_path} -o {mo_file_path}")

    @lru_cache(maxsize=128)
    async def get_all_translations(self, language: str) -> dict:
        """
        Возвращает все переводы для указанного языка из базы данных.
        """
        translation_path = self.locales_dir / language / "LC_MESSAGES" / "messages.mo"
        if not translation_path.exists():
            translation_path = self.locales_dir / "en" / "LC_MESSAGES" / "messages.mo"

        with translation_path.open("rb") as f:
            translations = Translations(f)

        return {
            msgid: translations.gettext(msgid) for msgid in translations._catalog.keys()
        }

    async def upload_locale_file(self, locale: str, file: UploadFile) -> None:
        if not file.filename.endswith(".txt"):
            raise HTTPException(status_code=400, detail="error.locale.not_text_file")

        content = await file.read()
        lines = content.decode("utf-8").splitlines()

        # Конвертация строкового файла в .po файл
        po_file_path = self._convert_text_to_po(locale, lines)

        # Компиляция в .mo файл
        self._compile_po_to_mo(po_file_path)
        self.get_all_translations.cache_clear()
