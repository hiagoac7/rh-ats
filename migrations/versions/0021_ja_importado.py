"""memoria da importacao

Antes, tudo que o RH apagava no sistema voltava no import seguinte, porque a
linha continuava na planilha. Esta tabela guarda o que ja foi importado alguma
vez, para distinguir "novidade" de "removido de proposito".

Revision ID: 0021
Revises: 0020
"""
from alembic import op
import sqlalchemy as sa

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ja_importado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("chave", sa.String(240), nullable=False),
        sa.Column("primeira_vez", sa.DateTime(), nullable=True),
        sa.Column("removido_em", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_ja_importado_tipo", "ja_importado", ["tipo"])
    op.create_index("ix_ja_importado_chave", "ja_importado", ["chave"])


def downgrade() -> None:
    op.drop_index("ix_ja_importado_chave", table_name="ja_importado")
    op.drop_index("ix_ja_importado_tipo", table_name="ja_importado")
    op.drop_table("ja_importado")
