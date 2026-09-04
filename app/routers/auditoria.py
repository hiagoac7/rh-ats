from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("", response_model=list[schemas.AuditoriaOut])
def listar(acao: str | None = None, entidade: str | None = None,
           limite: int = Query(200, le=1000), db: Session = Depends(get_db),
           _: models.Usuario = Depends(require_perm("auditoria.ver"))):
    stmt = select(models.Auditoria).order_by(models.Auditoria.id.desc())
    if acao:
        stmt = stmt.where(models.Auditoria.acao == acao)
    if entidade:
        stmt = stmt.where(models.Auditoria.entidade == entidade)
    return db.scalars(stmt.limit(limite)).all()
