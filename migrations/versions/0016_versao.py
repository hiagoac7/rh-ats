"""controle de edicao simultanea (campo versao)

Revision ID: 0016
Revises: 0015
"""
from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidatos", sa.Column("versao", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("vagas", sa.Column("versao", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("vagas", "versao")
    op.drop_column("candidatos", "versao")
