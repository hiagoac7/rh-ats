"""anotações de candidato e banco de talentos

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidatos", sa.Column("banco_talentos", sa.Boolean(), nullable=True, server_default=sa.false()))
    op.create_table(
        "anotacoes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("candidato_id", sa.Integer, sa.ForeignKey("candidatos.id"), nullable=False),
        sa.Column("autor", sa.String(160), nullable=True),
        sa.Column("texto", sa.Text, nullable=False),
        sa.Column("criado_em", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("anotacoes")
    op.drop_column("candidatos", "banco_talentos")
