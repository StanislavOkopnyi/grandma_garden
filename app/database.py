from sqlalchemy import create_engine
from settings import settings

sync_engine = create_engine(url=settings.DB_URL, echo=True)
