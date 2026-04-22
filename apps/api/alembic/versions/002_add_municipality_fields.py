"""Add municipality fields and indexes – Fase 3

Revision ID: 002
Revises: 001
Create Date: 2026-04-22 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add kommunenr index for fast municipality lookups
    op.create_index("ix_projects_kommunenr", "projects", ["kommunenr"])

    # Add fylke column to projects
    op.add_column("projects",
        sa.Column("fylke", sa.String(128), nullable=True)
    )

    # Add rate_limit_hits table for persistent rate limiting (optional, for distributed deployments)
    op.create_table(
        "rate_limit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ip_address", sa.String(64), nullable=False),
        sa.Column("endpoint", sa.String(256), nullable=True),
        sa.Column("hit_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_rate_limit_log_ip_hit", "rate_limit_log", ["ip_address", "hit_at"])


def downgrade() -> None:
    op.drop_table("rate_limit_log")
    op.drop_column("projects", "fylke")
    op.drop_index("ix_projects_kommunenr", "projects")
