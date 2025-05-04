import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

from .config import Settings
from .constants import API_PREFIX
from .database import SessionLocal
from .routes.auth import auth_router
from .routes.help_offers import help_offers
from .routes.help_requests import help_requests
from .routes.user import users_router

logger = logging.getLogger(__name__)


def create_fastapi(settings: Settings):
    """
    args:
        settings(Settings): Settings to be applied in the app.
    """

    app = FastAPI(title="Need a hand?")
    app.openapi_schema = None
    # Add routes.
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(users_router, prefix=API_PREFIX)
    app.include_router(help_requests, prefix=API_PREFIX)
    app.include_router(help_offers, prefix=API_PREFIX)

    # CORS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


def setup_engine(settings: Settings):
    """Created database engine based on config and configures sessionmaker."""

    kwargs = {
        # pool_pre_ping=True will enable the connection pool “pre-ping” feature
        # that tests connections for liveness upon each checkout.
        "pool_pre_ping": True,
        # The default pool size is 5, doubling the pool size to avoid QueuePool overflow error in case of concurrent API requests.
        # https://aspaara.atlassian.net/browse/MAT1-2553
        "pool_size": 10,
    }
    if settings.sqlalchemy_database_url.startswith("sqlite://"):
        kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(settings.sqlalchemy_database_url, **kwargs)

    # Configure sessionmaker to use the engine.
    SessionLocal.configure(bind=engine)

    return engine
