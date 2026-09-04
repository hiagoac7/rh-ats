"""campos personalizados, extras e perfil do usuario

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campos_personalizados",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entidade", sa.String(20), nullable=False),
        sa.Column("chave", sa.String(60), nullable=False),
        sa.Column("rotulo", sa.String(120), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="texto"),
        sa.Column("opcoes", sa.JSON(), nullable=True),
        sa.Column("ordem", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_campos_entidade", "campos_personalizados", ["entidade"])
    op.add_column("candidatos", sa.Column("extras", sa.JSON(), nullable=True))
    op.add_column("vagas", sa.Column("extras", sa.JSON(), nullable=True))
    op.add_column("usuarios", sa.Column("foto", sa.Text(), nullable=True))
    op.add_column("usuarios", sa.Column("preferencias", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "preferencias")
    op.drop_column("usuarios", "foto")
    op.drop_column("vagas", "extras")
    op.drop_column("candidatos", "extras")
    op.drop_index("ix_campos_entidade", table_name="campos_personalizados")
    op.drop_table("campos_personalizados")
