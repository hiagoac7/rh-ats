"""listas configuraveis (substitui a aba LISTAS)

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("valor", sa.String(120), nullable=False),
        sa.Column("ordem", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_listas_tipo", "listas", ["tipo"])


def downgrade() -> None:
    op.drop_index("ix_listas_tipo", table_name="listas")
    op.drop_table("listas")
