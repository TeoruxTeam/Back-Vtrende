from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import Date, cast, func
from sqlalchemy.future import select

from core.repositories import BaseRepository

from .mappers import ActivityStatsMapper
from .models import ActivityStats
from .schemas import (
    ActivityStatsSchema,
    DailyActivityStatsSchema,
    HourlyActivityStatsSchema,
)


class IStatsRepository(ABC):

    @abstractmethod
    async def get_activity_stats_grouped_by_hour(
        self, limit: int, offset: int
    ) -> List[HourlyActivityStatsSchema]:
        pass

    @abstractmethod
    async def get_activity_stats_grouped_by_day(
        self, limit: int, offset: int
    ) -> List[DailyActivityStatsSchema]:
        pass

    @abstractmethod
    async def add_activity_stats(self, schema: ActivityStatsSchema) -> None:
        pass


class StatsRepository(IStatsRepository, BaseRepository):

    async def get_activity_stats_grouped_by_hour(self, limit: int, offset: int):
        async with self.get_session() as session:
            hour_truncated = func.date_trunc("hour", ActivityStats.start_date).label(
                "hour"
            )

            query = (
                select(
                    hour_truncated,
                    func.sum(ActivityStats.count).label("total_count"),
                    func.min(ActivityStats.start_date).label("first_start_date"),
                    func.max(ActivityStats.end_date).label("last_end_date"),
                )
                .group_by(hour_truncated)  # Group by the truncated hour explicitly
                .order_by(hour_truncated)  # Order by the truncated hour
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(query)
            grouped_activities = result.all()

            return ActivityStatsMapper.to_aggregated_hourly_schema_list(
                grouped_activities
            )

    async def add_activity_stats(self, schema: ActivityStatsSchema) -> None:

        async with self.get_session() as session:
            entity = ActivityStatsMapper.to_entity(schema)
            session.add(entity)
            await session.commit()

    async def get_activity_stats_grouped_by_day(self, limit: int, offset: int):
        async with self.get_session() as session:
            day_truncated = func.date_trunc("day", ActivityStats.start_date).label(
                "day"
            )

            query = (
                select(
                    day_truncated,
                    func.sum(ActivityStats.count).label("total_count"),
                    func.min(ActivityStats.start_date).label("first_start_date"),
                    func.max(ActivityStats.end_date).label("last_end_date"),
                )
                .group_by(day_truncated)
                .order_by(day_truncated)
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(query)
            grouped_activities = result.all()

            return ActivityStatsMapper.to_aggregated_daily_schema_list(
                grouped_activities
            )
