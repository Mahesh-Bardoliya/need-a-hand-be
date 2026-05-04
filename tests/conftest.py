import os
import shutil

import pytest
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import need_a_hand_be.models
from need_a_hand_be.config import Settings
from need_a_hand_be.database import Base
from need_a_hand_be.database import SessionLocal
from need_a_hand_be.dependencies import get_db_session
from need_a_hand_be.dependencies import get_settings
from need_a_hand_be.factory import create_fastapi


# Create a settings override for testing
def get_settings_override():
    # Ensure var directory exists for test database
    os.makedirs("var", exist_ok=True)
    return Settings(
        sqlalchemy_database_url="sqlite:///./var/test.db",
        secret_key="testsecret",
        jwt_algorithm="HS256",
        access_token_expire_minutes=30,
        cors_allow_origins=["*"],
    )


settings_override = get_settings_override()

# Setup test engine
engine = create_engine(
    settings_override.sqlalchemy_database_url,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def manage_test_db():
    # Setup: Ensure fresh DB file
    db_file = "var/test.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield
    # Teardown: Clean up DB file after all tests
    engine.dispose()
    if os.path.exists(db_file):
        os.remove(db_file)


def override_get_db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = create_fastapi(settings_override)
app.dependency_overrides[get_settings] = get_settings_override
app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture(autouse=True)
def setup_database():
    # Recreate tables for every test to ensure isolation
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
