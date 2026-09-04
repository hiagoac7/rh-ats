"""
Modelo de dados do sistema de R&S (ATS).

Traduz as abas da planilha em tabelas relacionais:
  - VAGAS        -> Vaga
  - CANDIDATOS   -> Candidato  (FK para Vaga)
  - CICLOS *     -> CicloVaga  (periodos das vagas perenes Vendedor/SDR)
  - LISTAS (I/K) -> Gestor     (cargo -> gestor -> e-mail)

As abas PAINEL e FILA GESTAO NAO viram tabelas: sao calculadas em queries
(ver routers/painel.py e routers/fila.py).
"""
from datetime import datetime, date
from sqlalchemy import (
    String, Integer, Float, Date, DateTime, ForeignKey, Text, Boolean, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Gestor(Base):
    __tablename__ = "gestores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), unique=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)

    vagas: Mapped[list["Vaga"]] = relationship(back_populates="gestor")


class Vaga(Base):
    __tablename__ = "vagas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str | None] = mapped_column(String(20), unique=True)
    cargo: Mapped[str] = mapped_column(String(160))
    cargo_padrao: Mapped[str | None] = mapped_column(String(160), nullable=True)
    nivel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    qtde: Mapped[int] = mapped_column(Integer, default=1)
    tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    salario: Mapped[float | None] = mapped_column(Float, nullable=True)
    area: Mapped[str | None] = mapped_column(String(80), nullable=True)
    linha: Mapped[str | None] = mapped_column(String(60), nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    data_abertura: Mapped[date | None] = mapped_column(Date, nullable=True)
    previsao_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_fechamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extras: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    gestor_id: Mapped[int | None] = mapped_column(ForeignKey("gestores.id"), nullable=True)
    gestor: Mapped["Gestor | None"] = relationship(back_populates="vagas")

    candidatos: Mapped[list["Candidato"]] = relationship(back_populates="vaga")
    ciclos: Mapped[list["CicloVaga"]] = relationship(back_populates="vaga")


class Candidato(Base):
    __tablename__ = "candidatos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160))
    cargo: Mapped[str | None] = mapped_column(String(160), nullable=True)
    contato: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    origem: Mapped[str | None] = mapped_column(String(40), nullable=True)

    contato_inicial: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_1a_etapa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hora_1a_etapa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    data_2a_etapa: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hora_2a_etapa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    data_aprovacao: Mapped[date | None] = mapped_column(Date, nullable=True)

    parecer: Mapped[str | None] = mapped_column(String(20), nullable=True)
    disc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consulta: Mapped[str | None] = mapped_column(String(20), nullable=True)
    chek: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reagendado: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reagendamento: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    etapa_atual: Mapped[str | None] = mapped_column(String(60), nullable=True)
    gestor_nome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    devolutiva: Mapped[str | None] = mapped_column(String(40), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    linha: Mapped[str | None] = mapped_column(String(60), nullable=True)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    banco_talentos: Mapped[bool] = mapped_column(Boolean, default=False)
    extras: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    vaga_id: Mapped[int | None] = mapped_column(ForeignKey("vagas.id"), nullable=True)
    vaga: Mapped["Vaga | None"] = relationship(back_populates="candidatos")

    @property
    def dias_parado(self) -> int | None:
        """
        Dias parados desde a ultima movimentacao.

        Conta apenas a DATA (ignora o horario), igual a formula da planilha
        (TODAY() - MAX(datas)). Sem isso, uma entrevista as 20h aparecia com
        um dia a menos e o semaforo de atraso ficava errado.
        """
        ref = self.data_2a_etapa or self.data_1a_etapa
        if ref is None:
            return None
        base = ref.date() if hasattr(ref, "date") else ref
        return (date.today() - base).days


class CicloVaga(Base):
    """Periodos de abertura/fechamento de vagas perenes (Vendedor, SDR)."""
    __tablename__ = "ciclos_vaga"

    id: Mapped[int] = mapped_column(primary_key=True)
    vaga_id: Mapped[int] = mapped_column(ForeignKey("vagas.id"))
    linha: Mapped[str | None] = mapped_column(String(60), nullable=True)
    data_abertura: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_fechamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    candidatos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aprovados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    vaga: Mapped["Vaga"] = relationship(back_populates="ciclos")


import enum


class Perfil(str, enum.Enum):
    """Perfis de acesso do sistema."""
    RH = "RH"
    TI = "TI"
    GESTOR = "GESTOR"
    DIRETORIA = "DIRETORIA"

PERFIS_ADMIN = (Perfil.RH, Perfil.TI)


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[str] = mapped_column(String(20), default=Perfil.RH.value)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    foto: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferencias: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    extra_perms: Mapped[list] = mapped_column(JSON, default=list)
    denied_perms: Mapped[list] = mapped_column(JSON, default=list)
    senha_alterada_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def permissoes(self) -> list[str]:
        from .permissions import perms_efetivas
        return sorted(perms_efetivas(self.perfil, self.extra_perms, self.denied_perms))


class Auditoria(Base):
    """Registro de auditoria: quem fez o quê e quando."""
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ator_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ator_nome: Mapped[str | None] = mapped_column(String(160), nullable=True)
    acao: Mapped[str] = mapped_column(String(60))
    entidade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entidade_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    detalhes: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Anotacao(Base):
    """Anotação/comentário de um recrutador sobre um candidato."""
    __tablename__ = "anotacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidato_id: Mapped[int] = mapped_column(ForeignKey("candidatos.id"))
    autor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    texto: Mapped[str] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Canal(Base):
    """
    Canal de divulgação de vagas (Indeed, LinkedIn, Sine, indicação...).

    ATENÇÃO: por segurança, este sistema NÃO guarda senhas de plataformas.
    Use um gerenciador de senhas para as credenciais.
    """
    __tablename__ = "canais"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    link: Mapped[str | None] = mapped_column(String(400), nullable=True)
    responsavel: Mapped[str | None] = mapped_column(String(120), nullable=True)
    login: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidaturas: Mapped[list["Candidatura"]] = relationship(back_populates="canal")


class Candidatura(Base):
    """Quantas candidaturas um canal trouxe para uma vaga (aba DIVULGAÇÃO: 'cvs recebidos')."""
    __tablename__ = "candidaturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    canal_id: Mapped[int] = mapped_column(ForeignKey("canais.id"))
    vaga_id: Mapped[int | None] = mapped_column(ForeignKey("vagas.id"), nullable=True)
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    canal: Mapped["Canal"] = relationship(back_populates="candidaturas")


class Lista(Base):
    """
    Listas configuraveis do sistema (substitui a aba LISTAS da planilha).

    tipo: cargo | origem | area | nivel | tipo_contrato | motivo | status_vaga
          | status_candidato | etapa | linha | reagendado
    """
    __tablename__ = "listas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(40), index=True)
    valor: Mapped[str] = mapped_column(String(120))
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class MapaCargoGestor(Base):
    """Cargo -> gestor responsável (aba LISTAS, colunas I/J da planilha)."""
    __tablename__ = "mapa_cargo_gestor"

    id: Mapped[int] = mapped_column(primary_key=True)
    cargo: Mapped[str] = mapped_column(String(160), unique=True)
    gestor: Mapped[str] = mapped_column(String(120))


class CampoPersonalizado(Base):
    """
    Campos criados pelo próprio usuário, sem precisar mexer no código.

    entidade: candidato | vaga
    tipo    : texto | numero | data | lista | sim_nao
    """
    __tablename__ = "campos_personalizados"

    id: Mapped[int] = mapped_column(primary_key=True)
    entidade: Mapped[str] = mapped_column(String(20), index=True)
    chave: Mapped[str] = mapped_column(String(60))
    rotulo: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(20), default="texto")
    opcoes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class ConfigEmail(Base):
    """Configuracao do servidor de e-mail (uma linha so)."""
    __tablename__ = "config_email"

    id: Mapped[int] = mapped_column(primary_key=True)
    servidor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    porta: Mapped[int] = mapped_column(Integer, default=587)
    usuario: Mapped[str | None] = mapped_column(String(160), nullable=True)
    senha: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remetente: Mapped[str | None] = mapped_column(String(160), nullable=True)
    nome_remetente: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=False)
    avisar_gestor: Mapped[bool] = mapped_column(Boolean, default=True)
    avisar_ti: Mapped[bool] = mapped_column(Boolean, default=True)
    email_ti: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lembrete_entrevista: Mapped[bool] = mapped_column(Boolean, default=True)
    horas_antes: Mapped[int] = mapped_column(Integer, default=24)


class ModeloMensagem(Base):
    """Modelos de e-mail/WhatsApp com variaveis {{candidato}}, {{vaga}}, {{data}}..."""
    __tablename__ = "modelos_mensagem"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    canal: Mapped[str] = mapped_column(String(20), default="email")
    gatilho: Mapped[str | None] = mapped_column(String(40), nullable=True)
    assunto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    corpo: Mapped[str] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class EnvioEmail(Base):
    """Registro dos e-mails enviados (para nao repetir e para auditoria)."""
    __tablename__ = "envios_email"

    id: Mapped[int] = mapped_column(primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    para: Mapped[str] = mapped_column(String(200))
    assunto: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    candidato_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sucesso: Mapped[bool] = mapped_column(Boolean, default=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)


class Requisicao(Base):
    """Pedido de abertura de vaga, feito pelo gestor e aprovado pela diretoria."""
    __tablename__ = "requisicoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    solicitante: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cargo: Mapped[str] = mapped_column(String(160))
    nivel: Mapped[str | None] = mapped_column(String(40), nullable=True)
    qtde: Mapped[int] = mapped_column(Integer, default=1)
    tipo: Mapped[str | None] = mapped_column(String(40), nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    substituindo: Mapped[str | None] = mapped_column(String(160), nullable=True)
    area: Mapped[str | None] = mapped_column(String(80), nullable=True)
    linha: Mapped[str | None] = mapped_column(String(60), nullable=True)
    salario: Mapped[float | None] = mapped_column(Float, nullable=True)
    previsao_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    gestor_id: Mapped[int | None] = mapped_column(ForeignKey("gestores.id"), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="PENDENTE")
    decidido_por: Mapped[str | None] = mapped_column(String(120), nullable=True)
    decidido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    observacao_decisao: Mapped[str | None] = mapped_column(Text, nullable=True)
    vaga_id: Mapped[int | None] = mapped_column(ForeignKey("vagas.id"), nullable=True)


class AcessoTI(Base):
    """
    Provisionamento de acessos pelo TI quando um candidato e aprovado.

    Criado automaticamente assim que o status do candidato vira APROVADO,
    para o TI saber quem entra, quando e o que precisa ser liberado.
    """
    __tablename__ = "acessos_ti"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidato_id: Mapped[int] = mapped_column(ForeignKey("candidatos.id"), unique=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    status: Mapped[str] = mapped_column(String(20), default="PENDENTE")
    itens: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsavel: Mapped[str | None] = mapped_column(String(120), nullable=True)
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Mudanca(Base):
    """
    Marca que algo mudou, para as telas abertas se atualizarem na hora.

    Uma linha por alteracao, bem pequena. E gravada automaticamente
    (veja app/eventos.py) — nenhuma rota precisa lembrar de avisar.
    """
    __tablename__ = "mudancas"

    id: Mapped[int] = mapped_column(primary_key=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    entidade: Mapped[str] = mapped_column(String(40), index=True)
    acao: Mapped[str] = mapped_column(String(20))
    registro_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    por: Mapped[str | None] = mapped_column(String(120), nullable=True)


class Avaliacao(Base):
    """
    Avaliacao estruturada de uma entrevista.

    Antes so existia o campo "parecer" (texto livre, que na pratica significa
    "liberado para a gestao"). Com isto, cada entrevistador registra notas por
    criterio e uma recomendacao — o que permite comparar dois candidatos sem
    depender de memoria, e mostra depois quem costuma aprovar mais.

    As notas ficam em JSON porque os criterios sao configuraveis (aba
    Configuracoes -> Listas, tipo "criterio_avaliacao"): cada empresa e cada
    cargo pesam coisas diferentes, e uma coluna por criterio engessaria isso.
    """
    __tablename__ = "avaliacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidato_id: Mapped[int] = mapped_column(ForeignKey("candidatos.id"), index=True)
    etapa: Mapped[str] = mapped_column(String(30))
    autor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    notas: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recomendacao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def media(self) -> float | None:
        vals = [v for v in (self.notas or {}).values() if isinstance(v, (int, float))]
        return round(sum(vals) / len(vals), 1) if vals else None


class JaImportado(Base):
    """
    Memoria da importacao: o que a planilha ja trouxe alguma vez.

    Sem isto, a importacao era de mao unica com a planilha sempre ganhando:
    tudo que o RH apagava no sistema voltava no import seguinte, porque a
    linha continuava la na planilha. Com este registro da para distinguir
    duas situacoes que pareciam iguais:

      * a chave nunca foi importada  -> e novidade, cria
      * a chave ja foi importada e nao esta mais no banco -> alguem removeu
        de proposito, entao NAO recria

    Guardamos so a chave (codigo da vaga, nome do candidato), nunca os dados.
    """
    __tablename__ = "ja_importado"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)
    chave: Mapped[str] = mapped_column(String(240), index=True)
    primeira_vez: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    removido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
