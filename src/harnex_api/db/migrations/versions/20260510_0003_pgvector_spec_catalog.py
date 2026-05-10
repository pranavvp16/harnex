"""pgvector + shared spec catalog

Revision ID: 20260510_0003
Revises: 20260510_0002
Create Date: 2026-05-10
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "20260510_0003"
down_revision: str | None = "20260510_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Must match `HARNEX_OPENAI_EMBEDDING_DIM` default; we hard-code the column type so
# the migration is reproducible without env access. Changing the embedding dim
# requires a new migration.
EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    spec_source_type = postgresql.ENUM(
        "builtin",
        "openapi_url",
        "openapi_upload",
        "bare_url",
        name="spec_source_type",
        create_type=False,
    )
    spec_source_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "connector_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_type", spec_source_type, nullable=False),
        sa.Column("source_key", sa.String(2048), nullable=False),
        sa.Column("spec_hash", sa.String(128), nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("operation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_spec", postgresql.JSONB(), nullable=False),
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
        sa.UniqueConstraint(
            "source_type", "source_key", "spec_hash", name="uq_connector_specs_identity"
        ),
    )

    op.create_table(
        "operation_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "spec_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connector_specs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_id", sa.String(256), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(2048), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("semantic_tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("auth_scheme_keys", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("parameters", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("request_body", postgresql.JSONB(), nullable=True),
        sa.Column("responses", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        sa.Column("schema_hash", sa.String(128), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        # search_tsv is a generated column; SA can't express GENERATED ALWAYS AS
        # cleanly here, so we add the column with raw DDL just below.
    )
    op.create_index("ix_operation_chunks_spec", "operation_chunks", ["spec_id"])

    # tsvector generated from path+summary+description+tags. Path and summary
    # carry the most user-relevant tokens, so they get weight A; description B;
    # tags C. Tags are jsonb; Postgres forbids subqueries in generated columns
    # so we cast to text — `["pulls","issues"]` tokenizes to "pulls issues",
    # which is good enough for keyword recall on tag terms.
    op.execute(
        """
        ALTER TABLE operation_chunks
        ADD COLUMN search_tsv tsvector GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(summary, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(path, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(tags::text, '')), 'C')
        ) STORED
        """
    )

    op.execute(
        "CREATE INDEX ix_operation_chunks_tsv ON operation_chunks USING gin (search_tsv)"
    )
    op.execute(
        "CREATE INDEX ix_operation_chunks_embedding "
        "ON operation_chunks USING hnsw (embedding vector_cosine_ops)"
    )

    op.add_column(
        "connections",
        sa.Column(
            "spec_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("connector_specs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_connections_spec_id", "connections", ["spec_id"])


def downgrade() -> None:
    op.drop_index("ix_connections_spec_id", table_name="connections")
    op.drop_column("connections", "spec_id")
    op.execute("DROP INDEX IF EXISTS ix_operation_chunks_embedding")
    op.execute("DROP INDEX IF EXISTS ix_operation_chunks_tsv")
    op.drop_table("operation_chunks")
    op.drop_table("connector_specs")
    op.execute("DROP TYPE IF EXISTS spec_source_type")
