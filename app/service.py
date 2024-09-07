from datetime import datetime
from typing import Any

import requests
from constants import DAYS_OF_THE_WEEK_ISO_MAP
from database import sync_engine
from models import Base, GardenTreeStaticDayModel
from pydantic import BaseModel, ValidationError
from schema import (
    GardenTreeStatisticDaySchemaIn,
    GardenTreeStatisticDaySchemaOut,
    GardenTreeStatisticDayUpdateSchema,
)
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text


class ValidationService:
    """Сервис для валидации словарей при помощи моделей Pydantic."""

    def __init__(self, pydantic_class: type[BaseModel]):
        self.pydantic_class = pydantic_class

    def __call__(self, *args, **kwargs) -> BaseModel | None:
        return self.pydantic_class(**kwargs)


class DatabaseRepository:
    """Репозиторий для взаимодействия с базой данных."""

    def __init__(self, engine: Engine, db_table: type[Base]):
        self.engine = engine
        self.db_table = db_table

    def create(self, *args, **kwargs) -> None:
        with Session(self.engine) as session:
            model_to_create = self.db_table(**kwargs)
            session.add(model_to_create)
            session.commit()

    def update(self, filter_by_args: dict | None = None, *args, **kwargs) -> None:
        with Session(self.engine) as session:
            filter_by_args = filter_by_args if isinstance(filter_by_args, dict) else {}
            session.query(self.db_table).filter_by(**filter_by_args).update(kwargs)
            session.commit()

    def delete(self, filter_by_args: dict | None = None, *args, **kwargs) -> None:
        with Session(self.engine) as session:
            filter_by_args = filter_by_args if isinstance(filter_by_args, dict) else {}
            session.query(self.db_table).filter_by(**filter_by_args).delete()
            session.commit()

    def get_all(self, *args, **kwargs):
        with Session(self.engine) as session:
            order_by = kwargs.get("order_by")
            models = session.scalars(select(self.db_table).order_by(text(order_by if order_by else "id"))).all()
        return models


class ServiceError(Exception):
    """Исключение, вызываемое при неправильной работе сервисов по созданию записей."""

    def __init__(self, *args: object, **kwargs) -> None:
        super().__init__(*args)
        self.message = kwargs.get("message")


class CreateRecordService:
    """Сервис по созданию записей."""

    def __init__(self, validation_service: ValidationService, repository: DatabaseRepository):
        self.validation_service = validation_service
        self.repository = repository

    def __call__(self, *args, **kwargs):
        try:
            validated_data = self.validation_service(**kwargs, strict=True)
        except ValidationError as err:
            raise ServiceError(message="Ошибка в вводимых данных") from err
        try:
            self.repository.create(**validated_data.model_dump())
        except IntegrityError as err:
            raise ServiceError(message="Запись на данный день недели с этим деревом уже существует") from err


class UpdateRecordService:
    """Сервис по обновлению записей."""

    def __init__(self, validation_service: ValidationService, repository: DatabaseRepository):
        self.validation_service = validation_service
        self.repository = repository

    def __call__(self, filter_by_args: dict | None = None, *args, **kwargs):
        try:
            update_kwargs = self.validation_service(**kwargs).model_dump(exclude_none=True)
        except ValidationError as err:
            raise ServiceError(message="Ошибка в вводимых данных") from err
        try:
            self.repository.update(filter_by_args=filter_by_args, **update_kwargs)
        except IntegrityError as err:
            raise ServiceError(message="Запись на данный день недели с этим деревом уже существует") from err


class DeleteRecordService:
    """Сервис по удалению записей."""

    def __init__(self, repository: DatabaseRepository):
        self.repository = repository

    def __call__(self, filter_by_args: dict | None = None, *args, **kwargs):
        try:
            self.repository.delete(filter_by_args=filter_by_args)
        except Exception as err:
            raise ServiceError(message="Ошибка при удалении") from err


class RequestsGetWeekWeather:
    """Сервис по получению погоды за прошлую неделю."""

    API_URL = r"https://api.open-meteo.com/v1/forecast?latitude=55.7522&longitude=37.6156&daily=temperature_2m_max&timezone=Europe%2FMoscow&past_days=7&forecast_days=1"

    def __call__(self, *args: Any, **kwargs: Any) -> dict[str, int]:
        data = requests.get(self.API_URL).json()
        return self._get_weather(data=data)

    def _get_weather(self, data: dict) -> dict[str, int]:
        """Обрабатываем json от API, возвращаем словарь
        с днем недели в качестве ключа, температурой в качестве значения.
        """
        # В рамках тестового не провожу дополнительной валидации
        days: list[str] = data.get("daily", {}).get("time", [])
        days_temperature: list[str] = data.get("daily", {}).get("temperature_2m_max", [])

        week_weather = {}
        for day, day_temperature in zip(days, days_temperature):
            day_iso_value: int = datetime.fromisoformat(day).isoweekday()
            weekday_name = DAYS_OF_THE_WEEK_ISO_MAP[day_iso_value]
            week_weather[weekday_name] = float(day_temperature)

        return week_weather


class GetAllRecordsService:
    """Сервис по получению всех записей."""

    def __init__(
        self,
        repository: DatabaseRepository,
        validation_service: ValidationService,
        weather_service: RequestsGetWeekWeather,
    ):
        self.repository = repository
        self.validation_service = validation_service
        # Получение словарь с днем недели к температуре
        # Загружаю один раз при запуске приложения
        self.weather_dict = weather_service()

    def __call__(self, order_by: str | None = None) -> list[dict]:
        result = []
        for model in self.repository.get_all(order_by=order_by):
            validated_data: dict = self.validation_service(**model.to_dict(), strict=True).model_dump()

            # Получаем температуру к дню недели
            day_of_the_week = validated_data["day_of_the_week"]
            temperature = self.weather_dict[day_of_the_week]
            validated_data["temperature"] = temperature

            result.append(validated_data)
        return result


garden_tree_validation_service_in = ValidationService(pydantic_class=GardenTreeStatisticDaySchemaIn)
garden_tree_validation_service_out = ValidationService(pydantic_class=GardenTreeStatisticDaySchemaOut)
garden_tree_validation_service_update = ValidationService(pydantic_class=GardenTreeStatisticDayUpdateSchema)
garden_tree_repository = DatabaseRepository(engine=sync_engine, db_table=GardenTreeStaticDayModel)

create_garden_tree_record = CreateRecordService(
    validation_service=garden_tree_validation_service_in,
    repository=garden_tree_repository,
)
update_garden_tree_record = UpdateRecordService(
    validation_service=garden_tree_validation_service_update,
    repository=garden_tree_repository,
)
delete_garden_tree_record = DeleteRecordService(repository=garden_tree_repository)

weather_service = RequestsGetWeekWeather()
get_all_garden_records = GetAllRecordsService(
    repository=garden_tree_repository,
    validation_service=garden_tree_validation_service_out,
    weather_service=weather_service,
)
