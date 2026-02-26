"""Add company address and contact_info columns

Revision ID: c2d3e4f5a6b7
Revises: b7c8d9e0f1a2
Create Date: 2026-02-26 12:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: str | Sequence[str] | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("company") as batch_op:
        batch_op.add_column(
            sa.Column(
                "address",
                sa.String(length=500),
                nullable=False,
                server_default="",
            )
        )
        batch_op.add_column(
            sa.Column(
                "contact_info",
                sa.String(length=500),
                nullable=False,
                server_default="",
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("company") as batch_op:
        batch_op.drop_column("contact_info")
        batch_op.drop_column("address")
