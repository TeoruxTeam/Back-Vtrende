from abc import ABC, abstractmethod

from core.utils import get_media_url
from ratings.services import IRatingService

from .schemas import GetSellerInfoResponseSchema, SellerInfo, UserDTO
from .services import IUserService


class IUserFacade(ABC):

    @abstractmethod
    async def get_seller_info(
        self, user_id: int, base_url: str
    ) -> GetSellerInfoResponseSchema:
        pass


class UserFacade(IUserFacade):

    def __init__(self, user_service: IUserService, rating_service: IRatingService):
        self.user_service = user_service
        self.rating_service = rating_service

    async def get_seller_info(
        self, user_id: int, base_url: str
    ) -> GetSellerInfoResponseSchema:
        user: UserDTO = await self.user_service.get_user_by_id(user_id, False)
        if user.avatar:
            user.avatar = get_media_url(base_url, user.avatar)
        rating = await self.rating_service.get_user_avg_rating(user_id)
        reviews_count = await self.rating_service.get_reviews_count(user_id)
        return GetSellerInfoResponseSchema(
            data=SellerInfo(
                id=user.id,
                username=user.name + " " + (user.surname or ""),
                rating=rating,
                reviews_count=reviews_count,
                avatar=user.avatar,
                phone_number=user.phone_number,
            )
        )
