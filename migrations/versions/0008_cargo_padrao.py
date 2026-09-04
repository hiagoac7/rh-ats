"""cargo padrao (agrupa as varias aberturas do mesmo cargo)

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vagas", sa.Column("cargo_padrao", sa.String(160), nullable=True))
    op.execute("UPDATE vagas SET cargo_padrao = cargo WHERE cargo_padrao IS NULL")


def downgrade() -> None:
    op.drop_column("vagas", "cargo_padrao")
