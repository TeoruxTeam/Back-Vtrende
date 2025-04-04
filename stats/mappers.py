from .models import ActivityStats
from .schemas import ActivityStatsSchema, HourlyActivityStatsSchema, DailyActivityStatsSchema
from typing import List


class ActivityStatsMapper:

    @staticmethod
    def to_entity(schema: ActivityStatsSchema) -> ActivityStats:
        return ActivityStats(
            count=schema.count,
            start_date=schema.start_date,
            end_date=schema.end_date
        )
    
    @staticmethod
    def to_schema(entity: ActivityStats) -> ActivityStatsSchema:
        return ActivityStatsSchema(
            count=entity.count,
            start_date=entity.start_date,
            end_date=entity.end_date
        )
    
    @staticmethod
    def to_schema_list(entities: List[ActivityStats]) -> List[ActivityStatsSchema]:
        return [ActivityStatsMapper.to_schema(entity) for entity in entities]
    
    @staticmethod
    def to_aggregated_hourly_schema_list(rows: List) -> List[HourlyActivityStatsSchema]:
        return [
            HourlyActivityStatsSchema(
                hour=row.hour,
                total_count=row.total_count,
                first_start_date=row.first_start_date,
                last_end_date=row.last_end_date
            )
            for row in rows
        ]
    
    @staticmethod
    def to_aggregated_daily_schema_list(rows: List) -> List[DailyActivityStatsSchema]:
        return [
            DailyActivityStatsSchema(
                day=row.day,
                total_count=row.total_count,
                first_start_date=row.first_start_date,
                last_end_date=row.last_end_date
            )
            for row in rows
        ]