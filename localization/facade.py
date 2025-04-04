from abc import ABC, abstractmethod

from .services import ILocalizationKeyService, ILocalizationService


class ILocalizationFacade(ABC):

    @abstractmethod
    async def translate(self, language: str, key: str):
        pass

    @abstractmethod
    async def get_translation(self, language: str):
        pass


class LocalizationFacade(ILocalizationFacade):

    def __init__(
        self,
        localization_service: ILocalizationService,
        localization_key_service: ILocalizationKeyService,
    ):
        self.localization_service = localization_service
        self.localization_key_service = localization_key_service

    async def translate(self, language: str, key: str):
        translations = await self.localization_service.get_all_translations(language)
        return translations.get(key, key)

    async def get_translation(self, language: str):
        return await self.localization_service.get_all_translations(language)
