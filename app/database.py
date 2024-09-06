from settings import settings
from sqlalchemy import create_engine

sync_engine = create_engine(url=settings.DB_URL, echo=True)
