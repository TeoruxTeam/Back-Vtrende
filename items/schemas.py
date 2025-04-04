from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from fastapi import Form
from pydantic import BaseModel, Field, HttpUrl, NonNegativeInt, model_validator

from core.schemas import CountSchema, StatusOkSchema
