"""
Tempo real: avisa as telas abertas assim que algo muda.

Como funciona, em duas partes:

1) DETECCAO — um "ouvinte" do SQLAlchemy percebe qualquer inclusao, alteracao
   ou exclusao dos registros que interessam e grava uma linha na tabela
   `mudancas`. Nenhuma rota precisa lembrar de avisar: e automatico.

2) ENTREGA — o endpoint /eventos mantem uma conexao aberta com cada tela e
   empurra um aviso sempre que aparecem linhas novas. Funciona com varios
   processos no servidor, porque o combinado passa pelo banco.
"""
from datetime import datetime, timedelta

from sqlalchemy import event, select, func
from sqlalchemy.orm import Session

from . import models

VIGIADOS = {
    models.Candidato: "candidato",
    models.Vaga: "vaga",
    models.AcessoTI: "acesso",
    models.Requisicao: "requisicao",
    models.Anotacao: "anotacao",
    models.Gestor: "gestor",
    models.Canal: "canal",
    models.Lista: "lista",
    models.CampoPersonalizado: "campo",
    models.Usuario: "usuario",
}

_ATOR: dict[int, str] = {}


def marcar_ator(sessao: Session, nome: str | None):
    if nome:
        _ATOR[id(sessao)] = nome


def _registrar(sessao: Session):
    """Chamado antes de cada gravacao: anota o que mudou."""
    por = _ATOR.get(id(sessao))
    novas = []
    for grupo, acao in ((sessao.new, "criado"),
                        (sessao.dirty, "alterado"),
                        (sessao.deleted, "excluido")):
        for obj in grupo:
            nome = VIGIADOS.get(type(obj))
            if not nome:
                continue
            if acao == "alterado" and not sessao.is_modified(obj, include_collections=False):
                continue
            novas.append(models.Mudanca(entidade=nome, acao=acao,
                                        registro_id=getattr(obj, "id", None), por=por))
    for m in novas:
        sessao.add(m)


@event.listens_for(Session, "before_flush")
def _antes_de_gravar(sessao, contexto, instancias):
    if any(isinstance(o, models.Mudanca) for o in sessao.new):
        return
    _registrar(sessao)


def ultimo_id(db: Session) -> int:
    return db.scalar(select(func.coalesce(func.max(models.Mudanca.id), 0))) or 0


def desde(db: Session, ultimo: int, limite: int = 50) -> list[dict]:
    """O que mudou depois de um certo ponto."""
    itens = db.scalars(
        select(models.Mudanca).where(models.Mudanca.id > ultimo)
        .order_by(models.Mudanca.id).limit(limite)).all()
    return [{"id": m.id, "entidade": m.entidade, "acao": m.acao,
             "registro_id": m.registro_id, "por": m.por} for m in itens]


def limpar_antigas(db: Session, dias: int = 2):
    """A tabela so serve para avisar as telas — o historico fica na Auditoria."""
    corte = datetime.now() - timedelta(days=dias)
    db.query(models.Mudanca).filter(models.Mudanca.criado_em < corte).delete()
    db.commit()
