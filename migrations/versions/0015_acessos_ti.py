"""acessos de TI para novos contratados

Revision ID: 0015
Revises: 0014
"""
from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "acessos_ti",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("candidato_id", sa.Integer, sa.ForeignKey("candidatos.id"), nullable=False, unique=True),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDENTE"),
        sa.Column("itens", sa.JSON(), nullable=True),
        sa.Column("observacoes", sa.Text, nullable=True),
        sa.Column("responsavel", sa.String(120), nullable=True),
        sa.Column("concluido_em", sa.DateTime, nullable=True),
    )
    op.add_column("config_email", sa.Column("avisar_ti", sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column("config_email", sa.Column("email_ti", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("config_email", "email_ti")
    op.drop_column("config_email", "avisar_ti")
    op.drop_table("acessos_ti")

