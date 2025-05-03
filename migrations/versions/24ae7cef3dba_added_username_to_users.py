"""added_username_to_users

Revision ID: 24ae7cef3dba
Revises: f10cfe4d265c
Create Date: 2025-04-27 22:50:14.614719

"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "24ae7cef3dba"
down_revision: Union[str, None] = "f10cfe4d265c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("username", sa.String(length=32), nullable=False))
    op.create_unique_constraint(op.f("uq_users_username"), "users", ["username"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f("uq_users_username"), "users", type_="unique")
    op.drop_column("users", "username")
