"""Create tournament and match storage

Revision ID: a15c03909edf
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "a15c03909edf"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rounds", sa.Integer(), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("include_self_play", sa.Boolean(), nullable=False),
        sa.Column("temptation", sa.Integer(), nullable=False),
        sa.Column("reward", sa.Integer(), nullable=False),
        sa.Column("punishment", sa.Integer(), nullable=False),
        sa.Column("sucker", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "2 * CAST(reward AS BIGINT) > CAST(temptation AS BIGINT) + sucker",
            name=op.f("ck_tournaments_mutual_cooperation"),
        ),
        sa.CheckConstraint(
            "rounds BETWEEN 1 AND 10000", name=op.f("ck_tournaments_rounds_range")
        ),
        sa.CheckConstraint(
            "temptation > reward AND reward > punishment AND punishment > sucker",
            name=op.f("ck_tournaments_payoff_order"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tournaments")),
    )
    op.create_index(
        "ix_tournaments_created_at",
        "tournaments",
        [sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tournament_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("strategy_a", sa.String(length=64), nullable=False),
        sa.Column("strategy_b", sa.String(length=64), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("score_a", sa.BigInteger(), nullable=False),
        sa.Column("score_b", sa.BigInteger(), nullable=False),
        sa.Column("cooperations_a", sa.Integer(), nullable=False),
        sa.Column("cooperations_b", sa.Integer(), nullable=False),
        sa.Column("winner", sa.String(length=3), nullable=False),
        sa.CheckConstraint(
            "winner IN ('a', 'b', 'tie')", name=op.f("ck_matches_winner_value")
        ),
        sa.CheckConstraint(
            "cooperations_a >= 0 AND cooperations_b >= 0",
            name=op.f("ck_matches_cooperations_nonnegative"),
        ),
        sa.CheckConstraint(
            "position >= 0", name=op.f("ck_matches_position_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
            name=op.f("fk_matches_tournament_id_tournaments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_matches")),
        sa.UniqueConstraint("tournament_id", "position", name="uq_matches_position"),
    )
    op.create_index(
        op.f("ix_matches_strategy_a"), "matches", ["strategy_a"], unique=False
    )
    op.create_index(
        op.f("ix_matches_strategy_b"), "matches", ["strategy_b"], unique=False
    )
    op.create_index(
        op.f("ix_matches_tournament_id"), "matches", ["tournament_id"], unique=False
    )
    op.create_table(
        "tournament_strategies",
        sa.Column("tournament_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_key", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "position >= 0", name=op.f("ck_tournament_strategies_position_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
            name=op.f("fk_tournament_strategies_tournament_id_tournaments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "tournament_id", "strategy_key", name=op.f("pk_tournament_strategies")
        ),
        sa.UniqueConstraint(
            "tournament_id", "position", name="uq_tournament_strategies_position"
        ),
    )
    op.create_table(
        "round_results",
        sa.Column("match_id", sa.Uuid(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("move_a", sa.String(length=9), nullable=False),
        sa.Column("move_b", sa.String(length=9), nullable=False),
        sa.Column("payoff_a", sa.Integer(), nullable=False),
        sa.Column("payoff_b", sa.Integer(), nullable=False),
        sa.Column("cumulative_score_a", sa.BigInteger(), nullable=False),
        sa.Column("cumulative_score_b", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "move_a IN ('cooperate', 'defect') AND move_b IN ('cooperate', 'defect')",
            name=op.f("ck_round_results_move_values"),
        ),
        sa.CheckConstraint(
            "round_number > 0", name=op.f("ck_round_results_round_positive")
        ),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
            name=op.f("fk_round_results_match_id_matches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "match_id", "round_number", name=op.f("pk_round_results")
        ),
    )


def downgrade() -> None:
    op.drop_table("round_results")
    op.drop_table("tournament_strategies")
    op.drop_index(op.f("ix_matches_tournament_id"), table_name="matches")
    op.drop_index(op.f("ix_matches_strategy_b"), table_name="matches")
    op.drop_index(op.f("ix_matches_strategy_a"), table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_tournaments_created_at", table_name="tournaments")
    op.drop_table("tournaments")
