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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

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
class TimestampMixin:
    """Adds created_at and updated_at with server default."""

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Adds deleted_at for soft delete (not managed by DB)."""

    deleted_at = Column(DateTime, nullable=True)


# =======================
# Users Table
# =======================
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)


# =======================
# Help Requests Table
# =======================
class HelpRequest(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "help_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = relationship("User", backref(__tablename__, cascade="CASCADE"))
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    radius_meters = Column(Integer, default=5000)
    is_active = Column(Boolean, default=True)


# =======================
# Help Offers Table
# =======================
class HelpOffer(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "help_offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("help_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    request = relationship("HelpRequest", backref(__tablename__, cascade="CASCADE"))
    helper_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    helper = relationship("User", backref(__tablename__, cascade="CASCADE"))
    message = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)


# =======================
# Ratings Table
# =======================
class Rating(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    help_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("help_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    help_request = relationship(
        "HelpRequest", backref=backref(__tablename__, cascade="CASCADE")
    )
    reviewer_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewer = relationship(
        "User",
        backref=backref("ratings_given", cascade="CASCADE"),
        foreign_keys=[reviewer_id],
    )
    reviewee_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reviewee = relationship(
        "User",
        backref=backref("ratings_received", cascade="CASCADE"),
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
