"""Rename anthropic_api_key to gemini_api_key

Revision ID: a1b2c3d4e5f6
Revises: ed57f237454a
Create Date: 2026-02-14 08:36:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "ed57f237454a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename anthropic_api_key to gemini_api_key in settings table."""
    with op.batch_alter_table("settings") as batch_op:
        batch_op.alter_column("anthropic_api_key", new_column_name="gemini_api_key")


def downgrade() -> None:
    """Revert gemini_api_key back to anthropic_api_key."""
    with op.batch_alter_table("settings") as batch_op:
        batch_op.alter_column("gemini_api_key", new_column_name="anthropic_api_key")
