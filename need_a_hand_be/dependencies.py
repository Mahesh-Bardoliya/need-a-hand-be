from contextlib import asynccontextmanager
from functools import lru_cache

from .config import settings
from .database import SessionLocal


@lru_cache()
def get_settings():
    return settings


# Dependency: Get DB Session
@asynccontextmanager
async def get_db():
    db = SessionLocal()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
