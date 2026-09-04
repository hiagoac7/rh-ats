"""
Automações que a planilha fazia com fórmulas.

Regras extraídas da planilha (aba CANDIDATOS, colunas V a AA — "calcula sozinho"):
  ETAPA ATUAL   = derivada do STATUS
  GESTOR        = derivado do CARGO (mapa cargo -> gestor)
  DATA APROVAÇÃO= data da 2ª etapa, quando o status é APROVADO
"""
from sqlalchemy.orm import Session
from . import models

STATUS_PARA_ETAPA = {
    "APROVADO":    "6. Aprovado",
    "REPROVADO":   "0. Encerrado",
    "DECLINOU":    "0. Encerrado",
    "DESISTIU":    "0. Encerrado",
    "SEM RETORNO": "0. Encerrado",
    "CANCELADO":   "0. Encerrado",
    "GESTÃO":      "4. Entrevista Gestão",
    "RH":          "3. Entrevista RH",
    "TRIADO":      "2. Triado",
    "CONGELADA":   "5. Congelado",
}
ETAPA_PADRAO = "1. Recebido"


def etapa_do_status(status: str | None) -> str:
    """Mesma regra da planilha: a etapa segue o status."""
    return STATUS_PARA_ETAPA.get((status or "").strip().upper(), ETAPA_PADRAO)


def gestor_do_cargo(db: Session, cargo: str | None) -> str | None:
    """Busca o gestor responsável pelo cargo (mapa configurável em Configurações)."""
    if not cargo:
        return None
    alvo = cargo.strip().lower()
    mapa = db.query(models.MapaCargoGestor).all()
    for m in mapa:
        if (m.cargo or "").strip().lower() == alvo:
            return m.gestor
    return None


def aplicar(db: Session, cand: models.Candidato, campos_enviados: set[str] | None = None) -> list[str]:
    """
    Aplica as automações ao candidato. Devolve a lista do que foi preenchido.

    Respeita o que o usuário digitou: só preenche o que veio vazio,
    exceto a ETAPA, que segue o status (igual à fórmula da planilha).
    """
    campos_enviados = campos_enviados or set()
    aplicados = []

    if "etapa_atual" not in campos_enviados:
        nova = etapa_do_status(cand.status)
        if cand.etapa_atual != nova:
            cand.etapa_atual = nova
            aplicados.append("etapa_atual")

    if not (cand.gestor_nome or "").strip():
        g = gestor_do_cargo(db, cand.cargo)
        if g:
            cand.gestor_nome = g
            aplicados.append("gestor_nome")

    if (cand.status or "").strip().upper() == "APROVADO" and not cand.data_aprovacao:
        if cand.data_2a_etapa:
            cand.data_aprovacao = cand.data_2a_etapa.date()
            aplicados.append("data_aprovacao")

    if (cand.status or "").strip().upper() == "APROVADO" and cand.id:
        ja = db.query(models.AcessoTI).filter_by(candidato_id=cand.id).first()
        if not ja:
            itens = {}
            for l in db.query(models.Lista).filter_by(tipo="acesso_ti", ativo=True).order_by(models.Lista.ordem).all():
                itens[l.valor] = False
            db.add(models.AcessoTI(candidato_id=cand.id, status="PENDENTE", itens=itens))
            aplicados.append("acessos_ti")

    return aplicados
