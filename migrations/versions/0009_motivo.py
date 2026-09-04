"""motivo da vaga (ampliacao / substituicao)

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vagas", sa.Column("motivo", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("vagas", "motivo")
