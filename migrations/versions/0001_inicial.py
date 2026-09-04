"""estrutura inicial (gestores, vagas, candidatos, ciclos, usuarios)

Revision ID: 0001
Revises:
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gestores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False, unique=True),
        sa.Column("email", sa.String(160), nullable=True),
    )
    op.create_table(
        "vagas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=True, unique=True),
        sa.Column("cargo", sa.String(160), nullable=False),
        sa.Column("nivel", sa.String(40), nullable=True),
        sa.Column("qtde", sa.Integer, nullable=False, server_default="1"),
        sa.Column("tipo", sa.String(40), nullable=True),
        sa.Column("salario", sa.Float, nullable=True),
        sa.Column("area", sa.String(80), nullable=True),
        sa.Column("status", sa.String(40), nullable=True),
        sa.Column("data_abertura", sa.Date, nullable=True),
        sa.Column("previsao_inicio", sa.Date, nullable=True),
        sa.Column("data_fechamento", sa.Date, nullable=True),
        sa.Column("observacoes", sa.Text, nullable=True),
        sa.Column("gestor_id", sa.Integer, sa.ForeignKey("gestores.id"), nullable=True),
    )
    op.create_table(
        "candidatos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(160), nullable=False),
        sa.Column("cargo", sa.String(160), nullable=True),
        sa.Column("contato", sa.String(120), nullable=True),
        sa.Column("cpf", sa.String(20), nullable=True),
        sa.Column("email", sa.String(160), nullable=True),
        sa.Column("origem", sa.String(40), nullable=True),
        sa.Column("contato_inicial", sa.Date, nullable=True),
        sa.Column("data_1a_etapa", sa.DateTime, nullable=True),
        sa.Column("data_2a_etapa", sa.DateTime, nullable=True),
        sa.Column("data_aprovacao", sa.Date, nullable=True),
        sa.Column("parecer", sa.String(20), nullable=True),
        sa.Column("disc", sa.String(20), nullable=True),
        sa.Column("status", sa.String(40), nullable=True),
        sa.Column("etapa_atual", sa.String(60), nullable=True),
        sa.Column("gestor_nome", sa.String(120), nullable=True),
        sa.Column("devolutiva", sa.String(40), nullable=True),
        sa.Column("observacoes", sa.Text, nullable=True),
        sa.Column("vaga_id", sa.Integer, sa.ForeignKey("vagas.id"), nullable=True),
    )
    op.create_table(
        "ciclos_vaga",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vaga_id", sa.Integer, sa.ForeignKey("vagas.id"), nullable=False),
        sa.Column("linha", sa.String(60), nullable=True),
        sa.Column("data_abertura", sa.Date, nullable=True),
        sa.Column("data_fechamento", sa.Date, nullable=True),
        sa.Column("candidatos", sa.Integer, nullable=True),
        sa.Column("aprovados", sa.Integer, nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("observacoes", sa.Text, nullable=True),
    )
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("email", sa.String(160), nullable=False, unique=True),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("perfil", sa.String(20), nullable=False, server_default="RH"),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_table("ciclos_vaga")
    op.drop_table("candidatos")
    op.drop_table("vagas")
    op.drop_table("gestores")
