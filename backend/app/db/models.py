"""Normalized SQLAlchemy tables, independent of the public API models."""

import sqlalchemy as sa

metadata = sa.MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

tournaments = sa.Table(
    "tournaments",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("rounds", sa.Integer, nullable=False),
    sa.Column("seed", sa.BigInteger, nullable=False),
    sa.Column("include_self_play", sa.Boolean, nullable=False),
    sa.Column("temptation", sa.Integer, nullable=False),
    sa.Column("reward", sa.Integer, nullable=False),
    sa.Column("punishment", sa.Integer, nullable=False),
    sa.Column("sucker", sa.Integer, nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    ),
    sa.CheckConstraint("rounds BETWEEN 1 AND 10000", name="rounds_range"),
    sa.CheckConstraint(
        "temptation > reward AND reward > punishment AND punishment > sucker",
        name="payoff_order",
    ),
    sa.CheckConstraint(
        "2 * CAST(reward AS BIGINT) > CAST(temptation AS BIGINT) + sucker",
        name="mutual_cooperation",
    ),
)
sa.Index("ix_tournaments_created_at", tournaments.c.created_at.desc())

tournament_strategies = sa.Table(
    "tournament_strategies",
    metadata,
    sa.Column(
        "tournament_id",
        sa.Uuid,
        sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column("strategy_key", sa.String(64), primary_key=True),
    sa.Column("position", sa.Integer, nullable=False),
    sa.UniqueConstraint(
        "tournament_id", "position", name="uq_tournament_strategies_position"
    ),
    sa.CheckConstraint("position >= 0", name="position_nonnegative"),
)

matches = sa.Table(
    "matches",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column(
        "tournament_id",
        sa.Uuid,
        sa.ForeignKey("tournaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sa.Column("position", sa.Integer, nullable=False),
    sa.Column("strategy_a", sa.String(64), nullable=False, index=True),
    sa.Column("strategy_b", sa.String(64), nullable=False, index=True),
    sa.Column("seed", sa.BigInteger, nullable=False),
    sa.Column("score_a", sa.BigInteger, nullable=False),
    sa.Column("score_b", sa.BigInteger, nullable=False),
    sa.Column("cooperations_a", sa.Integer, nullable=False),
    sa.Column("cooperations_b", sa.Integer, nullable=False),
    sa.Column("winner", sa.String(3), nullable=False),
    sa.UniqueConstraint("tournament_id", "position", name="uq_matches_position"),
    sa.CheckConstraint("position >= 0", name="position_nonnegative"),
    sa.CheckConstraint("winner IN ('a', 'b', 'tie')", name="winner_value"),
    sa.CheckConstraint(
        "cooperations_a >= 0 AND cooperations_b >= 0", name="cooperations_nonnegative"
    ),
)

round_results = sa.Table(
    "round_results",
    metadata,
    sa.Column(
        "match_id",
        sa.Uuid,
        sa.ForeignKey("matches.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column("round_number", sa.Integer, primary_key=True),
    sa.Column("move_a", sa.String(9), nullable=False),
    sa.Column("move_b", sa.String(9), nullable=False),
    sa.Column("payoff_a", sa.Integer, nullable=False),
    sa.Column("payoff_b", sa.Integer, nullable=False),
    sa.Column("cumulative_score_a", sa.BigInteger, nullable=False),
    sa.Column("cumulative_score_b", sa.BigInteger, nullable=False),
    sa.CheckConstraint("round_number > 0", name="round_positive"),
    sa.CheckConstraint(
        "move_a IN ('cooperate', 'defect') AND move_b IN ('cooperate', 'defect')",
        name="move_values",
    ),
)
