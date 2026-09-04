"""redefinicao de senha por e-mail

Revision ID: 0018
Revises: 0017
"""
from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("senha_alterada_em", sa.DateTime(), nullable=True))

    op.create_table(
        "tokens_senha",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=True),
        sa.Column("expira_em", sa.DateTime(), nullable=False),
        sa.Column("usado_em", sa.DateTime(), nullable=True),
        sa.Column("pedido_por", sa.String(160), nullable=True),
    )
    op.create_index("ix_tokens_senha_hash", "tokens_senha", ["token_hash"], unique=True)
    op.create_index("ix_tokens_senha_usuario", "tokens_senha", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_tokens_senha_usuario", table_name="tokens_senha")
    op.drop_index("ix_tokens_senha_hash", table_name="tokens_senha")
    op.drop_table("tokens_senha")
    op.drop_column("usuarios", "senha_alterada_em")
