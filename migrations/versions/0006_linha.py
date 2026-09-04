"""campo linha (Amarela / Movimentacao) em vagas e candidatos

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vagas", sa.Column("linha", sa.String(60), nullable=True))
    op.add_column("candidatos", sa.Column("linha", sa.String(60), nullable=True))


def downgrade() -> None:
    op.drop_column("candidatos", "linha")
    op.drop_column("vagas", "linha")
