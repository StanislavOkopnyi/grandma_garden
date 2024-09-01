from enum import Enum


class DaysOfTheWeekEnum(Enum):
    monday = "mn"
    tuesday = "ts"
    wendsday = "wn"
    thursday = "th"
    friday = "fr"
    saturday = "st"
    sunday = "sn"


DAYS_MAP = {
    "Понедельник": DaysOfTheWeekEnum.monday,
    "Вторник": DaysOfTheWeekEnum.tuesday,
    "Среда": DaysOfTheWeekEnum.wendsday,
    "Четверг": DaysOfTheWeekEnum.thursday,
    "Пятница": DaysOfTheWeekEnum.friday,
    "Суббота": DaysOfTheWeekEnum.saturday,
    "Воскресенье": DaysOfTheWeekEnum.sunday,
}

REVERSE_DAYS_MAP = {y: x for x, y in DAYS_MAP.items()}

DAYS_OF_THE_WEEK = tuple(DAYS_MAP.keys())
DAYS_OF_THE_WEEK_DB_VALUES = tuple(REVERSE_DAYS_MAP.keys())
