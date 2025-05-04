from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from .models import Base

# The engine is configured by .factory:setup_engine().
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False)
DB_COMMIT_CHUNKS = 10000


class DBSessionContext:
    """Context manager for database session.

    This simply wraps `SessionLocal`, but includes type hints.

    """

    _db_session: Session

    def __init__(self) -> None:
        self._db_session = SessionLocal()

    def __enter__(self) -> Session:
        return self._db_session

    def __exit__(self, type, value, traceback) -> None:
        self._db_session.close()


def create_tables(engine):
    Base.metadata.create_all(bind=engine)


def drop_tables(engine):
    meta = MetaData()
    meta.reflect(bind=engine)
    meta.drop_all(bind=engine)
