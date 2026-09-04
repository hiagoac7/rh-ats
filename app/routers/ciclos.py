from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_perm
from .. import models, schemas

router = APIRouter(prefix="/ciclos", tags=["Ciclos"])


@router.get("", response_model=list[schemas.CicloOut])
def listar_ciclos(vaga_id: int | None = None, db: Session = Depends(get_db),
                  _: models.Usuario = Depends(require_perm("vagas.ver"))):
    stmt = select(models.CicloVaga)
    if vaga_id:
        stmt = stmt.where(models.CicloVaga.vaga_id == vaga_id)
    return db.scalars(stmt).all()
