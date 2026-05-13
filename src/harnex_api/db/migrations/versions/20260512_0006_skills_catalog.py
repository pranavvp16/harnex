"""skills catalog + skill execution mode

Revision ID: 20260512_0006
Revises: 20260511_0005
Create Date: 2026-05-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "20260512_0006"
down_revision: str | None = "20260511_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Mirrors EMBEDDING_DIM in 20260510_0003 — must stay in lockstep.
EMBEDDING_DIM = 1536


def upgrade() -> None:
    # Postgres can't ALTER TYPE … ADD VALUE inside a transaction block in older
    # versions; alembic runs migrations inside one. Wrapping in autocommit-block
    # would require op.execute_block. In recent PG (12+) ADD VALUE works within
    # a transaction as long as the new value is not used in the same txn — which
    # is exactly the case here (we only insert rows with mode="skill" later).
    op.execute("ALTER TYPE execution_mode ADD VALUE IF NOT EXISTS 'skill'")

    op.add_column(
        "executions",
        sa.Column("artifact_url", sa.String(2048), nullable=True),
    )
    op.add_column(
        "executions",
        sa.Column("artifact_bytes", sa.BigInteger(), nullable=True),
    )

    skill_runtime = postgresql.ENUM(
        "node",
        "python",
        name="skill_runtime",
        create_type=False,
    )
    skill_runtime.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("runtime", skill_runtime, nullable=False),
        sa.Column("output_format", sa.String(32), nullable=False),
        sa.Column("overview", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("scripts", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("embedding_model", sa.String(128), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column(
            "indexed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("key", name="uq_skills_key"),
    )
    op.create_index("ix_skills_key", "skills", ["key"])

    # tsvector over name + overview + output_format. Skills are coarse-grained;
    # the overview holds the strong document-intent tokens, so it gets weight A
    # alongside the name. output_format gets B so "pdf", "xlsx" tokens still hit.
    op.execute(
        """
        ALTER TABLE skills
        ADD COLUMN search_tsv tsvector GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(overview, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(output_format, '')), 'B')
        ) STORED
        """
    )

    op.execute("CREATE INDEX ix_skills_tsv ON skills USING gin (search_tsv)")
    op.execute(
        "CREATE INDEX ix_skills_embedding "
        "ON skills USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 32, ef_construction = 128)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_skills_embedding")
    op.execute("DROP INDEX IF EXISTS ix_skills_tsv")
    op.drop_index("ix_skills_key", table_name="skills")
    op.drop_table("skills")
    op.execute("DROP TYPE IF EXISTS skill_runtime")
    op.drop_column("executions", "artifact_bytes")
    op.drop_column("executions", "artifact_url")
    # Postgres has no DROP VALUE for enums without recreating the type; leaving
    # the "skill" enum value in place is safe because the column drops above
    # remove the only rows that referenced it.
