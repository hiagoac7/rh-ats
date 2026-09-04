"""avisos de mudanca (tempo real)

Revision ID: 0017
Revises: 0016
"""
from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mudancas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("entidade", sa.String(40), nullable=False),
        sa.Column("acao", sa.String(20), nullable=False),
        sa.Column("registro_id", sa.Integer, nullable=True),
        sa.Column("por", sa.String(120), nullable=True),
    )
    op.create_index("ix_mudancas_criado_em", "mudancas", ["criado_em"])
    op.create_index("ix_mudancas_entidade", "mudancas", ["entidade"])


def downgrade() -> None:
    op.drop_index("ix_mudancas_entidade", table_name="mudancas")
    op.drop_index("ix_mudancas_criado_em", table_name="mudancas")
    op.drop_table("mudancas")
