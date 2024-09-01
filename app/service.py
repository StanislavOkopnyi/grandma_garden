from sqlalchemy.orm import Session
from schema import (
    GardenTreeStatisticDaySchemaIn,
    GardenTreeStatisticDaySchemaOut,
    GardenTreeStatisticDayUpdateSchema,
)
from models import GardenTreeStaticDayModel, Base
from pydantic import BaseModel, ValidationError
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from database import sync_engine


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
            validated_data = self.validation_service(**kwargs)
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
            validated_data = self.validation_service(**kwargs)
        except ValidationError as err:
            raise ServiceError(message="Ошибка в вводимых данных") from err
        try:
            # Убираем ключи, которые ссылаются на None
            update_kwargs = {x: y for x, y in validated_data.model_dump().items() if y is not None}
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


class GetAllRecordsService:
    """Сервис по получению всех записей."""

    def __init__(self, repository: DatabaseRepository, validation_service: ValidationService):
        self.repository = repository
        self.validation_service = validation_service

    def __call__(self, order_by: str | None = None) -> list[dict]:
        result = []
        for model in self.repository.get_all(order_by=order_by):
            validated_data = self.validation_service(**model.to_dict())
            result.append(validated_data.model_dump())
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
get_all_garden_records = GetAllRecordsService(
    repository=garden_tree_repository,
    validation_service=garden_tree_validation_service_out,
)
