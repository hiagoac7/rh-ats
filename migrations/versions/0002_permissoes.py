"""colunas de permissão por usuário (extra_perms, denied_perms)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("extra_perms", sa.JSON(), nullable=True, server_default="[]"))
    op.add_column("usuarios", sa.Column("denied_perms", sa.JSON(), nullable=True, server_default="[]"))


def downgrade() -> None:
    op.drop_column("usuarios", "denied_perms")
    op.drop_column("usuarios", "extra_perms")
