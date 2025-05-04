import re

from passlib.context import CryptContext
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import nullsfirst
from sqlalchemy import nullslast
from sqlalchemy import or_

from ..models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def is_user_authenticated(password: str, user: User = None):
    if (
        user
        and user.password_hash
        and len(user.password_hash.strip()) != 0
        and verify_password(password, user.password_hash)
    ):
        return True
    return False


def change_case(value: str):
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def apply_search(db_query, model, fields, search):
    terms = [term.strip().lower() for term in search.split() if term.strip()]
    if not terms:
        return db_query

    filters = []
    for term in terms:
        term_filter = or_(
            *[getattr(model, field).ilike(f"%{term}%") for field in fields]
        )
        filters.append(term_filter)

    return db_query.filter(*filters)


def apply_filters(model, db_query, query):
    filters = []
    for key, value in query.items():
        filters.append(getattr(model, key) == value)
    return db_query.filter(*filters)


def apply_sorting(model, db_query, sorting, columns):
    ordering = []
    default_order = desc(
        func.coalesce(getattr(model, "updated_at"), getattr(model, "created_at"))
    )
    for column_name, order in sorting.items():
        if column_name not in columns:
            pass
        column = getattr(model, column_name)
        if order == "asc":
            ordering.append(nullsfirst(column.asc()))
        else:
            default_order = asc(
                func.coalesce(
                    getattr(model, "updated_at"), getattr(model, "created_at")
                )
            )
            ordering.append(nullslast(column.desc()))

    return db_query.order_by(*ordering, default_order) if ordering else db_query
