from sqlalchemy import String, UniqueConstraint, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from database import sync_engine
from constants import DaysOfTheWeekEnum


class Base(DeclarativeBase):

    def to_dict(self):
        """Функция для представления атрибутов модели в виде словаря."""
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

class GardenTreeStaticDayModel(Base):
    """Модель для хранения записей о числе фруктов у дерева в определенный день недели."""
    __tablename__ = "garden_tree_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_of_the_week: Mapped[DaysOfTheWeekEnum]
    name: Mapped[str] = mapped_column(String(255))
    fruits_num: Mapped[int]

    __table_args__ = (UniqueConstraint("day_of_the_week", "name", name="unique_tree"),)


# В рамках тестового задания не расписываю миграции и при перезапуске, сбрасываю БД
Base.metadata.drop_all(sync_engine)
Base.metadata.create_all(sync_engine)
