"""config de email, modelos de mensagem, envios e requisicoes de vaga

Revision ID: 0014
Revises: 0013
"""
from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "config_email",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("servidor", sa.String(160), nullable=True),
        sa.Column("porta", sa.Integer, nullable=False, server_default="587"),
        sa.Column("usuario", sa.String(160), nullable=True),
        sa.Column("senha", sa.String(255), nullable=True),
        sa.Column("remetente", sa.String(160), nullable=True),
        sa.Column("nome_remetente", sa.String(120), nullable=True),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("avisar_gestor", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("lembrete_entrevista", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("horas_antes", sa.Integer, nullable=False, server_default="24"),
    )
    op.create_table(
        "modelos_mensagem",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("canal", sa.String(20), nullable=False, server_default="email"),
        sa.Column("gatilho", sa.String(40), nullable=True),
        sa.Column("assunto", sa.String(200), nullable=True),
        sa.Column("corpo", sa.Text, nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "envios_email",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("para", sa.String(200), nullable=False),
        sa.Column("assunto", sa.String(200), nullable=True),
        sa.Column("tipo", sa.String(40), nullable=True),
        sa.Column("candidato_id", sa.Integer, nullable=True),
        sa.Column("sucesso", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("erro", sa.Text, nullable=True),
    )
    op.create_table(
        "requisicoes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("solicitante", sa.String(120), nullable=True),
        sa.Column("cargo", sa.String(160), nullable=False),
        sa.Column("nivel", sa.String(40), nullable=True),
        sa.Column("qtde", sa.Integer, nullable=False, server_default="1"),
        sa.Column("tipo", sa.String(40), nullable=True),
        sa.Column("motivo", sa.String(30), nullable=True),
        sa.Column("substituindo", sa.String(160), nullable=True),
        sa.Column("area", sa.String(80), nullable=True),
        sa.Column("linha", sa.String(60), nullable=True),
        sa.Column("salario", sa.Float, nullable=True),
        sa.Column("previsao_inicio", sa.Date, nullable=True),
        sa.Column("justificativa", sa.Text, nullable=True),
        sa.Column("gestor_id", sa.Integer, sa.ForeignKey("gestores.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDENTE"),
        sa.Column("decidido_por", sa.String(120), nullable=True),
        sa.Column("decidido_em", sa.DateTime, nullable=True),
        sa.Column("observacao_decisao", sa.Text, nullable=True),
        sa.Column("vaga_id", sa.Integer, sa.ForeignKey("vagas.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("requisicoes")
    op.drop_table("envios_email")
    op.drop_table("modelos_mensagem")
    op.drop_table("config_email")
