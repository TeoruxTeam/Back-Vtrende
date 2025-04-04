from pydantic import BaseModel
from datetime import datetime


class ActivityStatsSchema(BaseModel):
    count: int
    start_date: datetime
    end_date: datetime


class HourlyActivityStatsSchema(BaseModel):
    hour: datetime
    total_count: int
    first_start_date: datetime
    last_end_date: datetime


class DailyActivityStatsSchema(BaseModel):
    day: datetime
    total_count: int
    first_start_date: datetime
    last_end_date: datetime