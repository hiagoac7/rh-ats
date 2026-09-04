"""remove a recuperacao de senha por e-mail

A funcao foi retirada do sistema: o envio de e-mail nao e confiavel neste
ambiente e a pessoa ficava esperando um link que nunca chegava. Quem perde o
acesso fala com o TI, que troca a senha na tela de Gestao.

A coluna usuarios.senha_alterada_em NAO e removida: ela continua sendo usada
para desconectar as sessoes abertas quando a senha muda, em qualquer caminho.

Revision ID: 0019
Revises: 0018
"""
from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for indice in ("ix_tokens_senha_usuario", "ix_tokens_senha_hash"):
        try:
            op.drop_index(indice, table_name="tokens_senha")
        except Exception:
            pass
    op.drop_table("tokens_senha")


def downgrade() -> None:
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
