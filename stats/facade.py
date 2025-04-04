from abc import ABC, abstractmethod

from admin.schemas import (
    DaysActivityResponse,
    DefaultStatsResponse,
    HoursActivityResponse,
)
from listings.services import IListingService
from stats.services import IStatsService
from users.services import IUserService

from .schemas import DailyActivityStatsSchema, HourlyActivityStatsSchema


class IStatsFacade(ABC):

    @abstractmethod
    async def get_total_users_count(self) -> int:
        pass

    @abstractmethod
    async def get_active_listings_total(self) -> int:
        pass

    @abstractmethod
    async def get_active_listings_month(self) -> int:
        pass

    @abstractmethod
    async def get_activity_hours(self, limit: int, offset: int) -> int:
        pass

    @abstractmethod
    async def get_activity_days(self, limit: int, offset: int) -> int:
        pass

    @abstractmethod
    async def get_new_users_month(self) -> int:
        pass

    @abstractmethod
    async def get_new_users_count(self) -> int:
        pass

    @abstractmethod
    async def get_refused_listings_count(self) -> int:
        pass


class StatsFacade(IStatsFacade):

    def __init__(
        self,
        user_service: IUserService,
        listing_service: IListingService,
        stats_service: IStatsService,
    ):
        self.user_service = user_service
        self.listing_service = listing_service
        self.stats_service = stats_service

    async def get_total_users_count(self) -> int:
        count = await self.user_service.get_total_users_count()
        return DefaultStatsResponse(data={"count": count})

    async def get_active_listings_total(self) -> int:
        count = await self.listing_service.get_total_active_listings_count()
        return DefaultStatsResponse(data={"count": count})

    async def get_active_listings_month(self) -> int:
        count = await self.listing_service.get_active_listings_month_count()
        return DefaultStatsResponse(data={"count": count})

    async def get_activity_hours(
        self, limit: int, offset: int
    ) -> HoursActivityResponse:
        activity_hour_stats = await self.stats_service.get_activity_hours(limit, offset)
        return HoursActivityResponse(data=activity_hour_stats)

    async def get_activity_days(self, limit: int, offset: int) -> DaysActivityResponse:
        activity_daily_stats = await self.stats_service.get_activity_days(limit, offset)
        return DaysActivityResponse(data=activity_daily_stats)

    async def get_new_users_month(self) -> int:
        count = await self.user_service.get_new_users_month()
        return DefaultStatsResponse(data={"count": count})

    async def get_new_users_count(self) -> int:
        count = await self.user_service.get_new_users_day()
        return DefaultStatsResponse(data={"count": count})

    async def get_refused_listings_count(self) -> int:
        count = await self.listing_service.get_refused_listings_count()
        return DefaultStatsResponse(data={"count": count})
