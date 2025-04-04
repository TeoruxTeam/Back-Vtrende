from abc import ABC, abstractmethod
from .schemas import ActivityStatsSchema, DailyActivityStatsSchema, HourlyActivityStatsSchema
from .repositories import IStatsRepository


class IStatsService(ABC):

    @abstractmethod
    async def add_activity_stats(self, schema: ActivityStatsSchema):
        pass

    @abstractmethod
    async def get_activity_hours(self, limit: int, offset: int) -> ActivityStatsSchema:
        pass

    @abstractmethod
    async def get_activity_days(self, limit: int, offset: int) -> ActivityStatsSchema:
        pass


class StatsService(IStatsService):
    def __init__(self, repo: IStatsRepository):
        self.repo = repo

    async def add_activity_stats(self, schema: ActivityStatsSchema):
        return await self.repo.add_activity_stats(schema)
    
    async def get_activity_hours(self, limit: int, offset: int) -> HourlyActivityStatsSchema:
        return await self.repo.get_activity_stats_grouped_by_hour(limit, offset)

    async def get_activity_days(self, limit: int, offset: int) -> DailyActivityStatsSchema:
        return await self.repo.get_activity_stats_grouped_by_day(limit, offset)