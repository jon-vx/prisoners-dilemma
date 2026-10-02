"""Add matches per pairing, defaulting existing tournaments to one.

Revision ID: b82e4d670a91
Revises: a15c03909edf
"""

from alembic import op
import sqlalchemy as sa


revision = "b82e4d670a91"
down_revision = "a15c03909edf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column("matches_per_pair", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.create_check_constraint(
        op.f("ck_tournaments_matches_per_pair_range"),
        "tournaments",
        "matches_per_pair BETWEEN 1 AND 10000",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_tournaments_matches_per_pair_range"), "tournaments", type_="check"
    )
    op.drop_column("tournaments", "matches_per_pair")
