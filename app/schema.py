from typing import Literal
from pydantic import BaseModel, field_serializer, Field
from constants import (
    DAYS_MAP,
    REVERSE_DAYS_MAP,
    DAYS_OF_THE_WEEK,
    DAYS_OF_THE_WEEK_DB_VALUES,
)


class GardenTreeStatisticDaySchemaIn(BaseModel):
    """Модель для валидации входящих данных о количестве фруктов у дерева."""

    day_of_the_week: Literal[DAYS_OF_THE_WEEK]
    name: str = Field(..., min_length=1)
    fruits_num: int

    @field_serializer("day_of_the_week")
    def serialize_day_of_the_week(self, name: str, _info):
        return DAYS_MAP[name]


class GardenTreeStatisticDayUpdateSchema(BaseModel):
    """Модель для валидации данных о количестве фруктов у дерева при обновлении записей."""

    day_of_the_week: Literal[DAYS_OF_THE_WEEK_DB_VALUES] | None = None
    name: str | None = None
    fruits_num: int | None = None


class GardenTreeStatisticDaySchemaOut(BaseModel):
    """Модель для валидации исходящих данных о количестве фруктов у дерева."""

    id: int
    day_of_the_week: Literal[DAYS_OF_THE_WEEK_DB_VALUES]
    name: str = Field(..., min_length=1)
    fruits_num: int

    @field_serializer("day_of_the_week")
    def serialize_day_of_the_week(self, name: str, _info):
        return REVERSE_DAYS_MAP[name]
