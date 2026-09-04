"""avaliacao estruturada da entrevista

Substitui a decisao baseada so no campo "parecer" (texto livre) por notas
em criterios configuraveis mais uma recomendacao. As notas ficam em JSON
porque os criterios mudam por cargo e por empresa.

Revision ID: 0020
Revises: 0019
"""
from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "avaliacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidato_id", sa.Integer(), sa.ForeignKey("candidatos.id"), nullable=False),
        sa.Column("etapa", sa.String(30), nullable=False),
        sa.Column("autor", sa.String(160), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=True),
        sa.Column("notas", sa.JSON(), nullable=True),
        sa.Column("recomendacao", sa.String(20), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
    )
    op.create_index("ix_avaliacoes_candidato", "avaliacoes", ["candidato_id"])


def downgrade() -> None:
    op.drop_index("ix_avaliacoes_candidato", table_name="avaliacoes")
    op.drop_table("avaliacoes")
