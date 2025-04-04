from abc import ABC, abstractmethod
from typing import Optional

from .services import ICategoryViewService, ISubcategoryViewService


class IRecommendationFacade(ABC):

    @abstractmethod
    async def add_user_interest_statistics(
        self, user_id: int, category_id: Optional[int], subcategory_id: Optional[int]
    ) -> None:
        pass


class RecommendationFacade(IRecommendationFacade):

    def __init__(
        self,
        category_view_service: ICategoryViewService,
        subcategory_view_service: ISubcategoryViewService,
    ):
        self.category_view_service = category_view_service
        self.subcategory_view_service = subcategory_view_service

    async def add_user_interest_statistics(
        self, user_id: int, category_id: Optional[int], subcategory_id: Optional[int]
    ) -> None:

        if category_id:
            await self.category_view_service.create_or_increment_views(
                user_id, category_id
            )

        if subcategory_id:
            await self.subcategory_view_service.create_or_increment_views(
                user_id, subcategory_id
            )
