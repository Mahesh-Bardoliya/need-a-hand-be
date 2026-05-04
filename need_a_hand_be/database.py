from sqlalchemy import MetaData
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import with_loader_criteria
from sqlalchemy.orm.session import Session

from .models import Base
from .models import SoftDeleteMixin

# The engine is configured by .factory:setup_engine().
SessionLocal = sessionmaker(class_=Session, autocommit=False, autoflush=False)
DB_COMMIT_CHUNKS = 10000


@event.listens_for(Session, "do_orm_execute")
def _add_filtering_criteria(execute_state):
    if (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
    ):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )


from .models import UserStampMixin


@event.listens_for(Session, "before_flush")
def receive_before_flush(session, flush_context, instances):
    from .dependencies import current_user_id_var

    user_id = current_user_id_var.get()
    if not user_id:
        return
    for obj in session.new:
        if isinstance(obj, UserStampMixin):
            if not obj.created_by_user_id:
                obj.created_by_user_id = user_id
            if not obj.updated_by_user_id:
                obj.updated_by_user_id = user_id
    for obj in session.dirty:
        if isinstance(obj, UserStampMixin):
            if session.is_modified(obj, include_collections=False):
                obj.updated_by_user_id = user_id


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
