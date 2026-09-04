"""mapa cargo -> gestor (automacao)

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mapa_cargo_gestor",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("cargo", sa.String(160), nullable=False, unique=True),
        sa.Column("gestor", sa.String(120), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("mapa_cargo_gestor")
