"""Initial schema – all tables for AI Byggesøknad

Revision ID: 001
Revises:
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ── projects ──────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("address_text", sa.Text, nullable=False),
        sa.Column("lat", sa.Float, nullable=True),
        sa.Column("lng", sa.Float, nullable=True),
        sa.Column("intent_text", sa.Text, nullable=False),
        sa.Column("measure_type", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("risk_level", sa.String(32), nullable=True),
        sa.Column("application_required", sa.Boolean, nullable=True),
        sa.Column("kommunenr", sa.String(10), nullable=True),
        sa.Column("kommunenavn", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])

    # ── analysis_results ──────────────────────────────────────────────────────
    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("classification", postgresql.JSONB, nullable=True),
        sa.Column("plan_layer", postgresql.JSONB, nullable=True),
        sa.Column("hazard", postgresql.JSONB, nullable=True),
        sa.Column("property_data", postgresql.JSONB, nullable=True),
        sa.Column("rule_results", postgresql.JSONB, nullable=True),
        sa.Column("ai_summary", sa.Text, nullable=True),
        sa.Column("next_steps", postgresql.JSONB, nullable=True),
        sa.Column("document_requirements", postgresql.JSONB, nullable=True),
        sa.Column("warnings", postgresql.JSONB, nullable=True),
        sa.Column("municipality_info", postgresql.JSONB, nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_analysis_results_project_id", "analysis_results", ["project_id"])

    # ── rules ─────────────────────────────────────────────────────────────────
    op.create_table(
        "rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_code", sa.String(32), nullable=False, unique=True),
        sa.Column("rule_name", sa.String(256), nullable=False),
        sa.Column("rule_group", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("legal_basis", sa.String(512), nullable=True),
        sa.Column("conditions", postgresql.JSONB, nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_rules_rule_code", "rules", ["rule_code"])
    op.create_index("ix_rules_rule_group", "rules", ["rule_group"])

    # ── documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("generated_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_documents_project_id", "documents", ["project_id"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("rules")
    op.drop_table("analysis_results")
    op.drop_table("projects")
