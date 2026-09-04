"""horário das entrevistas (1ª e 2ª etapa)

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidatos", sa.Column("hora_1a_etapa", sa.String(10), nullable=True))
    op.add_column("candidatos", sa.Column("hora_2a_etapa", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("candidatos", "hora_2a_etapa")
    op.drop_column("candidatos", "hora_1a_etapa")
