"""canais de divulgacao e candidaturas recebidas

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "canais",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(80), nullable=False, unique=True),
        sa.Column("link", sa.String(400), nullable=True),
        sa.Column("responsavel", sa.String(120), nullable=True),
        sa.Column("login", sa.String(160), nullable=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("observacoes", sa.Text, nullable=True),
    )
    op.create_table(
        "candidaturas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("canal_id", sa.Integer, sa.ForeignKey("canais.id"), nullable=False),
        sa.Column("vaga_id", sa.Integer, sa.ForeignKey("vagas.id"), nullable=True),
        sa.Column("quantidade", sa.Integer, nullable=False, server_default="0"),
        sa.Column("data", sa.Date, nullable=True),
        sa.Column("observacoes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("candidaturas")
    op.drop_table("canais")
