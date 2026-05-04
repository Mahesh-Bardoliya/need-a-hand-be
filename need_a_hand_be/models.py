import uuid

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import coalesce

SQL_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=SQL_NAMING_CONVENTION)

Base = declarative_base(metadata=metadata)


# =======================
# Common Mixins
# =======================
class TimestampMixin(object):
    """Adds created_at and updated_at with server default."""

    created_at = Column(
        DateTime(timezone=False), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin(object):
    """Adds deleted_at for soft delete (not managed by DB)."""

    deleted_at = Column(DateTime, nullable=True)


class IdMixin(object):
    """Adds deleted_at for soft delete (not managed by DB)."""

    id = Column(
        Integer, primary_key=True, unique=True, nullable=False, autoincrement=True
    )
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)


class UserStampMixin(object):
    """Automatic columns for user stamps."""

    @declared_attr
    def created_by_user_id(cls):
        return Column(
            "created_by_user_id",
            ForeignKey("users.id", ondelete="SET NULL"),
            index=True,
            # TODO Set automatically.
            # default=lambda: getattr(current_user, "id", None),
        )

    @declared_attr
    def created_by_user(cls):
        backref_remote_side = None
        # This is self-referential for users, so remote_side needs to be specified
        # explicitly.
        if cls.__tablename__ == "users":
            backref_remote_side = "User.id"
        return relationship(
            "User",
            foreign_keys=[cls.created_by_user_id],
            backref=backref(
                "created_%s" % cls.__tablename__, remote_side=backref_remote_side
            ),
        )

    @declared_attr
    def updated_by_user_id(cls):
        return Column(
            "updated_by_user_id",
            ForeignKey("users.id", ondelete="SET NULL"),
            default=None,
            index=True,
            # TODO Set automatically.
            # onupdate=lambda: getattr(current_user, "id", None),
        )

    @declared_attr
    def updated_by_user(cls):
        backref_remote_side = None
        # This is self-referential for users, so remote_side needs to be specified
        # explicitly.
        if cls.__tablename__ == "users":
            backref_remote_side = "User.id"
        return relationship(
            "User",
            foreign_keys=[cls.updated_by_user_id],
            backref=backref(
                "updated_%s" % cls.__tablename__, remote_side=backref_remote_side
            ),
        )

    @hybrid_property
    def last_updated_at(self):
        return self.updated_at if self.updated_at else self.created_at

    @last_updated_at.expression
    def last_updated_at(cls):
        # https://docs.sqlalchemy.org/en/14/core/tutorial.html
        return coalesce(cls.updated_at, cls.created_at).label("last_updated_at")

    @hybrid_property
    def last_updated_by(self):
        return self.updated_by_user if self.updated_by_user else self.created_by_user

    @last_updated_by.expression
    def last_updated_by(cls):
        # https://docs.sqlalchemy.org/en/14/core/tutorial.html
        return coalesce(
            select(User.username)
            .where(User.id == cls.updated_by_user_id)
            .scalar_subquery(),
            select(User.username)
            .where(User.id == cls.created_by_user_id)
            .scalar_subquery(),
        ).label("last_updated_by")


class CommonMixin(TimestampMixin, SoftDeleteMixin, IdMixin, UserStampMixin):
    pass


# =======================
# Users Table
# =======================
class User(Base, CommonMixin):
    __tablename__ = "users"

    name = Column(String(100), nullable=False)
    username = Column(String(32), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)

    @hybrid_property
    def total_help_requests_count(self):
        count = 0
        for help_request in self.help_requests:
            if help_request.deleted_at is None:
                count += 1
        return count

    @total_help_requests_count.expression
    def total_help_requests_count(cls):
        return select(func.count(HelpRequest.id)).where(
            HelpRequest.user_id == cls.id, HelpRequest.deleted_at == None
        )

    @hybrid_property
    def total_help_offers_count(self):
        count = 0
        for help_offer in self.help_offers:
            if help_offer.help_request.deleted_at is None:
                count += 1
        return count

    @total_help_offers_count.expression
    def total_help_offers_count(cls):
        return select(func.count(HelpOffer.id)).where(
            HelpRequest.user_id == cls.id, HelpRequest.help_request.deleted_at == None
        )


# =======================
# Help Requests Table
# =======================
class HelpRequest(Base, CommonMixin):
    __tablename__ = "help_requests"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        backref=backref(__tablename__, cascade="all, delete-orphan"),
    )
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    radius_meters = Column(Integer, default=5000)
    is_active = Column(Boolean, default=True)


# =======================
# Help Offers Table
# =======================
class HelpOffer(Base, CommonMixin):
    __tablename__ = "help_offers"

    help_request_id = Column(
        Integer, ForeignKey("help_requests.id", ondelete="CASCADE"), nullable=False
    )
    help_request = relationship(
        "HelpRequest", backref=backref(__tablename__, cascade="all, delete-orphan")
    )
    helper_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    helper = relationship(
        "User",
        foreign_keys=[helper_id],
        backref=backref(__tablename__, cascade="all, delete-orphan"),
    )
    message = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)

    @hybrid_property
    def help_request_uuid(self):
        return self.help_request.uuid

    @hybrid_property
    def help_request_title(self):
        return self.help_request.title


# =======================
# Ratings Table
# =======================
class Rating(Base, CommonMixin):
    __tablename__ = "ratings"

    help_request_id = Column(
        Integer, ForeignKey("help_requests.id", ondelete="CASCADE"), nullable=False
    )
    help_request = relationship(
        "HelpRequest", backref=backref(__tablename__, cascade="all, delete-orphan")
    )
    reviewer_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewer = relationship(
        "User",
        backref=backref("ratings_given", cascade="all, delete-orphan"),
        foreign_keys=[reviewer_id],
    )
    reviewee_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewee = relationship(
        "User",
        backref=backref("ratings_received", cascade="all, delete-orphan"),
        foreign_keys=[reviewee_id],
    )
    rating = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)

    # Prevent duplicate ratings for the same help request
    __table_args__ = (
        UniqueConstraint(
            "help_request_id", "reviewer_id", "reviewee_id", name="uq_rating"
        ),
    )
