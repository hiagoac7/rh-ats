"""tabela de auditoria

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("ator_id", sa.Integer, nullable=True),
        sa.Column("ator_nome", sa.String(160), nullable=True),
        sa.Column("acao", sa.String(60), nullable=False),
        sa.Column("entidade", sa.String(40), nullable=True),
        sa.Column("entidade_id", sa.String(40), nullable=True),
        sa.Column("detalhes", sa.JSON(), nullable=True),
    )
    op.create_index("ix_auditoria_id", "auditoria", ["id"])


def downgrade() -> None:
    op.drop_index("ix_auditoria_id", table_name="auditoria")
    op.drop_table("auditoria")
