"""checklist (consulta/chek), reagendamento e rank da vaga

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidatos", sa.Column("consulta", sa.String(20), nullable=True))
    op.add_column("candidatos", sa.Column("chek", sa.String(20), nullable=True))
    op.add_column("candidatos", sa.Column("reagendado", sa.String(40), nullable=True))
    op.add_column("candidatos", sa.Column("reagendamento", sa.String(40), nullable=True))
    op.add_column("vagas", sa.Column("rank", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("vagas", "rank")
    for c in ("reagendamento", "reagendado", "chek", "consulta"):
        op.drop_column("candidatos", c)
