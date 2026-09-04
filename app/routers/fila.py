"""Fila de parecer da gestão (equivale à aba FILA GESTÃO)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas

router = APIRouter(tags=["Fila Gestao"],
                   dependencies=[Depends(require_perm("fila.ver"))])

SLA_DIAS = 3
STATUS_FINAIS = {"APROVADO", "REPROVADO", "DECLINOU", "DESISTIU", "SEM RETORNO", "CANCELADO"}


@router.get("/fila-gestao", response_model=list[schemas.FilaItem])
def fila_gestao(sla_dias: int = Query(SLA_DIAS), db: Session = Depends(get_db)):
    stmt = select(models.Candidato).where(
        or_(
            models.Candidato.status.ilike("GEST%"),
            models.Candidato.etapa_atual.ilike("%entrevista gest%"),
        )
    )
    itens = []
    for c in db.scalars(stmt).all():
        if (c.status or "").upper() in STATUS_FINAIS:
            continue
        dias = c.dias_parado
        situacao = "ATRASADO" if (dias is not None and dias > sla_dias) else "NO PRAZO"
        itens.append(schemas.FilaItem(
            id=c.id, candidato=c.nome, cargo=c.cargo, gestor=c.gestor_nome,
            data_2a_etapa=c.data_2a_etapa, hora_2a_etapa=c.hora_2a_etapa, dias_parado=dias, situacao=situacao,
            contato=c.contato, email=c.email,
        ))
    itens.sort(key=lambda x: (x.dias_parado is None, -(x.dias_parado or 0)))
    return itens
