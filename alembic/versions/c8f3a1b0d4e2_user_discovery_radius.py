"""user discovery zone and max distance

Revision ID: c8f3a1b0d4e2
Revises: b7e4d2a91c03
Create Date: 2026-10-30 00:50:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c8f3a1b0d4e2"
down_revision = "b7e4d2a91c03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("search_zone", sa.String(length=160), nullable=True))
    op.add_column(
        "users",
        sa.Column("max_distance_km", sa.Integer(), nullable=False, server_default="15"),
    )


def downgrade() -> None:
    op.drop_column("users", "max_distance_km")
    op.drop_column("users", "search_zone")
