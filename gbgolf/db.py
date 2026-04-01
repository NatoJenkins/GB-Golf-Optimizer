"""
Database models for GB Golf Optimizer.

Tables defined using SQLAlchemy Core (no ORM). Queries use db.session.execute(text(...)).
"""
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

fetches = db.Table(
    "fetches",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("tournament_name", sa.String, nullable=False),
    sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("player_count", sa.Integer, nullable=False),
    sa.Column("source", sa.String, nullable=False),
    sa.Column("tour", sa.String, nullable=False),
    sa.Column("datagolf_updated_at", sa.DateTime(timezone=True), nullable=True),
)

projections = db.Table(
    "projections",
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column(
        "fetch_id",
        sa.Integer,
        sa.ForeignKey("fetches.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("player_name", sa.String, nullable=False),
    sa.Column("projected_score", sa.Float, nullable=False),
)
